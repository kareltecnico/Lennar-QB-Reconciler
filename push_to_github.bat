@echo off
echo Inicializando entorno Git local...
git init

echo Añadiendo el Remote Repository URL...
git remote add origin https://github.com/kareltecnico/Lennar-QB-Reconciler.git
IF %ERRORLEVEL% NEQ 0 (
  git remote set-url origin https://github.com/kareltecnico/Lennar-QB-Reconciler.git
)

echo Cambiando rama principal a 'main'...
git branch -M main

echo Haciendo Push al origen...
git push -u origin main

echo Push exitoso.
pause
