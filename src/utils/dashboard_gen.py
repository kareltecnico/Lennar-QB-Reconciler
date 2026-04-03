import datetime
from pathlib import Path

def generate_html_dashboard(out_path, total_lennar, total_qb, total_diff, dashboard_lines, discrepancias):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lennar-QB Reconciler Dashboard</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #121212; color: #f8f9fa; }}
        .kpi-card {{ background-color: #1e1e1e; border: none; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .kpi-title {{ font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; color: #adb5bd; }}
        .kpi-value {{ font-size: 2rem; font-weight: bold; }}
        .text-green {{ color: #20c997; }}
        .text-blue {{ color: #0d6efd; }}
        .text-red {{ color: #dc3545; }}
        .card-header {{ background-color: #2c2c2c; border-bottom: 1px solid #444; font-weight: bold; }}
        .table-dark {{ background-color: #1e1e1e; }}
        .project-ok {{ border-left: 5px solid #20c997; padding-left: 10px; margin-bottom: 10px; background-color: #1e1e1e; padding: 10px; border-radius: 5px; }}
        .project-error {{ border-left: 5px solid #dc3545; padding-left: 10px; margin-bottom: 15px; background-color: #1e1e1e; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
<div class="container py-5">
    <h1 class="mb-4 text-center">📊 Lennar vs QuickBooks <span class="text-blue">Audit Dashboard</span></h1>
    <p class="text-center text-muted mb-5">Generado el: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <!-- KPIs -->
    <div class="row mb-5 text-center">
        <div class="col-md-4">
            <div class="card kpi-card p-4">
                <div class="kpi-title">Total Lennar</div>
                <div class="kpi-value text-blue">${total_lennar:,.2f}</div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card kpi-card p-4">
                <div class="kpi-title">Total QuickBooks</div>
                <div class="kpi-value text-blue">${total_qb:,.2f}</div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card kpi-card p-4">
                <div class="kpi-title">Diferencia Neta</div>
                <div class="kpi-value text-green">${total_diff:,.2f}</div>
            </div>
        </div>
    </div>

    <!-- Alert Section -->
    <div class="row">
        <div class="col-12">
            <h3 class="mb-3">🔴 Acciones Requeridas en QuickBooks</h3>
"""
    
    # Renderizar Errores Reales
    error_found = False
    for line in dashboard_lines:
        if line.startswith("🔴 ERROR DETECTADO:"):
            # Extract basic info
            parts = line.replace("🔴 ERROR DETECTADO: ", "").split("|")
            proj_name = parts[0].strip()
            diff_total = parts[1].strip()
            
            html += f"""
            <div class="project-error">
                <h5 class="text-red mb-1">{proj_name}</h5>
                <p class="mb-2 text-muted">{diff_total}</p>
                <ul class="mb-0">
            """
            error_found = True
        elif line.startswith("    - Fase"):
            html += f"<li>{line.strip().replace('- Fase', '<strong>Fase</strong>')}</li>"
            
    if not error_found:
        html += """<div class="alert alert-success bg-dark text-success border-success">¡Matemáticamente perfecto! No hay diferencias sin compensar.</div>"""
        
    html += """
                </ul>
            </div>
        </div>
    </div>

    <!-- OK Section -->
    <div class="row mt-5">
        <div class="col-12">
            <h3 class="mb-3">✅ Proyectos Compensados / OK</h3>
    """
    for line in dashboard_lines:
        if line.startswith("✅ PROYECTO OK:"):
            name = line.replace("✅ PROYECTO OK:", "").strip()
            html += f"""<div class="project-ok">{name}</div>\n"""

    html += """
        </div>
    </div>
</div>

<!-- Bootstrap JS Bundle -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    Path(out_path).write_text(html, encoding='utf-8')
    print(f"\n[✓] PRO Dashboard HTML exportado en: {out_path}")
