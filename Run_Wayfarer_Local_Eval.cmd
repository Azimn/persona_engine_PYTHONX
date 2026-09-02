@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
  python tools\local_eval.py preflight --output-dir .wayfarer-local-eval
) else (
  python tools\local_eval.py %*
)

set CODE=%ERRORLEVEL%
echo.
echo Wayfarer local evaluation exit code: %CODE%
exit /b %CODE%
