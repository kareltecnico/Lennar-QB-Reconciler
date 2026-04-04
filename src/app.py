import streamlit as st
import pandas as pd
from pathlib import Path
import os
import sys
import signal
import datetime
import sqlite3

# Ensure src modules are discoverable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from reconciler import LennarQBReconciler

# --- Self-Healing Health Check ---
def health_check():
    ROOT_DIR = Path(__file__).parent.parent
    LOG_DIR = ROOT_DIR / "logs"
    DATA_DIR = ROOT_DIR / "data"
    OUT_DIR = ROOT_DIR / "output"
    
    repairs = []
    
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        repairs.append("Created /logs directory.")
        
    log_file = LOG_DIR / "system_health.log"
    
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        repairs.append("Created /data directory.")
        
    if not OUT_DIR.exists():
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        repairs.append("Created /output directory.")
        
    if repairs:
        with open(log_file, "a") as f:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] SYSTEM AUTO-REPAIR:\n")
            for r in repairs:
                f.write(f" - {r}\n")

health_check()

st.set_page_config(page_title="Lennar-QB Reconciler V3.3", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# --- Custom Styling & Enterprise Dark Mode ---
st.markdown("""
<style>
    .kpi-container {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Directory setup
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
OUT_DIR = ROOT_DIR / "output"
LOGO_PATH = OUT_DIR / "logo.png"

# Default File Paths
LENNAR_PATH = DATA_DIR / "lennar check.xlsx"
QB_PATH = DATA_DIR / "to check from qb.xlsx"
DB_PATH = DATA_DIR / "reconciler.db"

# Header & Logo
col1, col2 = st.columns([1, 8])
with col1:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=100, use_column_width=False)
    else:
        st.markdown("<h3 style='color: #4CAF50;'>🏢 BRAND LOGO</h3>", unsafe_allow_html=True)
with col2:
    st.title("Lennar vs QuickBooks Audit Hub")

st.markdown("---")

# Navigation Tabs
tab_audit, tab_db = st.tabs(["📊 Audit Dashboard", "⚙️ Manage Database (Mappings & Foremen)"])

# ====== SIDEBAR ======
with st.sidebar:
    st.header("App Controls")
    
    # Run Button
    run_btn = st.button("🚀 Run Analysis", use_container_width=True, type="primary")
    
    st.markdown("---")
    st.markdown("**File Uploaders** (Overrides existing data in `/data`)")
    
    upload_lennar = st.file_uploader("Upload Lennar File", type=['xlsx'])
    upload_qb = st.file_uploader("Upload QuickBooks File", type=['xlsx'])
    
    if upload_lennar:
        with open(LENNAR_PATH, "wb") as f:
            f.write(upload_lennar.getbuffer())
        st.toast("Lennar file updated 📝")
        
    if upload_qb:
        with open(QB_PATH, "wb") as f:
            f.write(upload_qb.getbuffer())
        st.toast("QuickBooks file updated 📝")
    
    st.markdown("---")
    if st.button("🛑 Shutdown App", use_container_width=True):
        st.warning("Shutting down...")
        os.kill(os.getpid(), signal.SIGTERM)

# ====== TAB 1: AUDIT DASHBOARD ======
with tab_audit:
    if run_btn:
        if LENNAR_PATH.exists() and QB_PATH.exists():
            with st.spinner("Analyzing files and applying Compensated Phase logic..."):
                try:
                    # Inicializar y auditar (Auto initializes SQL table dynamically)
                    rec = LennarQBReconciler(
                        db_path=str(DB_PATH),
                        lennar_path=str(LENNAR_PATH),
                        qb_path=str(QB_PATH),
                        output_dir=str(OUT_DIR)
                    )
                    
                    result = rec.audit()
                    
                    # UI Metrics
                    st.markdown("<div class='kpi-container'>", unsafe_allow_html=True)
                    kpi1, kpi2, kpi3 = st.columns(3)
                    with kpi1:
                        st.metric(label="Total Lennar", value=f"${result['total_lennar']:,.2f}")
                    with kpi2:
                        st.metric(label="Total QuickBooks", value=f"${result['total_qb']:,.2f}")
                    with kpi3:
                        st.metric(label="Exact Net Difference", value=f"${result['total_diff']:,.2f}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # UI Errors and OKs
                    discrepancias = result['discrepancias']
                    dashboard_lines = result['dashboard_lines']
                    
                    if not discrepancias:
                        st.success("¡MATHEMATICALLY BALANCED! No uncompensated differences found.")
                    else:
                        st.subheader("🔴 Required Actions in QuickBooks")
                        for d in discrepancias:
                            with st.container(border=True):
                                st.error(f"**{d['Project']}** (Phase {d['Phase']}) | Foreman: **{d['Foreman']}**")
                                col_a, col_b, col_c = st.columns(3)
                                col_a.metric("Lennar Amount", d['Lennar Amount'])
                                col_b.metric("QB Amount", d['QB Amount'])
                                col_c.write(f"**QB Memo:** {d['QB Memo']}")
                                
                                st.markdown(f"**Discrepancy:** `<span style='color: #ff4b4b; font-size:1.2em;'>{d['Difference']}</span>`", unsafe_allow_html=True)
                                st.warning(f"**🔥 REQUIRED ACTION IN QB:** {d['Action Required']}")
                                
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    with st.expander("✅ Balanced Projects (Compensated internally or Exact Match)"):
                        for line in dashboard_lines:
                            if line.startswith("✅ PROJECT BALANCED:"):
                                name = line.replace("✅ PROJECT BALANCED:", "").strip()
                                st.markdown(f"- **{name}**")
                                
                except Exception as e:
                    st.error(f"Execution Error: {e}")
                    st.info("Ensure the files meet the schema and mappings exist in the SQL Database.")
        else:
            st.error("Missing core Excel files in the `/data` directory. Please upload them on the sidebar.")
    else:
        st.info("Press **Run Analysis** in the sidebar to compile the audit.")

# ====== TAB 2: DATABASE MANAGEMENT ======
with tab_db:
    st.subheader("SQLite Project & Foreman Database")
    st.write("Modify the central nomenclature dictionary directly in SQL. Changes persist indefinitely without Excel files. **Null fields are not permitted.**")
    
    # Ensure DB exists using a dummy initialization
    LennarQBReconciler(str(DB_PATH), "dummy", "dummy", "dummy")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        df_map = pd.read_sql_query('SELECT qb_name AS "QuickBooks Name", lennar_name AS "Lennar Name (Simplified)", foreman AS "Foreman" FROM mappings', conn)
        conn.close()
        
        edited_df = st.data_editor(
            df_map,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="db_editor"
        )
        
        if st.button("Save Database", type="primary"):
            # Check blanks for QB Name and Foreman specifically
            if edited_df['QuickBooks Name'].astype(str).str.strip().eq('').any() or \
               edited_df['Foreman'].astype(str).str.strip().eq('').any() or \
               edited_df.isnull().values.any():
                st.error("Error: All fields are mandatory! ❌")
            else:
                # Write to DB safely
                edited_df = edited_df.rename(columns={
                    "QuickBooks Name": "qb_name",
                    "Lennar Name (Simplified)": "lennar_name",
                    "Foreman": "foreman"
                })
                conn = sqlite3.connect(str(DB_PATH))
                # Full replacing strategy for simplicity
                edited_df.to_sql('mappings', conn, if_exists='replace', index=False)
                # Ensure primary key is preserved by recreating table and inserting
                # To be completely robust, we will replace table manually ensuring schema.
                cursor = conn.cursor()
                cursor.execute('CREATE TABLE IF NOT EXISTS mappings_new (qb_name TEXT PRIMARY KEY, lennar_name TEXT, foreman TEXT)')
                cursor.execute('DELETE FROM mappings_new')
                for _, row in edited_df.iterrows():
                    cursor.execute('INSERT OR IGNORE INTO mappings_new (qb_name, lennar_name, foreman) VALUES (?, ?, ?)',
                                   (str(row['qb_name']).strip(), str(row['lennar_name']).strip(), str(row['foreman']).strip()))
                cursor.execute('DROP TABLE mappings')
                cursor.execute('ALTER TABLE mappings_new RENAME TO mappings')
                conn.commit()
                conn.close()
                st.toast("Database updated successfully! ✅", icon="✅")
                # Also a success box
                st.success("Database updated successfully! ✅")
                
    except Exception as e:
        st.error(f"Error loading SQL Database: {e}")
