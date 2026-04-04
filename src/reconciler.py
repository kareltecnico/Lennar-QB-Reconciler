import pandas as pd
from pathlib import Path
import os
import sys

class LennarQBReconciler:
    def __init__(self, mapping_path, lennar_path, qb_path, output_dir):
        self.mapping_path = Path(mapping_path)
        self.lennar_path = Path(lennar_path)
        self.qb_path = Path(qb_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _check_and_swap_files(self):
        # Read the first few rows just to get headers
        df1_cols = pd.read_excel(self.lennar_path, nrows=0).columns
        df2_cols = pd.read_excel(self.qb_path, nrows=0).columns
        
        df1_cols_upper = [str(c).strip().upper() for c in df1_cols]
        df2_cols_upper = [str(c).strip().upper() for c in df2_cols]
        
        if 'COMMUNITY' not in df1_cols_upper and 'COMMUNITY' in df2_cols_upper:
            # Swap!
            self.lennar_path, self.qb_path = self.qb_path, self.lennar_path
            
    def load_data(self):
        # Check for smart swap first
        self._check_and_swap_files()
        
        self.mapping_df = pd.read_excel(self.mapping_path)
        
        # Validation for Mapping
        required_map_cols = ['QuickBooks Name', 'Lennar Name (Simplified)']
        for col in required_map_cols:
            if col not in self.mapping_df.columns:
                raise ValueError(f"Data Schema Error: Mapping file is missing '{col}' column.")
        
        if 'Foreman' not in self.mapping_df.columns:
            self.mapping_df['Foreman'] = 'Pending Assignment'
            self.mapping_df.to_excel(self.mapping_path, index=False)
                
        self.mapping_dict = dict(zip(
            self.mapping_df['QuickBooks Name'].astype(str).str.strip().str.upper(), 
            self.mapping_df['Lennar Name (Simplified)'].astype(str).str.strip().str.upper()
        ))
        
        # Lennar
        self.lennar_df = pd.read_excel(self.lennar_path)
        self.lennar_df.columns = [str(c).strip().replace('\n', ' ').upper() for c in self.lennar_df.columns]
        
        # Validation for Lennar
        if 'COMMUNITY' not in self.lennar_df.columns or 'AMOUNT PAID' not in self.lennar_df.columns:
            raise ValueError("Data Schema Error (Lennar file): Missing required columns 'COMMUNITY' or 'AMOUNT PAID'. Please check your Excel structure.")
            
        self.lennar_df = self.lennar_df.dropna(subset=['COMMUNITY'])  # Remove grand totals row
        self.lennar_df['AMOUNT PAID'] = pd.to_numeric(self.lennar_df['AMOUNT PAID'], errors='coerce').fillna(0)
        self.lennar_df = self.lennar_df[self.lennar_df['AMOUNT PAID'] > 0]
        self.lennar_df['COMMUNITY_RAW'] = self.lennar_df['COMMUNITY'].astype(str).str.strip().str.upper()
        
        # Phase Mapping for Lennar
        def get_lennar_phase(activity):
            activity = str(activity).upper()
            if 'ROUGH' in activity: return 'A'
            if 'TOP OUT' in activity: return 'B'
            if 'FINAL' in activity: return 'C'
            if 'WARRANTY' in activity or 'THEFT' in activity: return 'X'
            return 'UNKNOWN'
        
        self.lennar_df['ACTIVITY'] = self.lennar_df.get('ACTIVITY', pd.Series()).fillna('')
        self.lennar_df['Phase'] = self.lennar_df['ACTIVITY'].apply(get_lennar_phase)
        
        # Normalize Project Name for Lennar
        def clean_lennar_community(name):
            if 'VIVANT' in name:
                if '2510460' in name: return 'VIVANT 2510460'
                if '2510660' in name: return 'VIVANT - 2510660'
            if 'REDLAND' in name: return 'REDLAND RIDGE REDWOOD / REDLAND RIDGE SF'
            if 'DORTA' in name: return 'SP RESIDENTIAL VILLAS'
            
            for mapped in set(self.mapping_dict.values()):
                if str(mapped) in name:
                    return str(mapped)
            return name
            
        self.lennar_df['Normalized_Project'] = self.lennar_df['COMMUNITY_RAW'].apply(clean_lennar_community)

        # QuickBooks
        self.qb_df = pd.read_excel(self.qb_path)
        if 'Name' not in self.qb_df.columns or 'Type' not in self.qb_df.columns or 'Amount' not in self.qb_df.columns:
            raise ValueError("Data Schema Error (QuickBooks file): Missing required columns 'Name', 'Type', or 'Amount'.")
            
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
        
        subtotal_lennar = self.lennar_df['AMOUNT PAID'].sum()
        subtotal_qb = self.qb_df['Amount'].sum()
        total_diff = round(subtotal_lennar - subtotal_qb, 2)
        
        lennar_g = self.lennar_df.groupby(['Normalized_Project', 'Phase'])['AMOUNT PAID'].sum().reset_index()
        qb_g = self.qb_df.groupby(['Normalized_Project', 'Phase'])['Amount'].sum().reset_index()
        
        merge_df = pd.merge(
            lennar_g.rename(columns={'AMOUNT PAID': 'Lennar'}),
            qb_g.rename(columns={'Amount': 'QB'}),
            on=['Normalized_Project', 'Phase'], how='outer'
        ).fillna(0)
        
        merge_df['Diff'] = (merge_df['Lennar'] - merge_df['QB']).round(2)
        
        project_net = merge_df.groupby('Normalized_Project')['Diff'].sum().round(2)
        
        discrepancias = []
        dashboard_lines = []
        
        for proj, net_diff in project_net.items():
            if net_diff == 0.00:
                internal_diffs = merge_df[(merge_df['Normalized_Project'] == proj) & (merge_df['Diff'] != 0)]
                if not internal_diffs.empty:
                    dashboard_lines.append(f"✅ PROJECT BALANCED: {proj} (Internal Phase Differences Compensated).")
                else:
                    dashboard_lines.append(f"✅ PROJECT BALANCED: {proj} (Exact Match).")
            else:
                dashboard_lines.append(f"🔴 REQUIRED ACTION DETECTED: {proj} | Diff Total: ${net_diff:,.2f}")
                
                internal_diffs = merge_df[
                    (merge_df['Normalized_Project'] == proj) & 
                    (merge_df['Diff'] != 0)
                ]
                
                for _, row in internal_diffs.iterrows():
                    auth_phase, diff = row['Phase'], row['Diff']
                    
                    qb_matches = self.qb_df[(self.qb_df['Normalized_Project'] == proj) & (self.qb_df['Phase'] == auth_phase)]
                    memos = ", ".join(qb_matches['Memo'].dropna().astype(str).unique()) if not qb_matches.empty else "N/A"
                    
                    action = f"Correct amount in Memo {memos}. Short by ${diff:,.2f}" if diff > 0 else f"Correct amount in Memo {memos}. Over by ${abs(diff):,.2f}"
                    
                    dashboard_lines.append(f"    - Phase {auth_phase}: {action}")
                    
                    discrepancias.append({
                        'Project': proj,
                        'Phase': auth_phase,
                        'QB Memo': memos,
                        'Lennar Amount': f"${row['Lennar']:,.2f}",
                        'QB Amount': f"${row['QB']:,.2f}",
                        'Difference': f"${diff:,.2f}",
                        'Action Required': action
                    })

        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if discrepancias:
            df_log = pd.DataFrame(discrepancias)
            csv_path = self.output_dir / f"audit_results_{ts}.csv"
            df_log.to_csv(csv_path, index=False)
            
        return {
            "total_lennar": subtotal_lennar,
            "total_qb": subtotal_qb,
            "total_diff": total_diff,
            "dashboard_lines": dashboard_lines,
            "discrepancias": discrepancias
        }
