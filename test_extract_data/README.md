# Cost Report Extraction with Codex CLI

This example shows how to use OpenAI’s Codex CLI as a local coding agent to automate a real-world data extraction workflow:

- Read multiple cost report spreadsheets from a folder  
- Extract specific tabs (`Input Data` and `Salaries`)  
- Normalize them into a clear data schema  
- Load the data into a SQLite database  
- Export a combined dataset to Excel/CSV  

All spreadsheets in this repo use **synthetic data** that mimics real report layouts — never use sensitive or confidential data directly with AI tools unless you fully understand your security and privacy setup.

---

## Project Structure

The 'extract' folder is the folder where OpenAI's Codex coding agent builds each step of extract, validation, desk review, reporting and visualization steps. 

The folders that end with '..._test' are the folders where we test each step to review the output and verify it's exactly what we need. 

---

