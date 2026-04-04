import sys
import os
from pathlib import Path
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reconciler import LennarQBReconciler

def run_tests():
    data_dir = Path("data")
    db_path = data_dir / "reconciler.db"
    lennar_path = data_dir / "lennar check.xlsx"
    qb_path = data_dir / "to check from qb.xlsx"
    
    # Init blank run to ensure DB creation
    try:
        LennarQBReconciler(str(db_path), str(lennar_path), str(qb_path), "output")
    except Exception:
        pass # Expected if files don't perfectly exist, but DB is created first

    # 1. Data Schema Test
    print("Running Data Schema Test (SQLite)...")
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
        
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(mappings)")
    columns_info = cursor.fetchall()
    conn.close()
    
    columns = [info[1] for info in columns_info]
    expected_cols = ['qb_name', 'lennar_name', 'foreman']
    
    for col in expected_cols:
        if col not in columns:
            raise KeyError(f"Data Schema Error: Missing required column '{col}' in SQLite mapping table.")
    print("[PASS] SQLite Data Schema is accurate.")

    # 2. Backend Logic Test
    print("Running Backend Logic Test with historical files...")
    if not (lennar_path.exists() and qb_path.exists()):
        print("[SKIP] Historical test files missing. Skipping logic test.")
        return
        
    rec = LennarQBReconciler(
        db_path=str(db_path),
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
