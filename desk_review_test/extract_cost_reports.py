#!/usr/bin/env python3
"""Normalize district salary reports into SQLite and CSV exports."""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cost_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_name TEXT NOT NULL,
    year_end TEXT NOT NULL,
    employee_name TEXT NOT NULL,
    salary NUMERIC,
    healthcare NUMERIC,
    retirement NUMERIC,
    federal_pct REAL,
    state_pct REAL,
    source_file TEXT NOT NULL,
    validation_passed INTEGER NOT NULL,
    validation_errors TEXT
);

CREATE TABLE IF NOT EXISTS contact_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_name TEXT NOT NULL,
    year_end TEXT NOT NULL,
    contact_name TEXT,
    contact_email TEXT,
    source_file TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS desk_review_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_name TEXT NOT NULL,
    year_end TEXT NOT NULL,
    report_id TEXT NOT NULL,
    finding_1_text TEXT NOT NULL,
    finding_1_x INTEGER NOT NULL,
    finding_1_y INTEGER NOT NULL,
    finding_2_text TEXT NOT NULL,
    finding_2_flag INTEGER NOT NULL,
    healthcare_pct_of_total_salary REAL,
    state_salary_threshold NUMERIC,
    healthcare_threshold NUMERIC
);
"""


STATE_SALARY_THRESHOLD = 60000
HEALTHCARE_THRESHOLD = 0.07

FINDING_1_TEMPLATE = (
    "For {x} of {y} employees, the district charged over the ${threshold:,.0f} "
    "threshold for state-related salary costs."
)
FINDING_2_TEXT = "District charged healthcare costs over 7% of total salaries."


@dataclass
class ReportMetadata:
    district_name: str
    year_end: str
    contact_name: str
    contact_email: str


def discover_workbooks(data_dir: Path) -> List[Path]:
    return sorted(
        p for p in data_dir.glob("*.xlsx") if not p.name.startswith("~$")
    )


def parse_input_metadata(workbook: Path) -> ReportMetadata:
    df = pd.read_excel(workbook, sheet_name="Input Data", header=None)
    df = df.dropna(how="all")

    district_name: Optional[str] = None
    year_end_value: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None

    for _, row in df.iterrows():
        key_cell = row.iloc[0]
        if isinstance(key_cell, str) and key_cell.endswith(":"):
            label = key_cell[:-1].strip().lower()
            value = row.iloc[1] if len(row) > 1 else None
            if pd.isna(value):
                value = None
            if label == "district name" and value is not None:
                district_name = str(value).strip()
            elif label == "year end" and value is not None:
                try:
                    year_end_value = pd.to_datetime(value).date().isoformat()
                except Exception:
                    year_end_value = str(value)
            elif label == "contact name" and value is not None:
                contact_name = str(value).strip()
            elif label == "contact email" and value is not None:
                contact_email = str(value).strip()

    if not district_name:
        district_name = workbook.stem.replace("Salary_Report_", "").replace("_", " ")
    if not year_end_value:
        year_end_value = ""

    return ReportMetadata(
        district_name=district_name,
        year_end=year_end_value,
        contact_name=contact_name or "",
        contact_email=contact_email or "",
    )


def _as_number(value) -> Optional[float]:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        sanitized = str(value).replace("$", "").replace(",", "").strip()
        return float(sanitized)
    except Exception:
        return None


def _as_fraction(value) -> Optional[float]:
    number = _as_number(value)
    if number is None:
        return None
    if number > 1:
        return number / 100.0
    return number


def safe_number(value: Optional[float]) -> float:
    return float(value) if value is not None else 0.0


def calculate_employee_metrics(record: dict) -> dict:
    """Compute per-employee desk review metrics using extracted fields."""

    salary = safe_number(record.get("salary"))
    healthcare = safe_number(record.get("healthcare"))
    retirement = safe_number(record.get("retirement"))
    total_payroll = salary + healthcare + retirement

    state_pct = record.get("state_pct") or 0.0
    federal_pct = record.get("federal_pct") or 0.0

    # Percentages in the workbook describe how salary dollars were funded,
    # so the state/federal portions are calculated on salary only.
    state_portion = salary * state_pct
    federal_portion = salary * federal_pct

    healthcare_pct_total = (healthcare / total_payroll) if total_payroll else 0.0
    retirement_pct_total = (retirement / total_payroll) if total_payroll else 0.0

    return {
        "total_payroll_costs": total_payroll,
        "state_portion_of_total_payroll_costs": state_portion,
        "federal_portion_of_total_payroll_costs": federal_portion,
        "healthcare_percentage_of_total_payroll_costs": healthcare_pct_total,
        "retirement_percentage_of_total_payroll_costs": retirement_pct_total,
    }


def perform_desk_review(records: List[dict]) -> List[dict]:
    """Aggregate per-employee metrics into district-level desk review findings."""

    grouped: Dict[tuple[str, str, str], dict] = {}
    for record in records:
        key = (record["district_name"], record["source_file"], record["year_end"])
        metrics = calculate_employee_metrics(record)
        bucket = grouped.setdefault(
            key,
            {
                "total_employees": 0,
                "over_state_threshold": 0,
                "total_salary": 0.0,
                "total_healthcare": 0.0,
            },
        )
        bucket["total_employees"] += 1
        if (
            metrics["state_portion_of_total_payroll_costs"]
            > STATE_SALARY_THRESHOLD
        ):
            bucket["over_state_threshold"] += 1
        bucket["total_salary"] += safe_number(record.get("salary"))
        bucket["total_healthcare"] += safe_number(record.get("healthcare"))

    findings: List[dict] = []
    for (district, report_id, year_end), bucket in grouped.items():
        total_salary = bucket["total_salary"]
        # Apply the healthcare threshold to the aggregate ratio (district totals
        # divided by total salaries) so reviewers see report-level exposure.
        healthcare_ratio = (
            bucket["total_healthcare"] / total_salary if total_salary else 0.0
        )
        finding_2_flag = healthcare_ratio > HEALTHCARE_THRESHOLD
        finding_1_text = FINDING_1_TEMPLATE.format(
            x=bucket["over_state_threshold"],
            y=bucket["total_employees"],
            threshold=STATE_SALARY_THRESHOLD,
        )
        findings.append(
            {
                "district_name": district,
                "year_end": year_end,
                "report_id": report_id,
                "finding_1_text": finding_1_text,
                "finding_1_x": bucket["over_state_threshold"],
                "finding_1_y": bucket["total_employees"],
                "finding_2_text": FINDING_2_TEXT,
                "finding_2_flag": finding_2_flag,
                "healthcare_pct_of_total_salary": healthcare_ratio,
                "state_salary_threshold": STATE_SALARY_THRESHOLD,
                "healthcare_threshold": HEALTHCARE_THRESHOLD,
            }
        )

    return findings


def parse_salary_rows(workbook: Path, metadata: ReportMetadata) -> List[dict]:
    df_raw = pd.read_excel(workbook, sheet_name="Salaries", header=None)
    df_raw = df_raw.dropna(how="all")
    if len(df_raw) < 3:
        return []

    header_series = df_raw.iloc[1].ffill()
    header = [str(value).strip() for value in header_series]
    df = df_raw.iloc[2:].copy()
    df.columns = header
    df = df.rename(columns=lambda c: str(c).strip())
    df = df.dropna(how="all")
    if "Name" not in df.columns:
        return []
    df = df[df["Name"].notna()]

    records: List[dict] = []
    for _, row in df.iterrows():
        employee_name = str(row.get("Name", "")).strip()
        if not employee_name:
            continue
        records.append(
            {
                "district_name": metadata.district_name,
                "year_end": metadata.year_end,
                "employee_name": employee_name,
                "salary": _as_number(row.get("Salaries")),
                "healthcare": _as_number(row.get("Healthcare")),
                "retirement": _as_number(row.get("Retirement")),
                "federal_pct": _as_fraction(row.get("Federal Funding %")),
                "state_pct": _as_fraction(row.get("State Funding %")),
                "source_file": workbook.name,
            }
        )
    return records


def load_records(workbooks: Iterable[Path]) -> tuple[List[dict], List[dict]]:
    salary_rows: List[dict] = []
    contact_rows: List[dict] = []
    for workbook in workbooks:
        metadata = parse_input_metadata(workbook)
        salary_rows.extend(parse_salary_rows(workbook, metadata))
        contact_rows.append(
            {
                "district_name": metadata.district_name,
                "year_end": metadata.year_end,
                "contact_name": metadata.contact_name,
                "contact_email": metadata.contact_email,
                "source_file": workbook.name,
            }
        )
    return salary_rows, contact_rows


def validate_cost_reports(
    salary_records: List[dict], workbook_paths: Sequence[Path]
) -> tuple[List[dict], Dict[str, dict]]:
    summary: Dict[str, dict] = {path.name: {"errors": []} for path in workbook_paths}
    amount_fields = [field for field in ("salary", "healthcare", "retirement")]
    percent_fields = [field for field in ("federal_pct", "state_pct")]

    for record in salary_records:
        errors: List[str] = []
        source_file = record.get("source_file", "unknown")
        summary.setdefault(source_file, {"errors": []})

        name_value = record.get("employee_name")
        if not isinstance(name_value, str) or not name_value.strip():
            errors.append("Missing employee name")

        for field in amount_fields:
            value = record.get(field)
            if value is None or not isinstance(value, (int, float)):
                errors.append(f"{field} missing or non-numeric")

        percent_missing = False
        percent_total = 0.0
        for field in percent_fields:
            value = record.get(field)
            if value is None or not isinstance(value, (int, float)):
                errors.append(f"{field} missing or non-numeric")
                percent_missing = True
                continue
            if not (0 <= value <= 1):
                errors.append(f"{field} out of range [0, 1]")
            percent_total += value

        if not percent_missing and percent_total:
            if abs(percent_total - 1.0) > 1e-3:
                errors.append("Percent fields must sum to 1")

        record["validation_passed"] = len(errors) == 0
        record["validation_errors"] = "; ".join(errors)
        summary[source_file]["errors"].extend(errors)

    for file_name, data in summary.items():
        data["passed"] = len(data["errors"]) == 0

    return salary_records, summary


def persist_to_sqlite(
    salary_records: List[dict],
    contact_records: List[dict],
    desk_review_records: List[dict],
    database_path: Path,
) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as conn:
        conn.execute("DROP TABLE IF EXISTS cost_reports")
        conn.execute("DROP TABLE IF EXISTS contact_info")
        conn.execute("DROP TABLE IF EXISTS desk_review_findings")
        conn.executescript(SCHEMA_SQL)
        conn.executemany(
            """
            INSERT INTO cost_reports (
                district_name,
                year_end,
                employee_name,
                salary,
                healthcare,
                retirement,
                federal_pct,
                state_pct,
                source_file,
                validation_passed,
                validation_errors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r["district_name"],
                    r["year_end"],
                    r["employee_name"],
                    r["salary"],
                    r["healthcare"],
                    r["retirement"],
                    r["federal_pct"],
                    r["state_pct"],
                    r["source_file"],
                    1 if r.get("validation_passed") else 0,
                    r.get("validation_errors", ""),
                )
                for r in salary_records
            ],
        )
        conn.executemany(
            """
            INSERT INTO contact_info (
                district_name,
                year_end,
                contact_name,
                contact_email,
                source_file
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    r["district_name"],
                    r["year_end"],
                    r["contact_name"],
                    r["contact_email"],
                    r["source_file"],
                )
                for r in contact_records
            ],
        )
        conn.executemany(
            """
            INSERT INTO desk_review_findings (
                district_name,
                year_end,
                report_id,
                finding_1_text,
                finding_1_x,
                finding_1_y,
                finding_2_text,
                finding_2_flag,
                healthcare_pct_of_total_salary,
                state_salary_threshold,
                healthcare_threshold
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r["district_name"],
                    r["year_end"],
                    r["report_id"],
                    r["finding_1_text"],
                    r["finding_1_x"],
                    r["finding_1_y"],
                    r["finding_2_text"],
                    1 if r["finding_2_flag"] else 0,
                    r["healthcare_pct_of_total_salary"],
                    r["state_salary_threshold"],
                    r["healthcare_threshold"],
                )
                for r in desk_review_records
            ],
        )


