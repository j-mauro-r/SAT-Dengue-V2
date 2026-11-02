"""Bounded national notification diagnostics; no canonical publication or model fitting."""

from __future__ import annotations

import hashlib
import json
import platform
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.consolidation import normalize_code_series, parse_epi_date_series
from sat_dengue.datasets.legacy_consolidation import resolve_repo_root
from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, SOURCE_IDENTITIES

SOURCES = (
    "data/raw/dengue.csv",
    "data/raw/dengue_grave.csv",
    "data/sources/Listados_DIVIPOLA.xlsx",
    "data/sources/Divipola-municipios.md",
    "data/sources/Divipola-departamentos.md",
    "data/sources/divipola-provenance.json",
)
ESSENTIAL = ("COD_DPTO_R", "COD_MUN_R", "INI_SIN", "COD_EVE")
STREAMS = {"dengue.csv": "210", "dengue_grave.csv": "220"}
COUNTS = {"210": "dengue_notifications_count", "220": "dengue_grave_notifications_count"}
LIMITATIONS = [
    "D1: occurrence/notification date differences are accepted; INI_SIN is never replaced.",
    "D2/D3: within the configured review calendar, absence of rows means zero notifications.",
    "File hashes establish snapshot integrity, not completeness of official extraction.",
    "Current DIVIPOLA membership does not establish historical territorial applicability.",
    "No validated historical crosswalk is supplied; no territorial reassignment is applied.",
    "Counts describe notifications, not unique patients, episodes or confirmed cases.",
    "Retrospective extracts cannot establish operational point-in-time availability.",
    "Climate, H5, labels and training admission are not evaluated in this analysis.",
]


@dataclass(frozen=True)
class AnalysisConfig:
    """Explicit review window, independent of future notification density.

    The defaults follow EXP-BETA01's training start and stop before its reserved
    2025 block. This diagnostic window is not a source-completeness assertion.
    """

    start_month: str = "2011-06"
    end_month: str = "2024-12"
    chunksize: int = 100_000
    output_dir: str = "data/interim/canonical-nacional-data"

    def __post_init__(self) -> None:
        for value in (self.start_month, self.end_month):
            if str(pd.Period(value, freq="M")) != value:
                raise ValueError("Review bounds must use YYYY-MM")
        if self.start_month > self.end_month or self.chunksize < 1:
            raise ValueError("Invalid review bounds or chunk size")
        if self.end_month >= "2025-01":
            raise ValueError("The reserved 2025 block is outside this diagnostic task")
        if Path(self.output_dir).is_absolute() or ".." in Path(self.output_dir).parts:
            raise ValueError("Output must be repository relative")
        if not self.output_dir.startswith("data/interim/canonical-nacional-data"):
            raise ValueError("Keep diagnostic outputs inside the dedicated interim directory")


def fingerprint(path: Path) -> dict[str, Any]:
    """Return a file identity without exposing its contents.

    Args:
        path: Existing source file.

    Returns:
        Byte size and SHA-256 digest.
    """
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"sha256": digest, "bytes": path.stat().st_size}


def inventory_sources(root: Path) -> pd.DataFrame:
    """Inventory required sources against existing Stage 2 and DANE identities.

    Args:
        root: Repository root.

    Returns:
        Availability and integrity evidence; completeness remains unverified.
    """
    expected = {
        key: value.copy() for key, value in {**SOURCE_IDENTITIES, **NATIVE_IDENTITIES}.items()
    }
    provenance = root / SOURCES[-1]
    if provenance.is_file():
        payload = json.loads(provenance.read_text(encoding="utf-8"))
        # A provenance file is a supplied assertion, not independent upstream proof.
        for name, item in payload.get("files", {}).items():
            expected.setdefault(f"data/sources/{name}", {"sha256": item["sha256"]})
    rows = []
    for relative in (*SOURCES, *NATIVE_IDENTITIES):
        path = root / relative
        available = path.is_file()
        observed = fingerprint(path) if available else {}
        reference = expected.get(relative, {})
        status = "missing"
        if available:
            status = "unreferenced"
            if reference:
                status = (
                    "match" if all(observed[k] == v for k, v in reference.items()) else "mismatch"
                )
        rows.append(
            {
                "source": relative,
                "available": available,
                **observed,
                "expected_sha256": reference.get("sha256", ""),
                "integrity": status,
                "official_extraction_completeness": "UNVERIFIED",
            }
        )
    return pd.DataFrame(rows).fillna("")


