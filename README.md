# Lennar-QB Reconciler v3.0 (Enterprise Suite) 📊

A professional English-language Web Application (Streamlit) designed to act as an auditing engine. It reconciles native **Lennar** payments against internal **QuickBooks** records, detecting accounting discrepancies down to the cent using a smart Phase Compensation algorithm.

## 🛠 Quick Installation

The tool is completely built in pure Python and cross-platform native (Mac/Windows).

1. Open the project folder in your terminal.
2. Initialize and activate your virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   # venv\Scripts\activate   # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Web App Deployment

To boot the graphic interface on your local server, simply execute the startup scripts:

**Direct Terminal Command:**
```bash
streamlit run src/app.py
```

**Automated Launchers:**
- 🖥️ **Mac/Linux:** Type `sh run_app.sh` or double-click the file.
- 🪟 **Windows:** Double-click `run_app.bat`.

The interface will automatically load in your browser at `http://localhost:8501`.

## 🧠 Smart Core & UI Features (V3.0)

### 1. Database Editor (Foreman Management)
You no longer need to edit `Mapeo de Nombres.xlsx` manually. The application features a **Manage Database** tab where you can Add, Edit, and Delete nomenclatures natively.
- **Foreman Assignment:** A strict new 'Foreman' column allows tracking.
- **Data Constraints:** Saving is locked if blank records or `Null` structures are detected, protecting mapping integrity.

### 2. Smart Swap Algorithm
To protect the user from UX misclicks in the file uploaders, the audit engine runs a pre-check script. If it detects the Lennar file was uploaded into the QuickBooks channel (by tracking the `COMMUNITY` column), it **automatically swaps their routing threads** before proceeding, preventing system crashes.

### 3. Phase Compensation Algorithm
When a payment is labeled `Phase C` in Lennar but recorded as `Phase X` in QuickBooks:
1. **Macro Grouping:** Computes the `Net_Diff` of completely aggregated projects.
2. **Conditional Validation:** 
   - If the sum of charges vs. payments is `$0.00`, it assumes the phases are internally balanced and hides it safely under the `Balanced Projects (Compensated)` expander.
   - If a variation is detected, it triggers the **Analytical Phase** bringing up red action cards, revealing exactly which QB Memo is flawed and how much the discrepancy is off by.

## 📈 Roadmap
- **Version 4.0:** Cloud-based sync native integration with QuickBooks Online API.
