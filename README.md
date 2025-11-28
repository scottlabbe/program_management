# Cost Report Extraction with Codex CLI

This example shows how to use OpenAI’s Codex CLI as a local coding agent to automate a real-world data extraction workflow:

- Read multiple cost report spreadsheets from a folder  
- Extract specific tabs (`Input Data` and `Salaries`)  
- Normalize them into a clear data schema  
- Load the data into a SQLite database  
- Export a combined dataset to Excel/CSV  

All spreadsheets in this repo use **synthetic data** that mimics real report layouts — never use sensitive or confidential data directly with AI tools unless you fully understand your security and privacy setup.

Follow along with YouTube walkthrough
- Part 1 - Extract Data: https://youtu.be/kAkkZ_oGTsE
- Part 2 - Validate and Desk Review Data: https://youtu.be/rD345V1tGus

---

## Project Structure

The `extract` folder is the folder where OpenAI's Codex coding agent builds each step of extract, validation, desk review, reporting and visualization steps. This will grow throughout the video series. 

The folders that end with `..._test` are the folders where I copied the `test_data` folder and the new extract_cost_reports.py file at each step to review and test the output and verify it's exactly what I need. 

---

## What You’ll Get

By following this guide, you’ll end up with:

1. A CLI script that extracts data from all cost report files.
2. A consistent data schema across reports.
3. A persistent `SQLite` database (for queries, checks, audits).
4. An Excel/CSV export suitable for build further analysis, desk reviews, or reporting.
5. A pattern you can reuse for other repetitive spreadsheet workflows.

You own the code. You can re-run it on your machine as often as you like without depending on any third-party “platform.”

---

## Prerequisites

You’ll need (ask for help via AI tools like ChatGPT):

- A ChatGPT / OpenAI plan that supports using Codex CLI (see OpenAI docs for current requirements).
- **Node.js + npm** _or_ **Homebrew** to install Codex CLI.
- **VS Code** to view and run the generated code.
- A Mac or Linux machine. (Windows users can use WSL; follow the Codex CLI docs.)

### Install Codex CLI

(Confirm exact install instructions in the official docs; example:)

```bash
# Using npm
npm install -g @openai/codex

# Or with Homebrew (if available)
brew install codex
```

Then authenticate:

```bash
codex
```

On first run you’ll be prompted to sign in or configure credentials.

---

## Test Data - Cost Report Spreadsheets

Each file in the `test_data` includes example tabs like:

- `Input Data`
- `Salaries`

These mirror common cost report layouts used in reimbursement and program oversight. You can use the compiled data for analysis, cost reporting, or desk review processes. 

---

## Step-by-Step: Use Codex to Build the Extractor

### 1. Open the folder in VS Code

1. Open VS Code.  
2. Go to **File → Open Folder…**  
3. Navigate to and select the `program_management` folder.

This lets you see whatever Codex generates as it works.

---

### 2. Start Codex in the correct directory

Copy the path/address to the `program_management` folder.
Open your terminal and navigate to the project:

```bash
cd /path/to/program_management
```

Verify contents:

```bash
ls
# Expect: extract_data
```

Start Codex:

```bash
codex
```

Codex should now be running **inside** `program_management`, with access to the files under this folder.

---

### 3. Provide a clear prompt to Codex - Extract Data

Use a prompt along these lines:

> The purpose of this folder is to build tools for a program manager or auditor.  
> In the `extract` folder, please:
> 1. Inspect the spreadsheets in the `extract/test_data` folder.  
> 2. Extract all data from the `Input Data` and `Salaries` tabs across all files.  
> 3. Propose a clean, explicit data schema for the combined dataset.  
> 4. Implement a script that:
>    - reads every file in `test_data`,
>    - normalizes the data into that schema,
>    - loads it into a local SQLite database (e.g. `cost_reports.db`), and
>    - exports the combined results to an Excel or CSV file (e.g. `combined_cost_reports.xlsx`).  
> 5. Add simple instructions to a `RUN.md` explaining how to run the scripts in VScode.
>
> Work step-by-step:
> - First, print the plan for my review.
> - Wait for approval.
> - Then create the scripts and any helper modules in the `extract` folder.

Then:

1. Review the plan Codex prints.  
2. Approve or adjust as needed.

---

### 4. Run the generated scripts

Run the instructions provided by Codex or follow the general instructions.

General insturctions: 
Once Codex has created the extraction script, copy the resulting extract script and the `test_data` to a new `test` folder.