def load_national_catalog(root: Path) -> pd.DataFrame:
    """Read the supplied DANE JSON snapshot (despite its .md extension).

    Args:
        root: Repository root.

    Returns:
        Full territorial universe, including catalogued non-municipal areas.

    Raises:
        ValueError: On incomplete, conflicting or malformed catalogue keys.
    """
    payload = json.loads((root / SOURCES[3]).read_text(encoding="utf-8"))
    frame = pd.DataFrame(payload["resultado"])
    codes = normalize_code_series(frame["CODIGO_DPTO_MPIO"], 5)
    departments = normalize_code_series(frame["CODIGO_DEPARTAMENTO"], 2)
    municipalities = normalize_code_series(frame["CODIGO_MUNICIPIO"], 3)
    if codes.eq("").any() or codes.ne(departments + municipalities).any():
        raise ValueError("DIVIPOLA contains incomplete or inconsistent territorial keys")
    result = pd.DataFrame(
        {
            "municipality_code": codes,
            "department_code": departments,
            "municipality_name": frame["NOMBRE_MUNICIPIO"],
            "territory_type": frame["CODIGO_TIPO_MUNICIPIO"],
        }
    ).drop_duplicates()
    if result.empty or result["municipality_code"].duplicated().any():
        raise ValueError("DIVIPOLA contains empty or ambiguous territorial identity")
    return result.sort_values("municipality_code").reset_index(drop=True)


def classify_notifications(
    raw: pd.DataFrame, catalog: pd.DataFrame, expected_event: str, config: AnalysisConfig
) -> pd.DataFrame:
    """Classify rows without changing raw fields or removing duplicate notifications.

    Args:
        raw: One source chunk, read as strings.
        catalog: Full national reference.
        expected_event: Event required by this source stream.
        config: Fixed review parameters.

    Returns:
        Separate helpers and independent exclusion flags, aligned to input rows.
    """
    fields = {name: raw[name].fillna("").astype(str).str.strip() for name in ESSENTIAL}
    dept = normalize_code_series(fields["COD_DPTO_R"], 2)
    mun = normalize_code_series(fields["COD_MUN_R"], 3)
    code = (dept + mun).where(dept.ne("") & mun.ne(""), "")
    valid = code.isin(catalog["municipality_code"])
    category = pd.Series("requires_review", index=raw.index)
    # Potentially historical is a triage category, never a proven equivalence.
    category.loc[dept.isin(catalog["department_code"]) & ~valid] = (
        "historical_or_potentially_homologable"
    )
    category.loc[code.eq("")] = "incomplete_or_unknown"
    category.loc[valid] = "valid"
    onset = parse_epi_date_series(raw["INI_SIN"])
    month = onset.dt.strftime("%Y-%m").fillna("")
    event = normalize_code_series(fields["COD_EVE"], 3)
    frame = pd.DataFrame(
        {
            "municipality_code": code,
            "territory_status": category,
            "year_month": month,
            "event": event,
            "invalid_territory": ~valid,
            "invalid_onset": onset.isna(),
            "invalid_event": ~event.isin(COUNTS),
            "stream_event_mismatch": event.ne(expected_event),
            "outside_review_window": ~month.between(config.start_month, config.end_month),
        }
    )
    frame["accepted"] = ~frame[
        [
            "invalid_territory",
            "invalid_onset",
            "invalid_event",
            "stream_event_mismatch",
            "outside_review_window",
        ]
    ].any(axis=1)
    return frame


