import subprocess
from pathlib import Path

def auto_commit_and_push(file_paths):
    """
    Agrega los archivos de log especificados, hace commit y sube al remoto.
    Asume que el directorio actual es un repositorio Git.
    """
    if not isinstance(file_paths, list):
        file_paths = [file_paths]
        
    print("\n--- Iniciando GitHub Auto-Backup ---")
    try:
        # Añadir archivos específicos (solo CSV/MD logs)
        for filepath in file_paths:
            path = Path(filepath)
            if path.exists():
                subprocess.run(["git", "add", str(path)], check=True)
                print(f"[Git] Añadido: {path.name}")
            else:
                print(f"[Git Advertencia] No se encontró el archivo: {filepath}")

        # Comprobar si hay cambios para commitear
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("[Git] No hay cambios nuevos para hacer commit.")
            return

        # Hacer commit
        commit_msg = f"Auto-backup de resultados de auditoría - {Path(file_paths[0]).name}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"[Git] Commit exitoso: '{commit_msg}'")

        # Intentar Push (podría fallar si el remoto no está configurado)
        push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push_result.returncode == 0:
            print("[Git] Push exitoso al remoto.")
        else:
            print("[Git Info] El push falló (probablemente no hay remote configurado).")
            # print(push_result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"[Git Error] Falló la ejecución de git: {e}")
    except Exception as e:
        print(f"[Git Error] Error inesperado en auto-backup: {e}")
        
    print("--- Fin Auto-Backup ---\n")

if __name__ == "__main__":
    auto_commit_and_push("output/")
