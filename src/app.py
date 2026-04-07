import streamlit as st
import pandas as pd
from pathlib import Path
import os
import sys
import signal
import datetime
import sqlite3
import time
import glob

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

st.set_page_config(page_title="Payment Reconciliation Tool v3.7", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

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
    /* Logo Fix & Circular Mask */
    [data-testid="stImageCanvas"] img, [data-testid="stImage"] img {
        background-color: transparent !important;
        border-radius: 50% !important;
        overflow: hidden !important;
        border: none !important;
        padding: 0 !important;
    }
    [data-testid="stImage"] {
        border-radius: 50% !important;
        overflow: hidden !important;
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
col1, col2 = st.columns([1, 4])
with col1:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=100)
    else:
        st.markdown("<h3 style='color: #4CAF50;'>🏢 BRAND LOGO</h3>", unsafe_allow_html=True)
with col2:
    st.title("Payment Reconciliation Tool")
    st.markdown("<h2 style='font-size: 1.8rem; font-weight: 800; color: #4CAF50;'>Leza's Plumbing - Financial Audit & Precision Tool</h2>", unsafe_allow_html=True)

st.markdown("---")

# Navigation Tabs
tab_audit, tab_db = st.tabs(["📊 Audit Dashboard", "⚙️ Manage Database"])

# ====== SIDEBAR ======
with st.sidebar:
    st.markdown("<h1 style='font-size: 2.2rem; font-weight: bold;'>Control Panel</h1>", unsafe_allow_html=True)
    
    st.markdown("**File Uploaders** (Overrides existing data in `/data`)")
    upload_lennar = st.file_uploader("Upload Lennar File", type=['xlsx'])
    upload_qb = st.file_uploader("Upload Quickbook File", type=['xlsx'])
    
    # Smart Toasts/Messages Place Holder
    status_msg = st.empty()
    
    if upload_lennar:
        with open(LENNAR_PATH, "wb") as f:
            f.write(upload_lennar.getbuffer())
        status_msg.success("Lennar file updated 📝")
        
    if upload_qb:
        with open(QB_PATH, "wb") as f:
            f.write(upload_qb.getbuffer())
        status_msg.success("Quickbook file updated 📝")
        
    # Run Button Layout
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Run Analysis", width="stretch", type="primary")
    st.markdown("---")

    # Spacer pushing Shutdown down
    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)
    if st.button("🛑 Shutdown App", width="stretch", type="secondary"):
        status_msg.success("Server Closed. You can now close this tab.")
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)