def build_review_calendar(
    catalog: pd.DataFrame,
    monthly: pd.DataFrame,
    config: AnalysisConfig,
    located_rows: pd.DataFrame,
) -> pd.DataFrame:
    """Complete the fixed territorial calendar with epidemiological zeros only.

    Args:
        catalog: Territorial universe chosen before reviewing case density.
        monthly: Accepted monthly event counts.
        config: Explicit interval; no future-density admission filters.
        located_rows: All geographically and temporally assignable source rows,
            including rows whose event requires review.

    Returns:
        Unique municipality-month rows with separate absence indicators per stream.
    """
    months = pd.period_range(config.start_month, config.end_month, freq="M").astype(str)
    grid = catalog.merge(pd.DataFrame({"year_month": months}), how="cross")
    result = grid.merge(
        monthly, on=["municipality_code", "year_month"], how="left", validate="one_to_one"
    )
    result = result.merge(
        located_rows, on=["municipality_code", "year_month"], how="left", validate="one_to_one"
    )
    result["requires_record_review"] = False
    for column in COUNTS.values():
        result[column] = result[column].fillna(0).astype("int64")
        raw_column = f"{column}_source_rows"
        result[raw_column] = result[raw_column].fillna(0).astype("int64")
        result[f"{column}_has_rows"] = result[raw_column].gt(0)
        result[f"{column}_zero_from_absence"] = result[raw_column].eq(0)
        result["requires_record_review"] |= result[raw_column].gt(result[column])
    result["eligible_for_canonical_review"] = ~result["requires_record_review"]
    result["historical_territory_applicability"] = "UNVERIFIED"
    result["training_eligibility"] = "NOT_ASSESSED"
    if result.duplicated(["municipality_code", "year_month"]).any():
        raise ValueError("Repeated municipality-month")
    for column in COUNTS.values():
        if result[column].lt(0).any() or result[column].sum() != monthly[column].sum():
            raise ValueError("Notification counts were not conserved")
    return result.sort_values(["municipality_code", "year_month"]).reset_index(drop=True)


def _increment(counter: Counter[Any], frame: pd.DataFrame, columns: list[str]) -> None:
    """Accumulate grouped counts across chunks."""
    for key, count in frame.groupby(columns, dropna=False).size().items():
        counter[key if isinstance(key, tuple) else (key,)] += int(count)


def _counter_frame(counter: Counter[Any], columns: list[str]) -> pd.DataFrame:
    """Convert a sorted counter to a reproducible aggregate table."""
    return pd.DataFrame(
        [(*key, value) for key, value in sorted(counter.items())],
        columns=[*columns, "notifications"],
    )


def _duplicate_chunk(connection: sqlite3.Connection, raw: pd.DataFrame, source: str) -> None:
    """Accumulate full-row fingerprints and candidate export identifiers on disk.

    Candidate CONSECUTIVE values are never treated as patient/episode identity.
    Only SHA-256 fingerprints enter the temporary store; no identifiers are exported.
    """
    columns = sorted(raw.columns)
    hashes = Counter(
        hashlib.sha256(
            json.dumps([columns, list(row)], ensure_ascii=False, separators=(",", ":")).encode()
        ).hexdigest()
        for row in raw[columns].itertuples(index=False, name=None)
    )
    connection.executemany(
        "INSERT INTO exact VALUES (?, ?, ?) ON CONFLICT(source, digest) "
        "DO UPDATE SET n=n+excluded.n",
        [(source, key, n) for key, n in hashes.items()],
    )
    if "CONSECUTIVE" in raw:
        identifiers = raw["CONSECUTIVE"].str.strip()
        hashed = Counter(
            hashlib.sha256(value.encode()).hexdigest() for value in identifiers if value
        )
        connection.executemany(
            "INSERT INTO candidate VALUES (?, ?, ?) ON CONFLICT(source, digest) "
            "DO UPDATE SET n=n+excluded.n",
            [(source, key, n) for key, n in hashed.items()],
        )
    connection.commit()


def _duplicate_summary(connection: sqlite3.Connection, sources: list[str]) -> pd.DataFrame:
    """Report duplicate groups, involved rows and excess rows without deleting any."""
    rows = []
    for source in sources:
        for table in ("exact", "candidate"):
            groups, involved, excess = connection.execute(
                f"SELECT count(*), coalesce(sum(n),0), coalesce(sum(n-1),0) FROM {table} "
                "WHERE source=? AND n>1",
                (source,),
            ).fetchone()
            rows.append(
                {
                    "source": source,
                    "category": table,
                    "groups": groups,
                    "rows_in_groups": involved,
                    "excess_rows": excess,
                }
            )
    cross = connection.execute(
        "SELECT count(*), coalesce(sum(n),0) FROM (SELECT sum(n) AS n FROM candidate "
        "GROUP BY digest HAVING count(DISTINCT source)>1)"
    ).fetchone()
    rows.append(
        {
            "source": "both_streams",
            "category": "candidate_identifier_overlap",
            "groups": cross[0],
            "rows_in_groups": cross[1],
            "excess_rows": None,
        }
    )
    return pd.DataFrame(rows)


