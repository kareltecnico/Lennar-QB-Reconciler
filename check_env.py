import os
import importlib.util

def check_setup():
    libraries = ['pandas', 'openpyxl']
    path = os.getcwd()
    
    print(f"\n--- Verificando Entorno: {path} ---")
    
    # 1. Verificar Librerías
    for lib in libraries:
        if importlib.util.find_spec(lib) is None:
            print(f"❌ Error: {lib} no está instalado. Corre: pip3 install {lib}")
        else:
            print(f"✅ {lib}: Instalado")

    # 2. Verificar Escritura
    if os.access(path, os.W_OK):
        print(f"✅ Acceso de escritura: OK")
    else:
        print(f"❌ Error: No tienes permisos de escritura en este directorio.")

if __name__ == "__main__":
    check_setup()
