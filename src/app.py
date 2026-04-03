import streamlit as st
import pandas as pd
from pathlib import Path
import os
import sys

# Ensure src modules are discoverable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from reconciler import LennarQBReconciler

st.set_page_config(page_title="Lennar-QB Reconciler", page_icon="📊", layout="wide")

# Directory setup
DATA_DIR = Path("data")
OUT_DIR = Path("output")
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Default File Paths
LENNAR_PATH = DATA_DIR / "lennar check.xlsx"
QB_PATH = DATA_DIR / "to check from qb.xlsx"
MAPPING_PATH = DATA_DIR / "Mapeo de Nombres.xlsx"

# Header & Logo
col1, col2 = st.columns([1, 8])
with col1:
    if Path("output/logo.png").exists():
        st.image("output/logo.png", width=80)
with col2:
    st.title("Lennar vs QuickBooks Audit Web App")

st.markdown("---")

# Sidebar Uploaders (Modo Manual)
with st.sidebar:
    st.header("Modo Manual (Uploaders)")
    st.markdown("Si subes un archivo aquí, sobrescribirá temporal o permanentemente los datos en `/data`.")
    
    upload_lennar = st.file_uploader("Subir Archivo Lennar", type=['xlsx'])
    upload_qb = st.file_uploader("Subir Archivo QuickBooks", type=['xlsx'])
    upload_mapping = st.file_uploader("Subir Archivo Mapping", type=['xlsx'])

    # Sobrescritura de archivos
    if upload_lennar:
        with open(LENNAR_PATH, "wb") as f:
            f.write(upload_lennar.getbuffer())
        st.success("Lennar actualizado.")
        
    if upload_qb:
        with open(QB_PATH, "wb") as f:
            f.write(upload_qb.getbuffer())
        st.success("QuickBooks actualizado.")
        
    if upload_mapping:
        with open(MAPPING_PATH, "wb") as f:
            f.write(upload_mapping.getbuffer())
        st.success("Mapping actualizado.")

# Modo Automático (Ejecución)
if LENNAR_PATH.exists() and QB_PATH.exists() and MAPPING_PATH.exists():
    try:
        # Inicializar y auditar
        rec = LennarQBReconciler(
            mapping_path=str(MAPPING_PATH),
            lennar_path=str(LENNAR_PATH),
            qb_path=str(QB_PATH),
            output_dir=str(OUT_DIR)
        )
        
        result = rec.audit()
        
        # UI Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Lennar", value=f"${result['total_lennar']:,.2f}")
        with col2:
            st.metric(label="Total QuickBooks", value=f"${result['total_qb']:,.2f}")
        with col3:
            st.metric(label="Diferencia Neta Exacta", value=f"${result['total_diff']:,.2f}", delta=None)
            
        st.markdown("---")
        
        # UI Errors and OKs
        discrepancias = result['discrepancias']
        dashboard_lines = result['dashboard_lines']
        
        if not discrepancias:
            st.success("¡PERFECCIÓN MATEMÁTICA! No se encontraron diferencias sin compensar.")
        else:
            st.subheader("🔴 Acciones Requeridas en QuickBooks (Faltantes/Sobrantes Netos)")
            for d in discrepancias:
                with st.error(f"**Error en {d['Proyecto']}** (Fase {d['Fase']})"):
                    st.write(f"**Diferencia de:** `<span style='color: white; font-weight: bold; font-size: 1.2rem;'>{d['Diferencia']}</span>`", unsafe_allow_html=True)
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Monto Lennar", d['Monto Lennar'])
                    col_b.metric("Monto QB", d['Monto QB'])
                    col_c.write(f"**Memo en QB:** {d['Memo QB']}")
                    
                    st.warning(f"**🔥 ACCIÓN EXACTA EN QB:** {d['Acción Correctiva']}")
                    
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.expander("✅ Proyectos Compensados / OK"):
            for line in dashboard_lines:
                if line.startswith("✅ PROYECTO OK:"):
                    name = line.replace("✅ PROYECTO OK:", "").strip()
                    st.markdown(f"- **{name}**")
                    
    except Exception as e:
        st.error(f"Error procesando la información: {e}")
        st.exception(e)

else:
    st.info("👋 **Bienvenido.** Sube los 3 archivos Excel obligatorios en el panel de la izquierda para comenzar la auditoría o asegúrate de que existan en la carpeta `/data`.")
