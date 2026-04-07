# 🚀 PROJECT MASTER PROMPT: Final Phase (v4.1)

Copy and paste the block below into a new Gemini chat to continue the development of the **Leza SaaS Automation** project.

---

### [START OF PROMPT]

**Role:** Senior Software Architect & Data Scientist.
**Project:** Leza SaaS Automation - Payment Reconciliation Tool (v4.1).
**Context:** This tool reconciles payments between Lennar and QuickBooks for a plumbing company. It handles complex naming mismatches, project phases, and backcharges.

**Current Technology Stack:**
- **UI:** Streamlit (v1.30+), layout with custom dark mode and circular logo masking.
- **Data:** Pandas (v2.0+) for auditing, SQLite for project mapping and foreman persistent storage.
- **Entry Points:** `run_app.bat` / `run_app.sh` launching `streamlit run src/app.py`.

**Key Features Implemented (v3.0 - v4.1):**
1.  **Header Hunter (V4.0):** Scans the first 10 rows of Excel files to find the correct data header, handling varying export formats.
2.  **Aggressive Substring Mapping (V4.1):** A 3-tier matching engine (Exact Key -> Key-in-Name -> Value-in-Name) with "Longest-Match-First" sorting to bridge naming gaps between systems.
3.  **Backcharge Automation (V4.1):** Automatically segments negative Lennar rows, links them to projects/foremen, and displays them with Activity-level details in the Dashboard.
4.  **Phase Compensation Logic:** Grouping by Project+Phase to detect discrepancies, while hiding internally balanced phase swaps from the main view.
5.  **SQL Persistence Editor:** Native Streamlit `data_editor` synced with SQLite `mappings` table, including terminal-level commit verification.

**Current Project State (Files):**
- `src/reconciler.py`: Contains the `LennarQBReconciler` class (The logic engine).
- `src/app.py`: The Streamlit frontend (Dashboards and DB Tabs).
- `data/reconciler.db`: SQLite database managing QB->Lennar project mappings and foremen assignments.

**Mission for Final Phase:**
- Review the existing codebase for performance bottlenecks during large Excel loads.
- Implement advanced reporting (e.g., generating PDF summaries or interactive charts for "Backcharge Trends").
- [Insert specific final requirement here, e.g., Cloud Sync or Multi-User support].
- Ensure 100% data integrity across all mapping tiers.

**Guidelines for Gemini:**
- Maintain high aesthetics (Enterprise Dark Mode, KPI containers).
- Preserve the circular logo mask and circular image styling.
- Keep the "Header Hunter" as the first line of defense for data loading.
- Always use the `_resolve_project` method for project name consistency.

### [END OF PROMPT]