def _scan_sources(
    root: Path, catalog: pd.DataFrame, config: AnalysisConfig, connection: sqlite3.Connection
) -> dict[str, pd.DataFrame]:
    """Stream private sources into bounded aggregate diagnostics."""
    connection.execute(
        "CREATE TABLE exact(source TEXT, digest TEXT, n INT, PRIMARY KEY(source,digest))"
    )
    connection.execute(
        "CREATE TABLE candidate(source TEXT, digest TEXT, n INT, PRIMARY KEY(source,digest))"
    )
    counters: dict[str, Counter[Any]] = {
        name: Counter()
        for name in (
            "territorial",
            "temporal",
            "events",
            "reconciliation",
            "monthly",
            "located",
            "missingness",
        )
    }
    source_rows = []
    for source, expected_event in STREAMS.items():
        count = 0
        minima: list[str] = []
        maxima: list[str] = []
        columns = pd.read_csv(root / "data/raw" / source, nrows=0).columns
        if not set(ESSENTIAL).issubset(columns):
            raise ValueError(
                f"Missing essential columns in {source}: {sorted(set(ESSENTIAL) - set(columns))}"
            )
        for raw in pd.read_csv(
            root / "data/raw" / source, dtype=str, keep_default_na=False, chunksize=config.chunksize
        ):
            count += len(raw)
            frame = classify_notifications(raw, catalog, expected_event, config)
            frame["source"] = source
            frame["raw_department"] = raw["COD_DPTO_R"].str.strip()
            frame["raw_municipality"] = raw["COD_MUN_R"].str.strip()
            frame["onset_year"] = frame["year_month"].str[:4].replace("", "UNASSIGNABLE")
            frame["onset_month"] = frame["year_month"].replace("", "UNASSIGNABLE")
            dates = frame.loc[frame["year_month"].ne(""), "year_month"]
            if not dates.empty:
                minima.append(str(dates.min()))
                maxima.append(str(dates.max()))
            _increment(
                counters["territorial"],
                frame,
                [
                    "source",
                    "territory_status",
                    "raw_department",
                    "raw_municipality",
                    "municipality_code",
                ],
            )
            _increment(counters["temporal"], frame, ["source", "onset_year", "onset_month"])
            _increment(counters["events"], frame, ["source", "event", "stream_event_mismatch"])
            frame["source_event"] = expected_event
            located = ~frame[["invalid_territory", "invalid_onset", "outside_review_window"]].any(
                axis=1
            )
            _increment(
                counters["located"],
                frame.loc[located],
                ["municipality_code", "year_month", "source_event"],
            )
            flags = [
                "invalid_territory",
                "invalid_onset",
                "invalid_event",
                "stream_event_mismatch",
                "outside_review_window",
                "accepted",
            ]
            _increment(counters["reconciliation"], frame, ["source", *flags])
            _increment(
                counters["monthly"],
                frame.loc[frame["accepted"]],
                ["municipality_code", "year_month", "event"],
            )
            for field in (*ESSENTIAL, "CONSECUTIVE", "FEC_NOT", "ANO"):
                if field not in raw:
                    counters["missingness"][(source, field, "column_absent")] += len(raw)
                else:
                    counters["missingness"][(source, field, "blank")] += int(
                        raw[field].str.strip().eq("").sum()
                    )
            _duplicate_chunk(connection, raw, source)
        source_rows.append(
            {
                "source": source,
                "rows": count,
                "first_onset_month": min(minima, default=""),
                "last_onset_month": max(maxima, default=""),
                "candidate_identifier_available": "CONSECUTIVE" in columns,
            }
        )
    return {
        "source_records": pd.DataFrame(source_rows),
        "territorial_discrepancies": _counter_frame(
            counters["territorial"],
            [
                "source",
                "territory_status",
                "raw_department",
                "raw_municipality",
                "municipality_code",
            ],
        ),
        "temporal_coverage": _counter_frame(
            counters["temporal"], ["source", "onset_year", "year_month"]
        ),
        "event_consistency": _counter_frame(
            counters["events"], ["source", "event", "stream_event_mismatch"]
        ),
        "record_reconciliation": _counter_frame(
            counters["reconciliation"],
            [
                "source",
                "invalid_territory",
                "invalid_onset",
                "invalid_event",
                "stream_event_mismatch",
                "outside_review_window",
                "accepted",
            ],
        ),
        "essential_missingness": _counter_frame(
            counters["missingness"], ["source", "field", "status"]
        ),
        "accepted_monthly": _counter_frame(
            counters["monthly"], ["municipality_code", "year_month", "event"]
        ),
        "duplicates": _duplicate_summary(connection, list(STREAMS)),
        "located_rows": _counter_frame(
            counters["located"], ["municipality_code", "year_month", "source_event"]
        ),
    }


