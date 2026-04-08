import pandas as pd
from pathlib import Path
import os
import sys
import sqlite3

class LennarQBReconciler:
    def __init__(self, db_path, lennar_path, qb_path, output_dir):
        self.db_path = Path(db_path)
        self.lennar_path = Path(lennar_path)
        self.qb_path = Path(qb_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_db_initialized()
        
    def _ensure_db_initialized(self):
        # Create table if not exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mappings (
                qb_name TEXT PRIMARY KEY,
                lennar_name TEXT,
                foreman TEXT
            )
        ''')
        
        # Check if empty, import from excel fallback
        cursor.execute('SELECT COUNT(*) FROM mappings')
        count = cursor.fetchone()[0]
        
        if count == 0:
            legacy_excel = Path("data/Mapeo de Nombres.xlsx")
            if legacy_excel.exists():
                df = pd.read_excel(legacy_excel)
                if 'QuickBooks Name' in df.columns:
                    qb_col = 'QuickBooks Name'
                    len_col = 'Lennar Name (Simplified)'
                else:
                    qb_col = 'Nombre en QuickBooks'
                    len_col = 'Nombre en Lennar (Simplificado)'
                    
                foreman_col = 'Foreman' if 'Foreman' in df.columns else None
                
                for _, row in df.iterrows():
                    q_val = str(row[qb_col]).strip()
                    l_val = str(row[len_col]).strip()
                    f_val = str(row[foreman_col]).strip() if foreman_col and not pd.isna(row[foreman_col]) else "Pending Assignment"
                    cursor.execute('''
                        INSERT OR IGNORE INTO mappings (qb_name, lennar_name, foreman)
                        VALUES (?, ?, ?)
                    ''', (q_val, l_val, f_val))
        conn.commit()
        conn.close()
        
    def _find_header_row(self, path, required_cols_upper, max_scan=10):
        """Scan up to max_scan rows to find the row index where required columns exist.
        Returns the integer row index suitable for pd.read_excel(header=N), or 0 as fallback."""
        for i in range(max_scan):
            try:
                probe = pd.read_excel(path, header=i, nrows=0)
                probe_cols = [str(c).strip().replace('\n', ' ').upper() for c in probe.columns]
                if all(req in probe_cols for req in required_cols_upper):
                    return i
            except Exception:
                break
        return 0  # Fallback: assume row 0 is the header

    def _build_match_tables(self):
        """Pre-compute sorted key/value lists for the aggressive matching engine.

        Both lists are sorted longest-first so that, when multiple substrings
        match, the most specific (longest) token wins.
        E.g. 'ALTESSA TH 200' is preferred over 'ALTESSA TH'.
        """
        # keys_sorted: list of (key_upper, value_upper) sorted by len(key) desc
        self._keys_sorted = sorted(
            self.mapping_dict.items(),
            key=lambda kv: len(kv[0]),
            reverse=True
        )
        # values_sorted: list of (value_upper, value_upper) – same value on both sides
        # so _resolve_project can return value directly
        self._values_sorted = sorted(
            set(self.mapping_dict.values()),
            key=len,
            reverse=True
        )

    def _resolve_project(self, raw_name: str) -> str:
        """Aggressive 3-tier project name resolver.

        Tier 1 – Exact key match:
            mapping_dict['WILTON MANORS'] -> 'ALTESSA TH'

        Tier 2 – Key is a substring of raw_name:
            raw_name = 'WILTON MANORS (ALTESSA TH)'
            key      = 'WILTON MANORS'  ->  maps to 'ALTESSA TH'

        Tier 3 – Value is a substring of raw_name:
            raw_name = 'ALTESSA TH SOME SUFFIX'
            value    = 'ALTESSA TH'     ->  returns 'ALTESSA TH'

        Hard-coded aliases (Vivant splits, Redland, Dorta) are resolved first
        before the dictionary scan so they always take priority.
        """
        name = str(raw_name).strip().upper()

        # ── Hard-coded priority aliases ─────────────────────────────────────
        if 'VIVANT' in name:
            if '2510460' in name: return 'VIVANT 2510460'
            if '2510660' in name: return 'VIVANT - 2510660'
        if 'REDLAND' in name:
            return 'REDLAND RIDGE REDWOOD / REDLAND RIDGE SF'
        if 'DORTA' in name:
            return 'SP RESIDENTIAL VILLAS'

        # ── Tier 1: exact key match ─────────────────────────────────────────
        if name in self.mapping_dict:
            return self.mapping_dict[name]

        # ── Tier 2: key is a substring of raw_name (longest key wins) ───────
        for key, value in self._keys_sorted:
            if key and key in name:
                return value

        # ── Tier 3: value is a substring of raw_name (longest value wins) ───
        for value in self._values_sorted:
            if value and value in name:
                return value

        # ── No match: return the input as-is ───────────────────────────────
        return name


    def _check_and_swap_files(self):
        # Use header hunter to detect the real header row before swapping
        lennar_hdr = self._find_header_row(self.lennar_path, ['COMMUNITY'])
        qb_hdr     = self._find_header_row(self.qb_path, ['NAME', 'TYPE', 'AMOUNT'])

        df1_cols = pd.read_excel(self.lennar_path, header=lennar_hdr, nrows=0).columns
        df2_cols = pd.read_excel(self.qb_path,     header=qb_hdr,     nrows=0).columns

        df1_cols_upper = [str(c).strip().upper() for c in df1_cols]
        df2_cols_upper = [str(c).strip().upper() for c in df2_cols]

        if 'COMMUNITY' not in df1_cols_upper and 'COMMUNITY' in df2_cols_upper:
            self.lennar_path, self.qb_path = self.qb_path, self.lennar_path
            
    def load_data(self):
        self._check_and_swap_files()
        
        conn = sqlite3.connect(self.db_path)
        self.mapping_df = pd.read_sql_query('SELECT * FROM mappings', conn)
        conn.close()

        # Normalizing DB
        self.mapping_dict = dict(zip(
            self.mapping_df['qb_name'].astype(str).str.strip().str.upper(),
            self.mapping_df['lennar_name'].astype(str).str.strip().str.upper()
        ))

        self.foreman_dict = dict(zip(
            self.mapping_df['lennar_name'].astype(str).str.strip().str.upper(),
            self.mapping_df['foreman'].astype(str).str.strip()
        ))

        # Build sorted match tables for the aggressive substring engine
        self._build_match_tables()

        # ── LENNAR ─────────────────────────────────────────────────────────────
        lennar_hdr = self._find_header_row(self.lennar_path, ['COMMUNITY', 'AMOUNT PAID'])
        self.lennar_df = pd.read_excel(self.lennar_path, header=lennar_hdr)
        self.lennar_df.columns = [str(c).strip().replace('\n', ' ').upper() for c in self.lennar_df.columns]

        if 'COMMUNITY' not in self.lennar_df.columns or 'AMOUNT PAID' not in self.lennar_df.columns:
            raise ValueError(
                f"Data Schema Error (Lennar file): Missing required columns 'COMMUNITY' or 'AMOUNT PAID'. "
                f"Detected columns: {list(self.lennar_df.columns)}"
            )

        self.lennar_df = self.lennar_df.dropna(subset=['COMMUNITY'])
        # Strip commas from currency strings before numeric conversion (e.g. "1,234.56" → 1234.56)
        self.lennar_df['AMOUNT PAID'] = (
            self.lennar_df['AMOUNT PAID'].astype(str).str.replace(',', '', regex=False)
        )
        self.lennar_df['AMOUNT PAID'] = pd.to_numeric(self.lennar_df['AMOUNT PAID'], errors='coerce').fillna(0)
        # Keep ALL rows (positive = regular payments, negative = backcharges)
        # Filtering is done later in audit() so both segments are available.
        self.lennar_df = self.lennar_df[self.lennar_df['AMOUNT PAID'] != 0]
        self.lennar_df['COMMUNITY_RAW'] = self.lennar_df['COMMUNITY'].astype(str).str.strip().str.upper()

        def get_lennar_phase(activity):
            activity = str(activity).upper()
            if 'ROUGH'    in activity: return 'A'
            if 'TOP OUT'  in activity: return 'B'
            if 'FINAL'    in activity: return 'C'
            if 'WARRANTY' in activity or 'THEFT' in activity: return 'X'
            return 'UNKNOWN'

        # Preserve ACTIVITY column — fall back to empty string if absent in this Excel
        if 'ACTIVITY' in self.lennar_df.columns:
            self.lennar_df['ACTIVITY'] = self.lennar_df['ACTIVITY'].fillna('')
        else:
            self.lennar_df['ACTIVITY'] = ''
        self.lennar_df['Phase'] = self.lennar_df['ACTIVITY'].apply(get_lennar_phase)

        # Aggressive mapping: resolve each Lennar community name to its canonical project
        self.lennar_df['Normalized_Project'] = (
            self.lennar_df['COMMUNITY_RAW'].apply(self._resolve_project)
        )

        # ── QUICKBOOK ──────────────────────────────────────────────────────────
        qb_hdr = self._find_header_row(self.qb_path, ['NAME', 'TYPE', 'AMOUNT'])
        self.qb_df = pd.read_excel(self.qb_path, header=qb_hdr)
        # Normalize headers: strip whitespace and newlines
        self.qb_df.columns = [str(c).strip().replace('\n', ' ') for c in self.qb_df.columns]

        if 'Name' not in self.qb_df.columns or 'Type' not in self.qb_df.columns or 'Amount' not in self.qb_df.columns:
            raise ValueError(
                f"Data Schema Error (Quickbook file): Missing required columns 'Name', 'Type', or 'Amount'. "
                f"Detected columns: {list(self.qb_df.columns)}"
            )

        self.qb_df = self.qb_df.dropna(subset=['Name', 'Type'])
        # Strip commas from currency strings before numeric conversion
        self.qb_df['Amount'] = (
            self.qb_df['Amount'].astype(str).str.replace(',', '', regex=False)
        )
        self.qb_df['Amount'] = pd.to_numeric(self.qb_df['Amount'], errors='coerce').fillna(0)
        self.qb_df['Name_Clean'] = self.qb_df['Name'].astype(str).str.strip().str.upper()

        def parse_qb_row(name):
            """Extract the project segment from a QB colon-delimited name, then
            run through the aggressive mapping engine to get the canonical project."""
            parts = str(name).split(':')
            if len(parts) >= 2:
                # parts[1] is the project token; last part is the phase
                project_raw = parts[1].strip()
                phase_raw   = parts[-1].strip() if len(parts) >= 4 else 'UNKNOWN'
            else:
                project_raw = name
                phase_raw   = 'UNKNOWN'

            # Aggressive resolve: exact → key-substring → value-substring
            mapped_proj = self._resolve_project(project_raw)
            return pd.Series({'Normalized_Project': mapped_proj, 'Phase': phase_raw})

        parsed = self.qb_df['Name_Clean'].apply(parse_qb_row)
        self.qb_df = pd.concat([self.qb_df, parsed], axis=1)

    def audit(self):
        self.load_data()

        # ── Segment Lennar rows ──────────────────────────────────────────────
        # Positive rows = regular payments used for main reconciliation
        # Negative rows = backcharges tracked separately
        lennar_pos = self.lennar_df[self.lennar_df['AMOUNT PAID'] > 0].copy()
        lennar_neg = self.lennar_df[self.lennar_df['AMOUNT PAID'] < 0].copy()

        bc_count = len(lennar_neg)
        bc_total = lennar_neg['AMOUNT PAID'].sum()
        print(f"[AUDIT] Lennar rows loaded: {len(self.lennar_df)} "
              f"(positive: {len(lennar_pos)}, backcharges: {bc_count})")
        if bc_count > 0:
            print(f"[AUDIT] Total backcharge amount: ${bc_total:,.2f}")

        # ── KPI totals ───────────────────────────────────────────────────────
        subtotal_lennar_pos = lennar_pos['AMOUNT PAID'].sum()   # No BC
        subtotal_lennar_bc  = bc_total                          # BC total (negative)
        subtotal_qb         = self.qb_df['Amount'].sum()
        total_diff          = round(subtotal_lennar_pos - subtotal_qb, 2)

        # ── Main reconciliation uses ONLY positive rows ──────────────────────
        lennar_g = lennar_pos.groupby(['Normalized_Project', 'Phase'])['AMOUNT PAID'].sum().reset_index()
        qb_g     = self.qb_df.groupby(['Normalized_Project', 'Phase'])['Amount'].sum().reset_index()

        merge_df = pd.merge(
            lennar_g.rename(columns={'AMOUNT PAID': 'Lennar'}),
            qb_g.rename(columns={'Amount': 'QB'}),
            on=['Normalized_Project', 'Phase'], how='outer'
        ).fillna(0)

        merge_df['Diff'] = (merge_df['Lennar'] - merge_df['QB']).round(2)

        project_net = merge_df.groupby('Normalized_Project').agg(
            Proj_Lennar=('Lennar', 'sum'),
            Proj_QB=('QB', 'sum'),
            Proj_Diff=('Diff', 'sum')
        ).reset_index()

        # ── Backcharge detail: group by project with activity descriptions ───
        backcharges_detail = {}   # { 'PROJECT NAME': [{'activity': ..., 'amount': ...}, ...] }
        if bc_count > 0:
            bc_grouped = lennar_neg.groupby('Normalized_Project')
            for proj_name, group in bc_grouped:
                entries = []
                for _, bc_row in group.iterrows():
                    activity_label = str(bc_row.get('ACTIVITY', '')).strip() or 'N/A'
                    entries.append({
                        'activity': activity_label,
                        'amount':   bc_row['AMOUNT PAID'],       # negative number
                        'foreman':  self.foreman_dict.get(proj_name, 'Pending Assignment')
                    })
                backcharges_detail[proj_name] = entries
            print(f"[AUDIT] Backcharges found in {len(backcharges_detail)} project(s): "
                  f"{list(backcharges_detail.keys())}")

        # ── Build dashboard lines & discrepancies ────────────────────────────
        discrepancias  = []
        dashboard_lines = []

        for _, r in project_net.iterrows():
            proj     = r['Normalized_Project']
            net_diff = round(r['Proj_Diff'], 2)
            f_man    = self.foreman_dict.get(proj, 'Pending Assignment')

            if net_diff == 0.00:
                internal_diffs = merge_df[
                    (merge_df['Normalized_Project'] == proj) & (merge_df['Diff'] != 0)
                ]
                if not internal_diffs.empty:
                    dashboard_lines.append(
                        f"✅ PROJECT BALANCED: {proj} 💯. Foreman: {f_man}"
                    )
                else:
                    dashboard_lines.append(
                        f"✅ PROJECT BALANCED: {proj} 💯. Foreman: {f_man}"
                    )
            else:
                dashboard_lines.append(
                    f"🔴 REQUIRED ACTION DETECTED: {proj} | Diff Total: ${net_diff:,.2f}"
                )

                internal_diffs = merge_df[
                    (merge_df['Normalized_Project'] == proj) & (merge_df['Diff'] != 0)
                ]

                for _, row in internal_diffs.iterrows():
                    auth_phase, diff = row['Phase'], row['Diff']

                    qb_matches = self.qb_df[
                        (self.qb_df['Normalized_Project'] == proj) &
                        (self.qb_df['Phase'] == auth_phase)
                    ]
                    memos = (
                        ", ".join(qb_matches['Memo'].dropna().astype(str).unique())
                        if not qb_matches.empty else 'N/A'
                    )

                    diff_type = 'Short' if diff > 0 else 'Over'
                    action    = f"Correct amount in Invoice {memos}. {diff_type} by ${abs(diff):,.2f}."

                    dashboard_lines.append(f"    - Phase {auth_phase}: {action}")

                    discrepancias.append({
                        'Project':           proj,
                        'Phase':             auth_phase,
                        'Quickbook Invoice': memos,
                        'Lennar Amount':     f"${row['Lennar']:,.2f}",
                        'Quickbook Amount':  f"${row['QB']:,.2f}",
                        'Difference':        f"${diff:,.2f}",
                        'Action Required':   action,
                        'Foreman':           f_man
                    })

        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if discrepancias:
            df_log   = pd.DataFrame(discrepancias)
            csv_path = self.output_dir / f"audit_results_{ts}.csv"
            df_log.to_csv(csv_path, index=False)

        return {
            "total_lennar":      subtotal_lennar_pos,   # Positives only (No BC)
            "total_lennar_bc":   subtotal_lennar_bc,    # Backcharge total (negative)
            "total_qb":          subtotal_qb,
            "total_diff":        total_diff,
            "dashboard_lines":   dashboard_lines,
            "discrepancias":     discrepancias,
            "backcharges_detail": backcharges_detail,   # {project: [{activity, amount, foreman}]}
        }
