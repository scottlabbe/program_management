
## Prompt

## Context
The database `program_management/extract_data/cost_reports.db` contains desk-reviewed data for multiple districts. Schema reference is in `DATABASE_REFERENCE.md`.

Tables you'll use:
- `cost_reports` – employee-level salary/benefits data
- `contact_info` – district contact metadata  
- `desk_review_findings` – finding narratives per district

The folder `templates/` contains:
- `desk_review_letter_template.docx`
- `desk_review_findings_template.docx`

Both templates use Jinja2-style placeholders.

## Goal
Build a reporting script that:
1. Reads all districts from the database
2. Aggregates cost data per district (state vs. federal totals)
3. Fills in both Word templates for each district
4. Converts each to PDF
5. Saves outputs in a structured folder

## Template field mappings

### desk_review_letter_template.docx
| Placeholder | Source |
|-------------|--------|
| `{{ current_date }}` | Today's date (format: Month DD, YYYY) |
| `{{ position_title }}` | `contact_info.contact_name` |
| `{{ district_name }}` | District name |
| `{{ fiscal_year }}` | `cost_reports.year_end` (extract year) |
| `{{ state_salary_total }}` | SUM of `salary * state_pct` for district |
| `{{ state_fringe_total }}` | SUM of `(healthcare + retirement) * state_pct` |
| `{{ state_reimbursement_total }}` | state_salary_total + state_fringe_total |
| `{{ federal_salary_total }}` | SUM of `salary * federal_pct` for district |
| `{{ federal_fringe_total }}` | SUM of `(healthcare + retirement) * federal_pct` |
| `{{ federal_reimbursement_total }}` | federal_salary_total + federal_fringe_total |

### desk_review_findings_template.docx
| Placeholder | Source |
|-------------|--------|
| `{{ district_name }}` | District name |
| `{{ fiscal_year }}` | Year from `year_end` |
| `{{ findings }}` | List of finding objects with `.text` attribute, built from `finding_1_text`, `finding_2_text` in `desk_review_findings` (include only non-null findings) |

## Output structure
```
reports/
  <district_name>/
    desk_review_letter_<district_name>.docx
    desk_review_letter_<district_name>.pdf
    desk_review_findings_<district_name>.docx
    desk_review_findings_<district_name>.pdf
```

## Constraints
- Do not modify any template formatting, fonts, or boilerplate text
- Only populate the placeholder fields listed above
- Format currency values with commas and 2 decimal places
- If a district has no findings, the findings template should render "No findings identified."

## Implementation notes
- Use `python-docx` for Word template filling (or `docxtpl` for Jinja2 syntax)
- Use a library like `docx2pdf` for PDF conversion
- Write modular helper functions:
  - `get_district_summary(db_path, district_name)` → returns dict of aggregated values
  - `get_district_findings(db_path, district_name)` → returns list of finding texts
  - `fill_letter_template(data_dict, template_path, output_path)`
  - `fill_findings_template(data_dict, template_path, output_path)`
  - `convert_to_pdf(docx_path, pdf_path)`
- Add a CLI entrypoint: `generate_reports(db_path, template_dir, output_dir)`
- Print a summary at the end: how many districts processed, any errors
```

