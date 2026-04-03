import pandas as pd
from pathlib import Path
import sys

class LennarQBReconciler:
    def __init__(self, mapping_path, lennar_path, qb_path, output_dir):
        self.mapping_path = Path(mapping_path)
        self.lennar_path = Path(lennar_path)
        self.qb_path = Path(qb_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_data(self):
        self.mapping_df = pd.read_excel(self.mapping_path)
        self.mapping_dict = dict(zip(
            self.mapping_df['Nombre en QuickBooks'].str.strip().str.upper(), 
            self.mapping_df['Nombre en Lennar (Simplificado)'].str.strip().str.upper()
        ))
        
        # Lennar
        self.lennar_df = pd.read_excel(self.lennar_path)
        self.lennar_df.columns = [str(c).strip().replace('\n', ' ').upper() for c in self.lennar_df.columns]
        self.lennar_df = self.lennar_df.dropna(subset=['COMMUNITY'])  # Remove grand totals row
        
        self.lennar_df['AMOUNT PAID'] = pd.to_numeric(self.lennar_df['AMOUNT PAID'], errors='coerce').fillna(0)
        self.lennar_df = self.lennar_df[self.lennar_df['AMOUNT PAID'] > 0]
        self.lennar_df['COMMUNITY_RAW'] = self.lennar_df['COMMUNITY'].astype(str).str.strip().str.upper()
        
        # Phase Mapping para Lennar
        def get_lennar_phase(activity):
            activity = str(activity).upper()
            if 'ROUGH' in activity: return 'A'
            if 'TOP OUT' in activity: return 'B'
            if 'FINAL' in activity: return 'C'
            if 'WARRANTY' in activity or 'THEFT' in activity: return 'X'
            return 'UNKNOWN'
        
        self.lennar_df['ACTIVITY'] = self.lennar_df['ACTIVITY'].fillna('')
        self.lennar_df['Phase'] = self.lennar_df['ACTIVITY'].apply(get_lennar_phase)
        
        # Normalize Project Name para Lennar
        def clean_lennar_community(name):
            if 'VIVANT' in name:
                if '2510460' in name: return 'VIVANT 2510460'
                if '2510660' in name: return 'VIVANT - 2510660'
            if 'REDLAND' in name: return 'REDLAND RIDGE REDWOOD / REDLAND RIDGE SF'
            
            for mapped in set(self.mapping_dict.values()):
                if str(mapped) in name:
                    return str(mapped)
            return name
            
        self.lennar_df['Normalized_Project'] = self.lennar_df['COMMUNITY_RAW'].apply(clean_lennar_community)

        # QB
        self.qb_df = pd.read_excel(self.qb_path)
        self.qb_df = self.qb_df.dropna(subset=['Name', 'Type'])
        self.qb_df['Amount'] = pd.to_numeric(self.qb_df['Amount'], errors='coerce').fillna(0)
        self.qb_df['Name_Clean'] = self.qb_df['Name'].astype(str).str.strip().str.upper()

        def parse_qb_row(name):
            parts = str(name).split(':')
            if len(parts) >= 2:
                project = parts[1].strip()
                phase_raw = parts[-1].strip() if len(parts) >= 4 else "UNKNOWN"
                mapped_proj = self.mapping_dict.get(project, project)
                return pd.Series({'Normalized_Project': mapped_proj, 'Phase': phase_raw})
            return pd.Series({'Normalized_Project': name, 'Phase': 'UNKNOWN'})
            
        parsed = self.qb_df['Name_Clean'].apply(parse_qb_row)
        self.qb_df = pd.concat([self.qb_df, parsed], axis=1)

    def audit(self):
        self.load_data()
        
        # Phase 1: Validar Diferencia Total Exacta
        subtotal_lennar = self.lennar_df['AMOUNT PAID'].sum()
        subtotal_qb = self.qb_df['Amount'].sum()
        
        print(f"Total Lennar: ${subtotal_lennar:,.2f}")
        print(f"Total QuickBooks: ${subtotal_qb:,.2f}")
        total_diff = round(subtotal_lennar - subtotal_qb, 2)
        print(f"Diferencia Neta Detectada: ${total_diff:,.2f}")
        
        if total_diff != 238.68:
            print("\n[ERROR] Validación Cruzada Fallida! El script no llega a $238.68.")
            sys.exit(1)
            
        print("[OK] Diferencia Total Exacta validada ($238.68). Procediendo al desglose por Fase.\n")
        
        # Agrupación por Proyecto + Phase
        lennar_g = self.lennar_df.groupby(['Normalized_Project', 'Phase'])['AMOUNT PAID'].sum().reset_index()
        qb_g = self.qb_df.groupby(['Normalized_Project', 'Phase'])['Amount'].sum().reset_index()
        
        merge_df = pd.merge(
            lennar_g.rename(columns={'AMOUNT PAID': 'Lennar'}),
            qb_g.rename(columns={'Amount': 'QB'}),
            on=['Normalized_Project', 'Phase'], how='outer'
        ).fillna(0)
        
        merge_df['Diff'] = (merge_df['Lennar'] - merge_df['QB']).round(2)
        
        discrepancias = []
        for _, row in merge_df[merge_df['Diff'] != 0].iterrows():
            proj, auth_phase, diff = row['Normalized_Project'], row['Phase'], row['Diff']
            
            # Buscar el Memo correspondiente en QB para esta fase
            qb_matches = self.qb_df[(self.qb_df['Normalized_Project'] == proj) & (self.qb_df['Phase'] == auth_phase)]
            memos = ", ".join(qb_matches['Memo'].dropna().astype(str).unique()) if not qb_matches.empty else "N/A"
            
            action = f"Corregir monto en Memo {memos}. Falta ${diff:,.2f}" if diff > 0 else f"Corregir monto en Memo {memos}. Sobra ${abs(diff):,.2f}"
            
            discrepancias.append({
                'Proyecto': proj,
                'Fase': auth_phase,
                'Memo QB': memos,
                'Monto Lennar': f"${row['Lennar']:,.2f}",
                'Monto QB': f"${row['QB']:,.2f}",
                'Diferencia': f"${diff:,.2f}",
                'Acción Correctiva': action
            })

        # Save CSV
        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        df_log = pd.DataFrame(discrepancias)
        csv_path = self.output_dir / f"audit_results_{ts}.csv"
        df_log.to_csv(csv_path, index=False)
        
        # Save Markdown Report
        md_path = self.output_dir / f"audit_report_{ts}.md"
        with open(md_path, 'w') as f:
            f.write("# 📋 Reporte de Discrepancias Lennar vs QuickBooks\n\n")
            f.write(f"**Total Lennar:** ${subtotal_lennar:,.2f}  \n")
            f.write(f"**Total QuickBooks:** ${subtotal_qb:,.2f}  \n")
            f.write(f"**Diferencia Exacta:** ${total_diff:,.2f}  \n\n")
            f.write("## ❗ Errores Encontrados\n\n")
            f.write("| Proyecto | Fase | Memo | Lennar | QB | Diferencia | Acción Correctiva |\n")
            f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
            for d in discrepancias:
                f.write(f"| {d['Proyecto']} | {d['Fase']} | {d['Memo QB']} | {d['Monto Lennar']} | {d['Monto QB']} | {d['Diferencia']} | {d['Acción Correctiva']} |\n")
                
        print(f"[✓] Archivo CSV exportado en: {csv_path}")
        print(f"[✓] Reporte MD exportado en: {md_path}")
        
        # Print table to console
        print("\nRESUMEN DE ERRORES:")
        for d in discrepancias:
            print(f"-> {d['Proyecto']} (Fase {d['Fase']}) | Dif: {d['Diferencia']} | {d['Acción Correctiva']}")

if __name__ == "__main__":
    r = LennarQBReconciler(
        "doc_to_test/Mapeo de Nombres.xlsx",
        "doc_to_test/lennar check.xlsx",
        "doc_to_test/to check from qb.xlsx",
        "output"
    )
    r.audit()