def export_records(records: List[dict], export_path: Path) -> None:
    if not records:
        raise ValueError("No records were parsed; nothing to export.")
    df = pd.DataFrame(records)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    if export_path.suffix.lower() == ".xlsx":
        df.to_excel(export_path, index=False)
    else:
        df.to_csv(export_path, index=False)


def export_contact_records(records: List[dict], export_path: Path) -> None:
    export_records(records, export_path)


def export_desk_review(records: List[dict], export_path: Path) -> None:
    export_records(records, export_path)


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).parent
    parser = argparse.ArgumentParser(
        description=(
            "Normalize Input Data and Salaries tabs across salary workbooks, "
            "store them in SQLite, and export a combined flat file."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_root / "test_data",
        help="Folder that contains Salary_Report_*.xlsx files.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=default_root / "cost_reports.db",
        help="SQLite database path to create or overwrite.",
    )
    parser.add_argument(
        "--export",
        type=Path,
        default=default_root / "combined_cost_reports.csv",
        help="Path for the combined export (.csv or .xlsx).",
    )
    parser.add_argument(
        "--contact-export",
        type=Path,
        default=default_root / "contact_info.csv",
        help="Path for contact export (.csv or .xlsx).",
    )
    parser.add_argument(
        "--desk-review-export",
        type=Path,
        default=default_root / "desk_review_findings.csv",
        help="Path for desk review summary export (.csv or .xlsx).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbooks = discover_workbooks(args.data_dir)
    if not workbooks:
        raise SystemExit(f"No .xlsx files found in {args.data_dir}")

    salary_records, contact_records = load_records(workbooks)
    if not salary_records:
        raise SystemExit("No salary rows detected in the provided workbooks.")

    salary_records, validation_summary = validate_cost_reports(
        salary_records, workbooks
    )
    for file_name, info in validation_summary.items():
        if info["passed"]:
            continue
        reasons = ", ".join(sorted(set(info["errors"]))) or "Unknown reason"
        print(f"Validation failed for {file_name}: {reasons}")

    desk_review_records = perform_desk_review(salary_records)

    persist_to_sqlite(
        salary_records, contact_records, desk_review_records, args.database
    )
    export_records(salary_records, args.export)
    export_contact_records(contact_records, args.contact_export)
    export_desk_review(desk_review_records, args.desk_review_export)

    print(f"Loaded {len(salary_records)} salary rows from {len(workbooks)} workbooks.")
    print(f"Captured {len(contact_records)} contact rows.")
    print(f"Generated desk review summaries for {len(desk_review_records)} reports.")
    print(f"SQLite database: {args.database}")
    print(f"Combined export: {args.export}")
    print(f"Contact export: {args.contact_export}")
    print(f"Desk review export: {args.desk_review_export}")


if __name__ == "__main__":
    main()
