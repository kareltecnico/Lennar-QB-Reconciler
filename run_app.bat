@echo off
echo Inicializando Lennar-QB Reconciler Web App...

IF EXIST "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

streamlit run src\app.py
pause