# ====== TAB 1: AUDIT DASHBOARD ======
with tab_audit:
    # Use a single empty slot for the status banner — avoids the black-bar artifact
    status_hub = st.empty()
    ui_msgs    = st.empty()

    if not run_btn:
        status_hub.info("Waiting for analysis... 🔍")

    if run_btn:
        status_msg.empty()          # Clear sidebar upload notifications
        status_hub.empty()          # Collapse the blue info box immediately — no black bar
        
        if LENNAR_PATH.exists() and QB_PATH.exists():
            
            # OUTPUT PURGE LOGIC
            for f in glob.glob(str(OUT_DIR / "*")):
                if "logo.png" not in Path(f).name:
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            with st.spinner("Analyzing files and applying Compensated Phase logic..."):
                try:
                    # Inicializar y auditar
                    rec = LennarQBReconciler(
                        db_path=str(DB_PATH),
                        lennar_path=str(LENNAR_PATH),
                        qb_path=str(QB_PATH),
                        output_dir=str(OUT_DIR)
                    )
                    
                    result = rec.audit()
                    # SUCCESS — only set after audit() returns without exceptions
                    status_hub.success("Analysis completed successfully! ✅")
                    
                    # UI Metrics — 4 KPI columns
                    bc_total   = result.get('total_lennar_bc', 0.0)
                    bc_detail  = result.get('backcharges_detail', {})
                    has_bc     = bc_total != 0.0

                    st.markdown("<div class='kpi-container'>", unsafe_allow_html=True)
                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    with kpi1:
                        st.metric(
                            label="Total Lennar (No BC)",
                            value=f"${result['total_lennar']:,.2f}"
                        )
                    with kpi2:
                        st.metric(
                            label="Total Quickbook",
                            value=f"${result['total_qb']:,.2f}"
                        )
                    with kpi3:
                        st.metric(
                            label="Net Difference",
                            value=f"${result['total_diff']:,.2f}"
                        )
                    with kpi4:
                        # Show backcharge total in red via delta hack
                        bc_value = abs(bc_total) if has_bc else 0.0
                        bc_label = f"-${bc_value:,.2f}" if has_bc else "$0.00"
                        st.metric(
                            label="Total Backcharges ⚠️" if has_bc else "Total Backcharges",
                            value=bc_label,
                            delta=f"{len(bc_detail)} project(s) affected" if has_bc else None,
                            delta_color="inverse"
                        )
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # UI Errors and OKs
                    discrepancias   = result['discrepancias']
                    dashboard_lines = result['dashboard_lines']
                    bc_detail       = result.get('backcharges_detail', {})

                    if not discrepancias:
                        ui_msgs.success("¡MATHEMATICALLY BALANCED! No uncompensated differences found.")
                    else:
                        st.subheader("🔴 Required Actions in Quickbook")
                        for d in discrepancias:
                            proj_key = d['Project']   # already normalized / uppercased
                            with st.container(border=True):
                                st.markdown(f"### **{d['Project']}** (Phase {d['Phase']}) | Foreman: **{d['Foreman']}**")

                                # ROW 1: Clean financial metrics
                                col_a, col_b, col_c = st.columns(3)
                                col_a.metric("Lennar Amount",    d['Lennar Amount'])
                                col_b.metric("Quickbook Amount", d['Quickbook Amount'])
                                col_c.metric("Difference",       d['Difference'])

                                # ROW 2: Required action instruction
                                st.warning(f"**🔥 REQUIRED ACTION IN QUICKBOOK:** {d['Action Required']}")

                                # ROW 3: Backcharge alerts for this project (if any)
                                proj_bcs = bc_detail.get(proj_key, [])
                                if proj_bcs:
                                    for bc in proj_bcs:
                                        bc_amt  = bc['amount']     # negative float
                                        bc_act  = bc['activity']
                                        st.info(
                                            f"⚠️ **Backcharge Detected** &nbsp;|&nbsp; "
                                            f"Activity: **{bc_act}** &nbsp;|&nbsp; "
                                            f"Amount: **-${abs(bc_amt):,.2f}**",
                                            icon="🟡"
                                        )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # ── EXPANDER 1: Balanced Projects (clean list) ────────────────
                    with st.expander("✅ Balanced Projects"):
                        for line in dashboard_lines:
                            if line.startswith("✅ PROJECT BALANCED:"):
                                # Render the full line, swapping the prefix for a cleaner label
                                display = line.replace("✅ PROJECT BALANCED:", "✅").strip()
                                st.markdown(f"- {display}")

                    # ── EXPANDER 2: Backcharge Details (orange pills) ─────────────
                    # Only show if there is at least one backcharge in this audit run
                    if bc_detail:
                        with st.expander("⚠️ Backcharge Details"):
                            # Helper: extract canonical project key from a dashboard line
                            def _extract_proj_key(line: str) -> str:
                                raw = line.replace("✅ PROJECT BALANCED:", "").strip()
                                # Split on " 💯", " (", or ". Foreman:" — whichever comes first
                                for sep in [" 💯", " (", ". Foreman:"]:
                                    if sep in raw:
                                        return raw.split(sep)[0].strip().upper()
                                return raw.upper()

                            # Iterate dashboard lines to preserve project ordering
                            rendered_projects = set()
                            for line in dashboard_lines:
                                if not line.startswith("✅ PROJECT BALANCED:"):
                                    continue
                                proj_key = _extract_proj_key(line)
                                if proj_key in rendered_projects:
                                    continue   # avoid duplicates
                                proj_bcs = bc_detail.get(proj_key, [])
                                if not proj_bcs:
                                    continue
                                rendered_projects.add(proj_key)
                                for bc in proj_bcs:
                                    bc_amt = bc['amount']        # negative float
                                    bc_act = bc['activity'] or 'N/A'
                                    st.markdown(
                                        f"<div style='"
                                        f"margin-bottom:0.4rem;"
                                        f"padding:0.45rem 0.85rem;"
                                        f"border-left:4px solid #FF8C00;"
                                        f"border-radius:4px;"
                                        f"background:rgba(255,140,0,0.09);"
                                        f"font-size:0.875rem;"
                                        f"'>"
                                        f"🟠 <b>Backcharge Detected</b> &nbsp;|&nbsp; "
                                        f"Project: <b>{proj_key}</b> &nbsp;|&nbsp; "
                                        f"Activity: <b>{bc_act}</b> &nbsp;|&nbsp; "
                                        f"Amount: <code>-${abs(bc_amt):,.2f}</code>"
                                        f"</div>",
                                        unsafe_allow_html=True
                                    )

                except Exception as e:
                    ui_msgs.error(f"Execution Error: {e}")
                    st.info("Ensure the files meet the schema and mappings exist in the SQL Database.")
        else:
            ui_msgs.error("Missing core Excel files in the `/data` directory. Please upload them on the sidebar.")

