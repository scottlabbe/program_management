import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence

from docx2pdf import convert as docx2pdf_convert
from docxtpl import DocxTemplate


LETTER_TEMPLATE_NAME = "desk_review_letter_template.docx"
FINDINGS_TEMPLATE_NAME = "desk_review_findings_template.docx"


def format_currency(value: float) -> str:
    value = value or 0.0
    return f"{value:,.2f}"


def safe_fragment(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in (" ", "_", "-") else "_" for ch in text).strip() or "district"


def get_all_districts(db_path: str) -> List[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT district_name FROM cost_reports ORDER BY district_name"
        ).fetchall()
    return [row[0] for row in rows]


def _extract_year(year_end: str) -> str:
    if not year_end:
        return ""
    try:
        return datetime.strptime(year_end, "%Y-%m-%d").strftime("%Y")
    except ValueError:
        return year_end[:4]


def get_district_summary(db_path: str, district_name: str) -> Dict[str, float]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        summary = conn.execute(
            """
            SELECT
                district_name,
                year_end,
                SUM(salary * state_pct) AS state_salary_total,
                SUM((healthcare + retirement) * state_pct) AS state_fringe_total,
                SUM(salary * federal_pct) AS federal_salary_total,
                SUM((healthcare + retirement) * federal_pct) AS federal_fringe_total
            FROM cost_reports
            WHERE district_name = ?
            GROUP BY district_name, year_end
            ORDER BY year_end DESC
            LIMIT 1
            """,
            (district_name,),
        ).fetchone()

        if not summary:
            raise ValueError(f"No cost report data found for {district_name}")

        contact = conn.execute(
            """
            SELECT contact_name
            FROM contact_info
            WHERE district_name = ?
            ORDER BY year_end DESC
            LIMIT 1
            """,
            (district_name,),
        ).fetchone()

        position_title = contact["contact_name"] if contact and contact["contact_name"] else "Program Contact"

        state_salary = summary["state_salary_total"] or 0.0
        state_fringe = summary["state_fringe_total"] or 0.0
        federal_salary = summary["federal_salary_total"] or 0.0
        federal_fringe = summary["federal_fringe_total"] or 0.0

        return {
            "district_name": summary["district_name"],
            "position_title": position_title,
            "fiscal_year": _extract_year(summary["year_end"]),
            "state_salary_total": state_salary,
            "state_fringe_total": state_fringe,
            "state_reimbursement_total": state_salary + state_fringe,
            "federal_salary_total": federal_salary,
            "federal_fringe_total": federal_fringe,
            "federal_reimbursement_total": federal_salary + federal_fringe,
        }
    finally:
        conn.close()


def get_district_findings(db_path: str, district_name: str) -> List[str]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                finding_1_text,
                finding_1_x,
                finding_2_text,
                finding_2_flag
            FROM desk_review_findings
            WHERE district_name = ?
            ORDER BY year_end DESC
            """,
            (district_name,),
        ).fetchall()
    finally:
        conn.close()

    findings: List[str] = []
    for row in rows:
        finding_1_text = row["finding_1_text"]
        finding_1_x = row["finding_1_x"]
        if finding_1_text and str(finding_1_text).strip() and (finding_1_x or 0) > 0:
            findings.append(finding_1_text.strip())

        finding_2_text = row["finding_2_text"]
        finding_2_flag = row["finding_2_flag"]
        if finding_2_text and str(finding_2_text).strip() and bool(finding_2_flag):
            findings.append(finding_2_text.strip())
    return findings


def fill_letter_template(data_dict: Dict[str, str], template_path: Path, output_path: Path) -> None:
    template = DocxTemplate(str(template_path))
    template.render(data_dict)
    template.save(str(output_path))


def fill_findings_template(data_dict: Dict[str, str], template_path: Path, output_path: Path) -> None:
    template = DocxTemplate(str(template_path))
    template.render(data_dict)
    template.save(str(output_path))


def convert_to_pdf(docx_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    docx2pdf_convert(str(docx_path), str(pdf_path))


def build_letter_context(summary: Dict[str, float]) -> Dict[str, str]:
    context = {
        "current_date": datetime.today().strftime("%B %d, %Y"),
        "position_title": summary["position_title"],
        "district_name": summary["district_name"],
        "fiscal_year": summary["fiscal_year"],
        "state_salary_total": format_currency(summary["state_salary_total"]),
        "state_fringe_total": format_currency(summary["state_fringe_total"]),
        "state_reimbursement_total": format_currency(summary["state_reimbursement_total"]),
        "federal_salary_total": format_currency(summary["federal_salary_total"]),
        "federal_fringe_total": format_currency(summary["federal_fringe_total"]),
        "federal_reimbursement_total": format_currency(summary["federal_reimbursement_total"]),
    }
    return context


def build_findings_context(summary: Dict[str, float], findings: Sequence[str]) -> Dict[str, object]:
    return {
        "district_name": summary["district_name"],
        "fiscal_year": summary["fiscal_year"],
        "findings": [{"text": finding} for finding in findings],
    }


def generate_reports(db_path: str, template_dir: str, output_dir: str) -> None:
    template_dir_path = Path(template_dir)
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    letter_template = template_dir_path / LETTER_TEMPLATE_NAME
    findings_template = template_dir_path / FINDINGS_TEMPLATE_NAME

    if not letter_template.exists():
        raise FileNotFoundError(f"Missing letter template: {letter_template}")
    if not findings_template.exists():
        raise FileNotFoundError(f"Missing findings template: {findings_template}")

    districts = get_all_districts(db_path)
    errors: Dict[str, str] = {}

    for district in districts:
        try:
            summary = get_district_summary(db_path, district)
            letter_context = build_letter_context(summary)
            findings_context = build_findings_context(summary, get_district_findings(db_path, district))

            district_folder_name = safe_fragment(district)
            district_dir = output_dir_path / district_folder_name
            district_dir.mkdir(parents=True, exist_ok=True)

            letter_docx = district_dir / f"desk_review_letter_{district_folder_name}.docx"
            letter_pdf = district_dir / f"desk_review_letter_{district_folder_name}.pdf"
            findings_docx = district_dir / f"desk_review_findings_{district_folder_name}.docx"
            findings_pdf = district_dir / f"desk_review_findings_{district_folder_name}.pdf"

            fill_letter_template(letter_context, letter_template, letter_docx)
            fill_findings_template(findings_context, findings_template, findings_docx)

            convert_to_pdf(letter_docx, letter_pdf)
            convert_to_pdf(findings_docx, findings_pdf)
        except Exception as exc:  # noqa: BLE001
            errors[district] = str(exc)

    processed = len(districts) - len(errors)
    print(f"Processed {processed}/{len(districts)} districts.")
    if errors:
        print("Errors encountered:")
        for district, message in errors.items():
            print(f"- {district}: {message}")
    else:
        print("All districts processed successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate desk review reports for all districts.")
    parser.add_argument(
        "--db-path",
        default="extract_data/cost_reports.db",
        help="Path to the SQLite database with desk review data.",
    )
    parser.add_argument(
        "--template-dir",
        default="templates",
        help="Directory containing the Word templates.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory where generated reports will be saved.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_reports(args.db_path, args.template_dir, args.output_dir)
