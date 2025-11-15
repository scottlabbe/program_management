# Cost Report Extraction with Codex CLI

This example shows how to use OpenAI’s Codex CLI as a local coding agent to automate a real-world data extraction workflow:

- Read multiple cost report spreadsheets from a folder  
- Extract specific tabs (`Input Data` and `Salaries`)  
- Normalize them into a clear data schema  
- Load the data into a SQLite database  
- Export a combined dataset to Excel/CSV  

All spreadsheets in this repo use **synthetic data** that mimics real report layouts — never use sensitive or confidential data directly with AI tools unless you fully understand your security and privacy setup.

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

## Repository Layout

After cloning/downloading the files, your structure should look like:

```text
program_management/
  extract_data/
    test_data/
      Salary_Report_BatonRouge.xlsx
      Salary_Report_Lafayette.xlsx
      Salary_Report_Monroe.xlsx
      Salary_Report_NewOrleans.xlsx
      Salary_Report_Northeast.xlsx
      Salary_Report_Plaquemines.xlsx
```

Each file includes example tabs like:

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

### 3. Provide a clear prompt to Codex

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

Run the instructions provided by Codex.

General insturctions: 
Once Codex has created the extraction script, switch to VScode, in the top menu bar, select 'Terminal -> New Terminal' 
In the new terminal window, run:

```bash
python extract_cost_reports.py
```

(or whatever filename Codex chose)

You should now see outputs such as:

- `cost_reports.db` – SQLite database with combined data.
- `combined_cost_reports.xlsx` – normalized export (use the `--export` flag for `.csv` instead).

---

## Quick Run in VS Code

1. In VS Code select **Terminal → New Terminal** (it opens in the workspace root by default).  
2. Run `cd extract_data` so the interpreter picks up the script and `test_data` folder.  
3. Execute `python extract_cost_reports.py` to generate `cost_reports.db` and `combined_cost_reports.xlsx`.  
4. Optional flags:  
   - `--data-dir <path>` if your spreadsheets are somewhere else.  
   - `--database <path>` to control the SQLite file location.  
   - `--export <path.ext>` where the extension decides between `.xlsx` and `.csv`.  
5. Re-run the command any time input files change; the script rebuilds both the database table and export each run.

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

- Be concrete in your instructions to Codex: files, tabs, schema, outputs.
- Let Codex:
  - propose a plan,
  - implement step-by-step,
  - write tests or checks using the extracted data.

- Windows users: use WSL or follow the latest Codex CLI instructions for Windows.

- Example spreadsheets use **synthetic** data for demonstration only.
- This project is for educational and workflow illustration purposes.
- Always validate outputs and follow your organization’s policies before using similar tooling in production or for official reporting.