# ====== TAB 2: DATABASE MANAGEMENT ======
with tab_db:
    st.subheader("SQLite Project & Foreman Database")
    st.write("Modify the central nomenclature dictionary directly in SQL. Changes persist indefinitely. **Null fields are not permitted.**")
    
    db_msgs = st.empty()
    
    # Ensure DB exists using a dummy initialization
    LennarQBReconciler(str(DB_PATH), "dummy", "dummy", "dummy")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        df_map = pd.read_sql_query('SELECT qb_name AS "Quickbook Name", lennar_name AS "Lennar Name (Simplified)", foreman AS "Foreman" FROM mappings', conn)
        conn.close()
        
        edited_df = st.data_editor(
            df_map,
            num_rows="dynamic",
            width="stretch",
            hide_index=True,
            key="db_editor"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            save_clicked = st.button("💾 Save Database", type="primary")
            
        if save_clicked:
            # Reconstruct the final DataFrame from session_state for reliable capture
            # st.data_editor returns the live edited version, but reading directly
            # from session_state delta ensures all edits (rows added/deleted/changed) are included.
            editor_state = st.session_state.get("db_editor", None)
            if editor_state is not None:
                working_df = df_map.copy()
                # Apply deletions
                deleted_rows = editor_state.get("deleted_rows", [])
                if deleted_rows:
                    working_df = working_df.drop(index=deleted_rows).reset_index(drop=True)
                # Apply edits
                edited_rows = editor_state.get("edited_rows", {})
                for idx_str, changes in edited_rows.items():
                    idx = int(idx_str)
                    if idx < len(working_df):
                        for col_name, val in changes.items():
                            working_df.at[idx, col_name] = val
                # Apply added rows
                added_rows = editor_state.get("added_rows", [])
                if added_rows:
                    new_rows_df = pd.DataFrame(added_rows)
                    working_df = pd.concat([working_df, new_rows_df], ignore_index=True)
                edited_df = working_df
            # else: fall back to the widget's direct return value (already set above)
            
            has_errors = False
            for index, row in edited_df.iterrows():
                if pd.isna(row['Quickbook Name']) or str(row['Quickbook Name']).strip() == "":
                    has_errors = True
                if pd.isna(row['Foreman']) or str(row['Foreman']).strip() == "":
                    has_errors = True
            
            if has_errors:
                db_msgs.error("Error: All fields are mandatory! ❌")
            else:
                conn = sqlite3.connect(str(DB_PATH))
                cursor = conn.cursor()
                try:
                    cursor.execute('DELETE FROM mappings')
                    for _, row in edited_df.iterrows():
                        q_val = str(row['Quickbook Name']).strip()
                        l_val = str(row['Lennar Name (Simplified)']).strip() if pd.notna(row['Lennar Name (Simplified)']) else ""
                        f_val = str(row['Foreman']).strip()
                        cursor.execute('INSERT INTO mappings (qb_name, lennar_name, foreman) VALUES (?, ?, ?)', (q_val, l_val, f_val))
                    
                    # --- PERSISTENCE VERIFICATION: print row count to terminal before commit ---
                    cursor.execute('SELECT COUNT(*) FROM mappings')
                    pending_count = cursor.fetchone()[0]
                    print(f"[DB SAVE] About to commit {pending_count} row(s) to mappings table in {DB_PATH}")
                    
                    conn.commit()
                    
                    # Post-commit verification
                    cursor.execute('SELECT COUNT(*) FROM mappings')
                    committed_count = cursor.fetchone()[0]
                    print(f"[DB SAVE] Commit verified: {committed_count} row(s) now in mappings table.")
                    
                    cursor.execute("SELECT COUNT(*) FROM mappings WHERE foreman IS NULL OR foreman = ''")
                    invalid_count = cursor.fetchone()[0]
                    
                    if invalid_count == 0:
                        db_msgs.success("Database successfully updated! ✅")
                    else:
                        db_msgs.error("Validation failed! Corrupt records detected in DB. ❌")
                        
                except Exception as db_err:
                    conn.rollback()
                    db_msgs.error(f"Failed to save Database: {db_err}")
                finally:
                    conn.close()
                    
    except Exception as e:
        db_msgs.error(f"Error loading SQL Database: {e}")