In VS Code select **Terminal → New Terminal** and navigate to the new test folder (it opens in the workspace root by default). 

```bash
cd /path/to/program_management/..._test
```

run:

```bash
python extract_cost_reports.py
```

(or whatever filename Codex chose)

You should now see outputs such as:

- `cost_reports.db` – SQLite database with combined data.
- `combined_cost_reports.xlsx` – normalized export (use the `--export` flag for `.csv` instead).

---

### 5. Verify the Results

Before treating this as a trusted tool:

1. Open a few original cost report spreadsheets in `test_data`.
2. Compare:
   - row counts,
   - sample records,
   - key totals (e.g. salaries, FTEs),
   against the database and export.
3. If anything looks wrong:
   - describe the issue to Codex,
   - let it update the script,
   - re-run and re-check.

Verification is essential, especially if you adapt this pattern for real programs or audits.

---

## Use Codex to Build the Validator

Follow steps 1-2 from above. 

Prompt:
> Add a validation step that runs after extraction and before desk review. Implement it in a clearly named function (for example, validate_cost_reports(...)).
> In the `extract` folder, please add:
> Validation requirements (adapt these to the actual column names you find):
> - Name fields - All employee name fields must be non-empty text.
> - Amount fields - All amount fields (e.g., salary, state share, federal share, healthcare, retirement) must be numeric and non-null.
> - Percent fields - Be numeric, Have values between 0 and 1 and sum to 1. 
>
> For each cost report file:
> Determine whether it passes or fails validation. 
> - If it fails: Print a clear message to the console with the file name and the reasons (e.g., missing names, invalid amounts, bad percentages).
> - In the final extracted and validated dataset: Add a column such as validation_passed (boolean) and validation_errors (string or JSON) at the report level or employee level, depending on how the data is structured.

Then:

1. Review the plan Codex prints.  
2. Approve or adjust as needed.

Follow steps 4-5 to run the resulting code for yourself.

---

## Use Codex to Build the Desk Review Process

Follow steps 1-2 from above. 

Prompt:
> Add a desk review step that operates per employee/person after validation. Implement it in a function (for example, perform_desk_review(...)).
> In the `extract` folder, please add:
> For each employee, calculate:
> - total_payroll_costs
> - state_portion_of_total_payroll_costs
> - federal_portion_of_total_payroll_costs
> - healthcare_percentage_of_total_payroll_costs
> - retirement_percentage_of_total_payroll_costs
>
> Use the fields already being extracted in cost_report_extract.py. If needed, create helper functions for these calculations and keep the math clearly documented in code comments.
>
> Implement the desk review findings
> Based on the per-employee calculations, implement these two findings at the cost report / district level:
> Finding #1 Text: “For X of Y employees, the district charged over the $60,000 threshold for state-related salary costs.”
> Finding #2 Text: “District charged healthcare costs over 7% of total salaries.”
>
> - This should be true if the average or aggregate healthcare cost percentage across employees exceeds 7% of total salaries for the report.
> - Document in code whether you are:
> - Comparing at the aggregate level, or
> - Flagging if any individual employee exceeds 7%.
> - Implement the 7% threshold as a constant so it can be easily changed later.
>
> Store these findings in a way that can be exported, for example:
> One row per cost report in a summary table with:
> - report_id / file_name
> - finding_1_text
> - finding_1_x
> - finding_1_y
> - finding_2_text
> - finding_2_flag (True/False)

Then:

1. Review the plan Codex prints.  
2. Approve or adjust as needed.

Follow steps 4-5 to run the resulting code for yourself.

---

## Using This Pattern on Real Data

When you’re satisfied:

1. Move the generated scripts into your secure environment.
2. Update paths so they point to your real cost report folder instead of `test_data`.
3. Run locally in that environment.

Guidelines:

- Design and debug with synthetic/anonymized data.
- Only use real data when:
  - you control where code runs,
  - credentials and storage are secured,
  - outputs are validated.

---

## Tips

- Be concrete in your instructions to Codex: files, tabs, data schema, calculations, outputs.
- Let Codex:
  - propose a plan,
  - implement step-by-step,
  - write tests or checks using the extracted data.

- Windows users: use WSL or follow the latest Codex CLI instructions for Windows.

- Example spreadsheets use **synthetic** data for demonstration only.
- This project is for educational and workflow illustration purposes.
- Always validate outputs and follow your organization’s policies before using similar tooling in production or for official reporting.
