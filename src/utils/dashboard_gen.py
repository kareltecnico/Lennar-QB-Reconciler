import datetime
from pathlib import Path

def generate_html_dashboard(out_path, total_lennar, total_qb, total_diff, dashboard_lines, discrepancias):
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lennar-QB Reconciler Dashboard</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #121212; color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .kpi-card {{ background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .kpi-title {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.5px; color: #adb5bd; font-weight: 600; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 2.2rem; font-weight: 700; }}
        .text-green {{ color: #20c997; }}
        .text-blue {{ color: #0d6efd; }}
        .text-red {{ color: #dc3545; }}
        .uppercase {{ text-transform: uppercase; letter-spacing: 1px; font-weight: 500; font-size: 0.75rem; }}
        .project-ok {{ border-left: 4px solid #20c997; margin-bottom: 12px; background-color: #1e1e1e; padding: 12px 18px; border-radius: 6px; font-weight: 500; font-size: 1.05rem; display: flex; align-items: center; justify-content: space-between; border-right: 1px solid #333; border-top: 1px solid #333; border-bottom: 1px solid #333; }}
        .project-error-card {{ border-left: 5px solid #dc3545; background-color: #171717; border-radius: 10px; box-shadow: 0 6px 14px rgba(0,0,0,0.4); margin-bottom: 1.8rem; border-right: 1px solid #333; border-top: 1px solid #333; border-bottom: 1px solid #333; overflow: hidden; }}
        .project-error-header {{ background-color: #1f1414; padding: 18px 25px; border-bottom: 1px solid #3a1c1d; }}
        .project-error-body {{ padding: 25px; }}
        .logo-img {{ height: 60px; object-fit: contain; filter: drop-shadow(0 0 8px rgba(255,255,255,0.1)); }}
        .header-container {{ display: flex; align-items: center; justify-content: center; gap: 24px; margin-bottom: 1rem; }}
        .action-alert {{ background-color: rgba(220,53,69,0.08); border: 1px solid rgba(220,53,69,0.3); border-radius: 8px; padding: 15px; font-size: 1.05rem; }}
    </style>
</head>
<body>
<div class="container py-5">
    <div class="header-container">
        <img src="logo.png" alt="Company Logo" class="logo-img">
        <h1 class="mb-0 fw-bold">📊 Lennar <span class="text-muted fw-normal mx-2">vs</span> QuickBooks <span class="text-blue">Audit</span></h1>
    </div>
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
            <div class="card kpi-card p-4" style="border-bottom: 4px solid #20c997;">
                <div class="kpi-title">Dif. Neta Auditada</div>
                <div class="kpi-value text-green">${total_diff:,.2f}</div>
            </div>
        </div>
    </div>

    <!-- Alert Section -->
    <div class="row">
        <div class="col-12">
            <h3 class="mb-4 fw-bold">🔴 Acciones Requeridas en QuickBooks</h3>
"""

    if len(discrepancias) == 0:
        html += """<div class="alert alert-success bg-dark text-success border-success fw-bold p-4 text-center fs-5">¡Perfección Matemática! No hay diferencias sin compensar.</div>\n"""
    else:
        for d in discrepancias:
            html += f"""
            <div class="card project-error-card">
                <div class="project-error-header d-flex justify-content-between align-items-center">
                    <h5 class="text-danger mb-0 fw-bold fs-4">{d['Proyecto']}</h5>
                    <span class="badge bg-danger rounded-pill fs-6 px-3 py-2">Fase {d['Fase']}</span>
                </div>
                <div class="project-error-body">
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <span class="text-muted d-block uppercase">Memo Asociado en QB</span>
                            <span class="fs-5 fw-bold font-monospace text-light">{d['Memo QB']}</span>
                        </div>
                        <div class="col-md-3">
                            <span class="text-muted d-block uppercase">Monto Lennar</span>
                            <span class="fs-5">{d['Monto Lennar']}</span>
                        </div>
                        <div class="col-md-3">
                            <span class="text-muted d-block uppercase">Monto QB</span>
                            <span class="fs-5">{d['Monto QB']}</span>
                        </div>
                        <div class="col-md-3">
                            <span class="text-muted d-block uppercase mb-1">Diferencia Neta</span>
                            <span class="fs-4 text-danger fw-bold">{d['Diferencia']}</span>
                        </div>
                    </div>
                    <div class="action-alert d-flex align-items-center">
                        <span class="fs-3 me-3">⚡</span> 
                        <div>
                            <div class="uppercase text-danger mb-1" style="font-size: 0.8rem;">Acción Exacta Requerida</div>
                            <strong class="text-light">{d['Acción Correctiva']}</strong>
                        </div>
                    </div>
                </div>
            </div>
            """

    html += """
        </div>
    </div>

    <!-- OK Section -->
    <div class="row mt-5">
        <div class="col-12">
            <h3 class="mb-4 fw-bold">✅ Proyectos Compensados / OK</h3>
            <div class="row">
    """
    
    ok_count = 0
    for line in dashboard_lines:
        if line.startswith("✅ PROYECTO OK:"):
            name = line.replace("✅ PROYECTO OK:", "").replace("(Diferencias internas en fases compensadas).", "").strip()
            html += f"""
                <div class="col-md-6 mb-1">
                    <div class="project-ok">
                        <span>{name}</span>
                        <span class="badge bg-success text-dark">Compensado/OK</span>
                    </div>
                </div>
            """
            ok_count += 1
            
    if ok_count == 0:
        html += """<div class="col-12"><p class="text-muted fst-italic">No se detectaron proyectos 100% compensados.</p></div>"""
        
    html += """
            </div>
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
