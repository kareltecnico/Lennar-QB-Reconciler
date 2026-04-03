#!/bin/bash

# Lennar-QB Reconciler - Push Script (Mac/Linux)

echo "Inicializando entorno Git local..."
git init

echo "Añadiendo el Remote Repository URL (si no existe)..."
git remote add origin https://github.com/kareltecnico/Lennar-QB-Reconciler.git 2>/dev/null || git remote set-url origin https://github.com/kareltecnico/Lennar-QB-Reconciler.git

echo "Cambiando rama principal a 'main'..."
git branch -M main

echo "Haciendo Push al origen..."
git push -u origin main

echo "Push exitoso."
