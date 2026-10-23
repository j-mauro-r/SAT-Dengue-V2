import { z } from "zod";

const month = z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/);
const probability = z.number().min(0).max(1);
const nullableMeasure = z.number().nonnegative().nullable();

export const availabilityStatusSchema = z.enum([
  "AVAILABLE",
  "INELIGIBLE",
  "INSUFFICIENT_HISTORY",
  "MISSING_DATA",
  "NOT_CALCULATED",
]);

const resultSchema = z
  .object({
    result_id: z.string().uuid().nullable(),
    horizon: z.enum(["T1", "T2"]),
    target_period: month,
    probability: probability.nullable(),
    threshold: probability.nullable(),
    alert_status: z.enum(["ALERT", "NO_ALERT", "UNAVAILABLE"]),
    availability_status: availabilityStatusSchema,
    availability_reason: z.string().min(1).max(300).nullable(),
    model_family: z.string().min(1).max(32).nullable(),
    model_role: z.enum(["PROVISIONAL_CANDIDATE", "CHAMPION"]).nullable(),
    model_version: z.string().min(1).max(128).nullable(),
    procedure_id: z.string().min(1).max(128).nullable(),
  })
  .strict()
  .superRefine((result, context) => {
    const available = result.availability_status === "AVAILABLE";
    const required = [
      result.result_id,
      result.probability,
      result.threshold,
      result.model_family,
      result.model_role,
      result.model_version,
      result.procedure_id,
    ];
    if (available && (required.some((value) => value === null) || result.availability_reason)) {
      context.addIssue({ code: "custom", message: "AVAILABLE result has incomplete traceability" });
    }
    if (
      available &&
      result.probability !== null &&
      result.threshold !== null &&
      result.alert_status !== (result.probability >= result.threshold ? "ALERT" : "NO_ALERT")
    ) {
      context.addIssue({
        code: "custom",
        message: "Alert status contradicts the contracted values",
      });
    }
    if (
      !available &&
      (result.result_id !== null ||
        result.probability !== null ||
        result.threshold !== null ||
        result.alert_status !== "UNAVAILABLE" ||
        result.availability_reason === null)
    ) {
      context.addIssue({ code: "custom", message: "Unavailable result has an invalid shape" });
    }
  });

const endemicPointSchema = z
  .object({
    period: month,
    cases: z.number().int().nonnegative().nullable(),
    p25: nullableMeasure,
    median: nullableMeasure,
    p75: nullableMeasure,
  })
  .strict();

const municipalitySchema = z
  .object({
    municipality_code: z.string().regex(/^\d{5}$/),
    municipality_name: z.string().min(1).max(150),
    cases_t: z.number().int().nonnegative().nullable(),
    endemic_zone_t: z.enum(["EXITO", "SEGURIDAD", "ALERTA", "EXCESO", "UNAVAILABLE"]),
    p25: nullableMeasure,
    median: nullableMeasure,
    p75: nullableMeasure,
    results: z.array(resultSchema).length(2),
    endemic_channel_series: z.array(endemicPointSchema),
  })
  .strict()
  .superRefine((municipality, context) => {
    if (new Set(municipality.results.map(({ horizon }) => horizon)).size !== 2) {
      context.addIssue({ code: "custom", message: "Municipality must contain T1 and T2" });
    }
  });

const evaluationRecordSchema = z
  .object({
    horizon: z.enum(["T1", "T2"]),
    procedure_id: z.string().min(1).max(128),
    evaluation_period_start: month,
    evaluation_period_end: month,
    evaluation_geography: z.string().min(1).max(300),
    auroc: probability.nullable(),
    average_precision: probability.nullable(),
    brier: probability.nullable(),
    false_alerts: z.number().int().nonnegative().nullable(),
    alerts_emitted: z.number().int().nonnegative().nullable(),
    false_alert_ratio: probability.nullable(),
    onsets_detected: z.number().int().nonnegative().nullable(),
    actual_onsets: z.number().int().nonnegative().nullable(),
    onset_sensitivity: probability.nullable(),
  })
  .strict();

export const dashboardResponseSchema = z
  .object({
    metadata: z
      .object({
        result_set_id: z.string().uuid(),
        reference_period: month,
        generated_at: z.string().datetime({ offset: true }),
        data_updated_at: z.string().datetime({ offset: true }).nullable(),
        data_version: z.string().min(1).max(128),
      })
      .strict(),
    governance: z
      .object({
        governance_gate: z.string().min(1).max(16),
        governance_status: z.enum(["APPROVED", "NOT_APPROVED"]),
        champion_status: z.enum(["SELECTED", "NOT_SELECTED"]),
        limitation: z.string().min(1).max(500),
      })
      .strict(),
    department: z
      .object({
        department_code: z.enum(["50", "73"]),
        department_name: z.string().min(1).max(100),
        requested_period: month,
      })
      .strict(),
    municipalities: z.array(municipalitySchema),
    evaluation_context: z
      .object({
        demonstrative_values: z.boolean(),
        evaluation_records: z.array(evaluationRecordSchema),
      })
      .strict(),
  })
  .strict()
  .superRefine((response, context) => {
    const expectedCount = response.department.department_code === "73" ? 47 : 29;
    if (response.municipalities.length !== expectedCount) {
      context.addIssue({
        code: "custom",
        message: `Department requires ${expectedCount} municipalities`,
      });
    }
    if (response.metadata.reference_period !== response.department.requested_period) {
      context.addIssue({ code: "custom", message: "Reference and requested periods must match" });
    }
    if (
      response.municipalities.some(
        ({ municipality_code }) =>
          !municipality_code.startsWith(response.department.department_code),
      )
    ) {
      context.addIssue({ code: "custom", message: "Municipality does not belong to department" });
    }
  });

export const apiErrorResponseSchema = z
  .object({
    error_code: z.enum([
      "INVALID_DEPARTMENT_CODE",
      "INVALID_PERIOD_FORMAT",
      "DASHBOARD_DATA_NOT_FOUND",
      "INTERNAL_ERROR",
    ]),
    message: z.string().min(1),
  })
  .strict();

export type DashboardResponse = z.infer<typeof dashboardResponseSchema>;
export type AvailabilityStatus = z.infer<typeof availabilityStatusSchema>;
