#!/bin/bash
echo "Inicializando Lennar-QB Reconciler Web App..."

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar streamlit
streamlit run src/app.py
