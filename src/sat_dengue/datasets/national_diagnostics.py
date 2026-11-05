"""Filesystem/SQLite adapter for the unchanged pure national diagnostic calculations."""

from __future__ import annotations

import hashlib
import json
import platform
import sqlite3
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.consolidation import normalize_code_series
from sat_dengue.data.national_diagnostics import (
    COUNTS as COUNTS,
)
from sat_dengue.data.national_diagnostics import (
    ESSENTIAL,
    LIMITATIONS,
    SOURCES,
    STREAMS,
    _counter_frame,
    _derive_tables,
    _increment,
)
from sat_dengue.data.national_diagnostics import (
    AnalysisConfig as AnalysisConfig,
)
from sat_dengue.data.national_diagnostics import (
    build_review_calendar as build_review_calendar,
)
from sat_dengue.data.national_diagnostics import (
    classify_notifications as classify_notifications,
)
from sat_dengue.datasets.legacy_consolidation import resolve_repo_root
from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, SOURCE_IDENTITIES


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
    summary["domain_code_sha256"] = fingerprint(
        Path(__file__).parents[1] / "data/national_diagnostics.py"
    )["sha256"]
    summary["calculation_code_sha256"] = fingerprint(
        Path(__file__).parents[1] / "data/consolidation.py"
    )["sha256"]
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
