@echo off
REM Script pour vérifier si le serveur local est démarré (Windows)
REM Usage: check_server.bat [port]

setlocal enabledelayedexpansion

set PORT=%1
if "%PORT%"=="" set PORT=8000
set URL=http://localhost:%PORT%

echo === Vérification du serveur local ===
echo.

REM Vérifier si curl est disponible
where curl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  curl n'est pas installé. Vérification manuelle recommandée.
    echo    Ouvrez %URL%/health dans votre navigateur
    echo.
    echo Pour installer curl sur Windows:
    echo    winget install curl.curl
    pause
    exit /b 1
)

REM Vérifier le endpoint /health
echo Vérification de %URL%/health...
curl -s -o nul -w "%%{http_code}" "%URL%/health" > temp_http_code.txt 2>nul
set /p HTTP_CODE=<temp_http_code.txt
del temp_http_code.txt

if "%HTTP_CODE%"=="200" (
    echo ✅ Serveur démarré et fonctionnel !
    echo.
    echo 📊 Endpoints disponibles:
    echo    - Health: %URL%/health
    echo    - Documentation: %URL%/docs
    echo    - ReDoc: %URL%/redoc
    echo    - API Summary: %URL%/api/summary
    echo.
    
    REM Afficher la réponse du health check
    echo Réponse du health check:
    curl -s "%URL%/health"
    echo.
) else (
    echo ❌ Serveur non accessible (code HTTP: %HTTP_CODE%)
    echo.
    echo Le serveur n'est probablement pas démarré.
    echo Pour démarrer le serveur:
    echo    start_local.bat %PORT%
    echo    ou
    echo    uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload
    pause
    exit /b 1
)

pause

