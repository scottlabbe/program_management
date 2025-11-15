#!/usr/bin/env python3
"""Normalize district salary reports into SQLite and CSV exports."""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

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
    source_file TEXT NOT NULL
);
"""


@dataclass
class ReportMetadata:
    district_name: str
    year_end: str


def discover_workbooks(data_dir: Path) -> List[Path]:
    return sorted(
        p for p in data_dir.glob("*.xlsx") if not p.name.startswith("~$")
    )


def parse_input_metadata(workbook: Path) -> ReportMetadata:
    df = pd.read_excel(workbook, sheet_name="Input Data", header=None)
    df = df.dropna(how="all")

    district_name: Optional[str] = None
    year_end_value: Optional[str] = None

    for _, row in df.iterrows():
        key_cell = row.iloc[0]
        if isinstance(key_cell, str) and key_cell.endswith(":"):
            label = key_cell[:-1].strip().lower()
            value = row.iloc[1] if len(row) > 1 else None
            if pd.isna(value):
                value = None
            if label == "district name" and value is not None:
                district_name = str(value).strip()
            if label == "year end" and value is not None:
                try:
                    year_end_value = pd.to_datetime(value).date().isoformat()
                except Exception:
                    year_end_value = str(value)

    if not district_name:
        district_name = workbook.stem.replace("Salary_Report_", "").replace("_", " ")
    if not year_end_value:
        year_end_value = ""

    return ReportMetadata(district_name=district_name, year_end=year_end_value)


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


def load_records(workbooks: Iterable[Path]) -> List[dict]:
    combined: List[dict] = []
    for workbook in workbooks:
        metadata = parse_input_metadata(workbook)
        combined.extend(parse_salary_rows(workbook, metadata))
    return combined


def persist_to_sqlite(records: List[dict], database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as conn:
        conn.execute("DROP TABLE IF EXISTS cost_reports")
        conn.execute(SCHEMA_SQL)
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
                source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                )
                for r in records
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbooks = discover_workbooks(args.data_dir)
    if not workbooks:
        raise SystemExit(f"No .xlsx files found in {args.data_dir}")

    records = load_records(workbooks)
    if not records:
        raise SystemExit("No salary rows detected in the provided workbooks.")

    persist_to_sqlite(records, args.database)
    export_records(records, args.export)

    print(f"Loaded {len(records)} salary rows from {len(workbooks)} workbooks.")
    print(f"SQLite database: {args.database}")
    print(f"Combined export: {args.export}")


if __name__ == "__main__":
    main()
