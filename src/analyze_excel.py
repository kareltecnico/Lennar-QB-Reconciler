import pandas as pd
from pathlib import Path
import sys

def main():
    base_dir = Path("doc_to_test")
    base_dir = base_dir.resolve()
    
    if not base_dir.exists():
        print(f"Error: La carpeta {base_dir} no existe.")
        sys.exit(1)
        
    print(f"Buscando archivos en: {base_dir}\n")

    files = [
        "Mapeo de Nombres.xlsx",
        "lennar check_template.xlsx",
        "to check from qb_template.xlsx"
    ]

    for f in files:
        path = base_dir / f
        if not path.exists():
            print(f"[!] Archivo no encontrado: {f}")
            continue

        try:
            # Cargar sólo las primeras filas para rápido análisis
            df = pd.read_excel(path, nrows=5)
            print(f"[OK] Archivo cargado exitosamente: {f}")
            print(f"     Columnas detectadas: {df.columns.tolist()}")
        except Exception as e:
            print(f"[ERROR] No se pudo leer {f}: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    main()
