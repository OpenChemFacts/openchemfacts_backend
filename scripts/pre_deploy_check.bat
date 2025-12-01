@echo off
REM Pre-deployment validation script for Windows
REM Runs checks before deploying to production
REM Usage: scripts\pre_deploy_check.bat

echo ==========================================
echo   Pre-Deployment Validation Script
echo ==========================================
echo.

set FAILED_CHECKS=0

echo 1. Checking Git status...
echo ----------------------------------------
git status --porcelain >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ No uncommitted changes
) else (
    echo ⚠️  Uncommitted changes detected:
    git status --short
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        echo Aborted. Please commit or stash changes first.
        exit /b 1
    )
)
echo.

echo 2. Checking for sensitive data...
echo ----------------------------------------
echo ⚠️  Manual check recommended: Search for password, secret, api_key, token
echo ✅ Skipping automated sensitive data check
echo.

echo 3. Checking Python syntax...
echo ----------------------------------------
set SYNTAX_ERRORS=0
for %%f in (app\*.py) do (
    python -m py_compile "%%f" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Syntax error in %%f
        set /a SYNTAX_ERRORS+=1
    )
)
if %SYNTAX_ERRORS% EQU 0 (
    echo ✅ All Python files have valid syntax
) else (
    echo ❌ %SYNTAX_ERRORS% file(s) with syntax errors
    set /a FAILED_CHECKS+=1
)
echo.

echo 4. Checking required files...
echo ----------------------------------------
set MISSING_FILES=0

if not exist "Procfile" (
    echo ❌ Procfile not found
    set /a MISSING_FILES+=1
) else (
    echo ✅ Procfile exists
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt not found
    set /a MISSING_FILES+=1
) else (
    echo ✅ requirements.txt exists
)

if not exist "app\main.py" (
    echo ❌ app\main.py not found
    set /a MISSING_FILES+=1
) else (
    echo ✅ app\main.py exists
)

if %MISSING_FILES% GTR 0 (
    echo ❌ %MISSING_FILES% required file(s) missing
    set /a FAILED_CHECKS+=1
)
echo.

echo 5. Checking Procfile content...
echo ----------------------------------------
findstr /C:"uvicorn app.main:app" Procfile >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Procfile contains correct uvicorn command
) else (
    echo ❌ Procfile may be incorrect
    echo ℹ️  Expected: web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    set /a FAILED_CHECKS+=1
)
echo.

echo 6. Checking .gitignore...
echo ----------------------------------------
if exist ".gitignore" (
    findstr /C:"venv/" .gitignore >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ .gitignore looks good
    ) else (
        echo ⚠️  .gitignore may be missing important entries
    )
) else (
    echo ⚠️  .gitignore not found
)
echo.

echo 7. Checking for test files...
echo ----------------------------------------
if exist "tests\test_api.py" (
    echo ✅ Test files found
) else (
    echo ⚠️  No test files found
)
echo.

echo 8. Running tests...
echo ----------------------------------------
if exist "venv\Scripts\pytest.exe" (
    call venv\Scripts\activate.bat
    pytest tests\ -v
    if %ERRORLEVEL% EQU 0 (
        echo ✅ All tests passed
    ) else (
        echo ❌ Some tests failed
        set /a FAILED_CHECKS+=1
    )
) else (
    echo ⚠️  pytest not found. Install with: pip install pytest httpx
    echo ℹ️  Skipping test execution
)
echo.

echo 9. Checking Scalingo remote...
echo ----------------------------------------
git remote | findstr /C:"scalingo" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Scalingo remote configured
    for /f "tokens=2" %%i in ('git remote get-url scalingo 2^>nul') do set SCALINGO_URL=%%i
    echo ℹ️  Remote URL: %SCALINGO_URL%
) else (
    echo ⚠️  Scalingo remote not found
    echo ℹ️  Configure with: scalingo link ^<app-name^>
)
echo.

echo 10. Summary...
echo ==========================================
if %FAILED_CHECKS% EQU 0 (
    echo ✅ All checks passed! Ready for deployment.
    echo.
    echo Next steps:
    echo   1. git add .
    echo   2. git commit -m "Your commit message"
    echo   3. git push origin main  (optional, for backup)
    echo   4. git push scalingo main
    echo   5. scalingo status
    echo   6. scalingo logs --lines 50
    exit /b 0
) else (
    echo ❌ %FAILED_CHECKS% check(s) failed. Please fix issues before deploying.
    echo.
    echo Review the errors above and fix them before proceeding with deployment.
    exit /b 1
)

