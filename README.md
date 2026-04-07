# 📊 Lennar-QB Reconciler v4.1 (Master Suite)
## Leza's Plumbing - Financial Audit & Precision Tool

This application is a professional-grade auditing engine designed for **Leza's Plumbing**. Its primary purpose is to reconcile payment data from **Lennar** (the client) against internal accounting records from **QuickBooks**, identifying discrepancies, tracking backcharges, and ensuring every cent is accounted for across complex project phases.

---

## 🏗️ System Architecture

The project is built on a modern Python stack optimized for data precision and ease of use:
- **Frontend:** [Streamlit](https://streamlit.io/) (Web-based UI with enterprise dark mode).
- **Engine:** [Pandas](https://pandas.pydata.org/) (High-performance data manipulation).
- **Storage:** [SQLite](https://sqlite.org/) (Local relational database for project mapping and foreman management).
- **Automation:** Self-healing health checks and automated file routing.

---

## 🧠 Core Logic Modules

The Reconciler employs several sophisticated algorithms to handle "dirty" real-world data:

### 1. 🔍 Header Hunter (V4.0)
Excel exports often contain blank rows, summary titles, or varying start positions.
- **Logic:** The engine scans the first 10 rows of any uploaded file.
- **Action:** It identifies the row where required columns (e.g., 'Community', 'Amount', 'Type') actually reside and reloads the data using that row as the header.

### 2. 🛡️ Aggressive Substring Mapping (V4.1)
Names rarely match perfectly between systems (e.g., `WILTON MANORS` vs `WILTON MANORS (ALTESSA TH)`).
- **Tier 1:** Exact key match.
- **Tier 2:** Key-as-substring (Is "WILTON MANORS" inside the QB name?).
- **Tier 3:** Value-as-substring (Is "ALTESSA TH" inside the Lennar project name?).
- **Priority:** Sorted by "Longest-Match-First" to ensure the most specific mapping wins.

### 3. ⚠️ Backcharge Automation (V4.1)
Negative values in Lennar exports are treated as "Backcharges" (deductions).
- **Segmentation:** The engine splits data into `Positive Payments` (Audit) and `Negative Backcharges`.
- **Tracking:** Backcharges are linked to their specific Projects and Foremen, and displayed with their original "ACTIVITY" descriptions (e.g., "ROUGH PLUMBING CREDIT") in the dashboard.

### 4. ⚖️ Phase Compensation Algorithm
Handles cases where phases are categorized differently (e.g., Phase C in Lennar vs Phase X in QB).
- **Balanced Projects:** If a project's total payment matches the total billed across all phases, it is marked as "Mathematically Balanced" and moved to a separate section.
- **Required Actions:** Only uncompensated discrepancies trigger the red "Action Required" cards.

---

## 📂 Project Structure

```bash
/
├── data/               # Persistent storage (.db, .xlsx fallbacks)
├── output/             # Exported audit CSVs and session assets
├── logs/               # System health logs
├── src/
│   ├── app.py          # Main Streamlit UI and Tab Logic
│   └── reconciler.py   # Core Audit Engine (The "Brain")
├── run_app.bat         # One-click Windows launcher
└── requirements.txt    # Dependency manifest
```

---

## 🚀 Installation & Usage

### 1. Requirements
Ensure you have **Python 3.10+** installed.

### 2. Setup
```bash
# Initialize Environment
python -m venv venv
venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 3. Running the App
Execute `run_app.bat` or run:
```bash
streamlit run src/app.py
```

### 4. Workflow
1.  **Sidebar:** Upload the Lennar file and the QuickBooks file.
2.  **Mapping (Optional):** Go to the **Manage Database** tab to link QB names to Lennar names and assign a Foreman.
3.  **Run:** Click `🚀 Run Analysis`.
4.  **Review:** Examine the 4 KPI metrics (including the red Backcharge indicator) and the Action Cards.
5.  **Export:** Audit logs are saved automatically in the `/output` folder.

---

## ⚙️ Data Schemas

### Lennar File Requirements
Must contain at least 1 of the following in the first 10 rows:
- `COMMUNITY` (Project Name)
- `AMOUNT PAID` (Numeric, handles commas)
- `ACTIVITY` (For phase detection and backcharge descriptions)

### QuickBooks File Requirements
Must contain at least 1 of the following in the first 10 rows:
- `Name` (Must follow `Client:Project:Phase` or `Client:Project` format)
- `Type`
- `Amount` (Numeric, handles commas)

---

## 🛠️ Database Management
The **Manage Database** tab allows direct edit of the `reconciler.db`.
- **Primary Key:** QuickBooks Name.
- **Validation:** All fields (QB Name, Lennar Name, Foreman) are mandatory. Use the **💾 Save Database** button to persist changes.
- **Persistence Verification:** The application prints a row-count verification to the terminal on every save to ensure the physical write was successful.