def _derive_tables(
    tables: dict[str, pd.DataFrame], catalog: pd.DataFrame, config: AnalysisConfig
) -> None:
    """Derive calendar, coverage denominators and admission-for-review summaries."""
    grouped = tables.pop("accepted_monthly")
    if grouped.empty:
        monthly = pd.DataFrame(columns=["municipality_code", "year_month", *COUNTS.values()])
    else:
        monthly = (
            grouped.pivot(
                index=["municipality_code", "year_month"], columns="event", values="notifications"
            )
            .reindex(columns=list(COUNTS))
            .fillna(0)
        )
        monthly = monthly.rename(columns=COUNTS).reset_index()
    located = (
        tables.pop("located_rows")
        .pivot(
            index=["municipality_code", "year_month"],
            columns="source_event",
            values="notifications",
        )
        .reindex(columns=list(COUNTS))
        .fillna(0)
        .rename(columns={event: f"{column}_source_rows" for event, column in COUNTS.items()})
        .reset_index()
    )
    calendar = build_review_calendar(catalog, monthly, config, located)
    accepted = tables["record_reconciliation"].query("accepted")["notifications"].sum()
    if calendar[list(COUNTS.values())].to_numpy().sum() != accepted:
        raise ValueError("Accepted notification reconciliation failed")
    total = tables["source_records"]["rows"].sum()
    if tables["record_reconciliation"]["notifications"].sum() != total:
        raise ValueError("Source rows were lost in reconciliation")
    territorial = tables["territorial_discrepancies"]
    summary = territorial.groupby(["source", "territory_status"], as_index=False)[
        "notifications"
    ].sum()
    summary["source_notifications"] = summary.groupby("source")["notifications"].transform("sum")
    summary["proportion_of_source"] = summary["notifications"] / summary["source_notifications"]
    tables["territorial_coverage"] = summary
    valid = territorial.loc[territorial["territory_status"].eq("valid")]
    tables["territorial_totals"] = pd.DataFrame(
        [
            {
                "observed_valid_municipalities": valid["municipality_code"].nunique(),
                "observed_valid_departments": valid["municipality_code"].str[:2].nunique(),
                "catalog_territories": len(catalog),
                "catalog_departments": catalog["department_code"].nunique(),
                "unresolved_notifications": int(
                    territorial.loc[
                        ~territorial["territory_status"].eq("valid"), "notifications"
                    ].sum()
                ),
            }
        ]
    )
    tables["municipality_month"] = calendar
    tables["municipality_eligibility"] = calendar.groupby("municipality_code", as_index=False).agg(
        review_months=("year_month", "size"),
        dengue_months_with_rows=(f"{COUNTS['210']}_has_rows", "sum"),
        severe_months_with_rows=(f"{COUNTS['220']}_has_rows", "sum"),
        eligible_review_months=("eligible_for_canonical_review", "sum"),
        months_requiring_record_review=("requires_record_review", "sum"),
    )
    eligibility = tables["municipality_eligibility"]
    eligibility["months_without_any_rows"] = (
        calendar.assign(absent=~calendar[[f"{c}_has_rows" for c in COUNTS.values()]].any(axis=1))
        .groupby("municipality_code")["absent"]
        .sum()
        .to_numpy()
    )
    eligibility["intermittent_notifications"] = eligibility["months_without_any_rows"].between(
        1, eligibility["review_months"] - 1
    )
    eligibility["eligible_for_canonical_review"] = eligibility["eligible_review_months"].gt(0)
    eligibility["training_eligibility"] = "NOT_ASSESSED"
    tables["period_eligibility"] = calendar.groupby("year_month", as_index=False)[
        list(COUNTS.values())
    ].sum()
    tables["period_eligibility"]["eligible_territories_for_review"] = (
        calendar.groupby("year_month")["eligible_for_canonical_review"].sum().to_numpy()
    )
    temporal = tables["temporal_coverage"]
    tables["annual_notifications"] = temporal.groupby(["source", "onset_year"], as_index=False)[
        "notifications"
    ].sum()


