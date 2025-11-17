@echo off
REM Script pour déployer l'application sur Scalingo (Windows)
REM À exécuter après avoir installé le CLI Scalingo et être connecté

set PROJECT_NAME=openchemfacts-api

echo === Déploiement sur Scalingo ===
echo.

REM Vérifier que le CLI Scalingo est installé
where scalingo >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Le CLI Scalingo n'est pas installé.
    echo Téléchargez-le depuis : https://cli.scalingo.com
    exit /b 1
)

echo 1. Connexion à Scalingo...
echo    (Cette étape ouvrira votre navigateur pour l'authentification)
scalingo login

echo.
echo 2. Création du projet '%PROJECT_NAME%'...
scalingo create %PROJECT_NAME%

echo.
echo 3. Liaison du dépôt Git...
scalingo link %PROJECT_NAME%

echo.
echo 4. Configuration de la variable d'environnement CORS...
scalingo env-set ALLOWED_ORIGINS=https://openchemfacts.com

echo.
echo ✅ Configuration terminée !
echo.
echo Pour déployer, exécutez :
echo   git push scalingo main
echo.
echo Pour voir les logs :
echo   scalingo logs
echo.
echo Pour vérifier l'état :
echo   scalingo status

pause

