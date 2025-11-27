@echo off
REM Script pour exécuter les tests automatiquement
REM Usage: scripts\run_tests.bat

echo === Execution des tests ===
echo.

REM Vérifier que l'environnement virtuel existe
if not exist "venv\Scripts\activate.bat" (
    echo ⚠️  Environnement virtuel non trouve.
    echo    Creation de l'environnement virtuel...
    python -m venv venv
    echo ✅ Environnement virtuel cree.
    echo.
)

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Vérifier que pytest est installé
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo ⚠️  pytest n'est pas installe. Installation...
    pip install pytest httpx
    echo ✅ pytest installe.
    echo.
)

REM Exécuter les tests
echo Execution des tests...
echo.
pytest tests/ -v

echo.
echo === Tests termines ===
pause

