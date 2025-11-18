@echo off
REM Script pour vérifier l'état du serveur Scalingo en production
REM Usage: check_scalingo.bat

echo === Vérification du serveur Scalingo ===
echo.

REM Vérifier que le CLI Scalingo est installé
where scalingo >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Le CLI Scalingo n'est pas installé.
    echo Téléchargez-le depuis : https://cli.scalingo.com
    pause
    exit /b 1
)

echo 1. Vérification du statut de l'application...
scalingo status
echo.

echo 2. Test du health check...
echo Récupération de l'URL de l'application...
for /f "tokens=*" %%i in ('scalingo open --print') do set APP_URL=%%i
if "%APP_URL%"=="" (
    echo ⚠️  Impossible de récupérer l'URL. Vérification manuelle nécessaire.
) else (
    echo URL: %APP_URL%
    echo Test de %APP_URL%/health...
    curl -s %APP_URL%/health
    echo.
    echo.
)

echo 3. Dernières lignes des logs (erreurs uniquement)...
scalingo logs --lines 50 --filter "error OR exception OR traceback" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Aucune erreur récente trouvée dans les logs.
)
echo.

echo 4. Métriques de ressources...
scalingo stats --one-shot 2>nul
echo.

echo === Vérification terminée ===
echo.
echo Commandes utiles:
echo   - Voir tous les logs: scalingo logs
echo   - Redémarrer: scalingo restart
echo   - Ouvrir l'app: scalingo open
echo.

pause

