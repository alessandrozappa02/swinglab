@echo off
chcp 65001 >nul
cd /d "%~dp0"
title SwingLab

if not exist ".venv\Scripts\python.exe" (
  echo Creo l'ambiente Python, solo la prima volta...
  py -3.12 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 (
    echo.
    echo Python non trovato. Installa Python 3.12 da https://www.python.org/downloads/
    echo e spunta "Add python.exe to PATH" durante l'installazione.
    pause
    exit /b 1
  )
)

if not exist ".venv\installato.txt" (
  echo Installo le librerie: qualche minuto, solo la prima volta...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Installazione non riuscita: controlla la connessione e riprova.
    pause
    exit /b 1
  )
  echo ok> ".venv\installato.txt"
)

echo Avvio SwingLab: il browser si apre da solo. Per chiudere, chiudi questa finestra.
".venv\Scripts\python.exe" -m streamlit run app.py
pause
