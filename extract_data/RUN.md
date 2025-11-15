# Running the Cost Report Extractor in VS Code

1. **Open the workspace**  
   - Start VS Code and choose **File → Open Folder…**.  
   - Select the `program_management` folder (it contains `extract_data`).

2. **Start an integrated terminal**  
   - In VS Code pick **Terminal → New Terminal**.  
   - Run `cd extract_data` so the prompt sits next to the scripts and data.

3. **Execute the extractor**  
   ```bash
   python extract_cost_reports.py
   ```  
   This reads every workbook under `test_data/`, rebuilds `cost_reports.db`, and writes `combined_cost_reports.csv` (salaries) plus `contact_info.csv`.

4. **Optional arguments**  
   - `--data-dir <path>`: point to a different folder of spreadsheets.  
   - `--database <path>`: choose where the SQLite file is stored.  
   - `--export <path>`: export salary data to `.csv` or `.xlsx`.  
   - `--contact-export <path>`: same for the contact list.

5. **Review the outputs**  
   - Open `combined_cost_reports.csv` in VS Code or Excel for a quick spot-check.  
   - Use a SQLite viewer/extension to inspect `cost_reports.db` if deeper queries are needed.