def run_analysis(root: Path | None = None, config: AnalysisConfig | None = None) -> dict[str, Any]:
    """Run deterministic national diagnostics or report missing local inputs explicitly.

    Args:
        root: Optional repository root (normally discovered from existing project helpers).
        config: All adjustable analysis parameters.

    Returns:
        Status, aggregate tables and execution provenance. Private aggregates are
        written only after both streams and the catalogue are successfully processed.
    """
    root = (root or resolve_repo_root()).resolve()
    config = config or AnalysisConfig()
    output = root / config.output_dir
    if not output.resolve().is_relative_to(root / "data/interim/canonical-nacional-data"):
        raise ValueError("Output escapes diagnostic storage")
    output.mkdir(parents=True, exist_ok=True)
    inventory = inventory_sources(root)
    tables: dict[str, pd.DataFrame] = {"inventory": inventory}
    missing = inventory.loc[~inventory["available"], "source"].tolist()
    required = {SOURCES[0], SOURCES[1], SOURCES[3]}
    summary: dict[str, Any] = {
        "analysis": "Canonical-nacional-data",
        "config": asdict(config),
        "missing_sources": missing,
        "limitations": LIMITATIONS,
        "evidence": "NOT_SCIENTIFICALLY_VALIDATED",
        "status": "READY_FOR_LOCAL_EXECUTION",
        "sources": inventory.to_dict(orient="records"),
        "source_preservation": "NOT_CHECKED",
        "outputs": {},
    }
    # Stable metadata only when private inputs are absent; never emit a fake calendar.
    if not required.intersection(missing):
        catalog = load_national_catalog(root)
        with TemporaryDirectory(prefix=".duplicate-index-", dir=output) as scratch:
            with sqlite3.connect(Path(scratch) / "fingerprints.sqlite") as connection:
                tables.update(_scan_sources(root, catalog, config, connection))
        nonempty = tables["source_records"]["rows"].gt(0).all()
        accepted = tables["record_reconciliation"].query("accepted")["notifications"].sum()
        if nonempty and accepted > 0:
            _derive_tables(tables, catalog, config)
        else:
            tables.pop("accepted_monthly")
        summary["status"] = "READY_WITH_LIMITATIONS" if nonempty and accepted > 0 else "BLOCKED"
        summary["evidence"] = "RETROSPECTIVE_DIAGNOSTICS_ONLY"
        summary["recommendation"] = (
            "Review unresolved geography, historical catalogue applicability, extraction coverage "
            "and climate before defining a national canonical contract or G1 admission."
        )
    after = inventory_sources(root)
    if not inventory.equals(after):
        raise ValueError("Sources changed during analysis; no outputs published")
    summary["source_preservation"] = "PASS"
    if inventory["integrity"].eq("mismatch").any():
        summary["status"] = "BLOCKED"
        summary["recommendation"] = (
            "Resolve source identity mismatches before canonical construction."
        )
    # Content-derived folders keep missing-source runs separate from earlier private tables.
    summary["code_sha256"] = fingerprint(Path(__file__))["sha256"]
    summary["calculation_code_sha256"] = fingerprint(Path(__file__).with_name("consolidation.py"))[
        "sha256"
    ]
    summary["runtime"] = {"python": platform.python_version(), "pandas": pd.__version__}
    execution_key = hashlib.sha256(
        json.dumps(summary, sort_keys=True, default=str).encode()
    ).hexdigest()[:20]
    destination = output / execution_key
    destination.mkdir(exist_ok=True)
    for name, table in sorted(tables.items()):
        path = destination / f"{name}.csv"
        table.to_csv(path, index=False)
        summary["outputs"][name] = {"path": str(path.relative_to(root)), **fingerprint(path)}
    summary["execution_id"] = execution_key
    (destination / "execution_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {"summary": summary, "tables": tables}
