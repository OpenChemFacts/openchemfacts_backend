@echo off
REM Script pour démarrer le serveur local (Windows)
REM Usage: start_local.bat [port]

setlocal enabledelayedexpansion

set PORT=%1
if "%PORT%"=="" set PORT=8000

echo === Démarrage du serveur local ===
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python n'est pas installé.
    pause
    exit /b 1
)

REM Vérifier que l'environnement virtuel existe
if not exist "venv" (
    echo ⚠️  Environnement virtuel non trouvé. Création...
    python -m venv venv
    echo ✅ Environnement virtuel créé.
)

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Vérifier que les dépendances sont installées
python -c "import fastapi" >nul 2>&1
set FASTAPI_OK=%ERRORLEVEL%
python -c "import slowapi" >nul 2>&1
set SLOWAPI_OK=%ERRORLEVEL%
if %FASTAPI_OK% NEQ 0 (
    echo ⚠️  Dépendances non installées. Installation...
    pip install -r requirements.txt
    echo ✅ Dépendances installées.
) else if %SLOWAPI_OK% NEQ 0 (
    echo ⚠️  Dépendances incomplètes. Installation...
    pip install -r requirements.txt
    echo ✅ Dépendances installées.
)

REM Vérifier que le fichier de données existe
dir /b data\results_ecotox_*.parquet >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Aucun fichier de données trouvé dans data\
    echo    Assurez-vous que le fichier results_ecotox_*.parquet existe.
)

echo.
echo 🚀 Démarrage du serveur sur http://localhost:%PORT%
echo    Documentation: http://localhost:%PORT%/docs
echo    Health check: http://localhost:%PORT%/health
echo.
echo Appuyez sur Ctrl+C pour arrêter le serveur.
echo.

REM Démarrer le serveur avec rechargement automatique
uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload

