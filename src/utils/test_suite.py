import sys
import os
from pathlib import Path
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reconciler import LennarQBReconciler

def run_tests():
    data_dir = Path("data")
    mapping_path = data_dir / "Mapeo de Nombres.xlsx"
    lennar_path = data_dir / "lennar check.xlsx"
    qb_path = data_dir / "to check from qb.xlsx"
    
    # 1. Data Schema Test
    print("Running Data Schema Test...")
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping file not found at {mapping_path}")
        
    df_map = pd.read_excel(mapping_path)
    expected_cols = ['QuickBooks Name', 'Lennar Name (Simplified)', 'Foreman']
    
    for col in expected_cols:
        if col not in df_map.columns:
            raise KeyError(f"Data Schema Error: Missing required column '{col}' in Mapping file.")
    print("[PASS] Data Schema is accurate.")

    # 2. Backend Logic Test
    print("Running Backend Logic Test with historical files...")
    if not (lennar_path.exists() and qb_path.exists()):
        print("[SKIP] Historical test files missing. Skipping logic test.")
        return
        
    rec = LennarQBReconciler(
        mapping_path=str(mapping_path),
        lennar_path=str(lennar_path),
        qb_path=str(qb_path),
        output_dir="output"
    )
    
    result = rec.audit()
    diff = result['total_diff']
    
    if diff != 238.68:
        raise ValueError(f"Logic Integrity Error: Expected Net Difference of $238.68, got ${diff}")
        
    print(f"[PASS] Backend Math Validator perfectly matched expected baseline (${diff}).")
    print("ALL TESTS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    run_tests()
