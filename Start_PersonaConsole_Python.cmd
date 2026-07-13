@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE="
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
) else (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=python"
)

if "%PYTHON_EXE%"=="" (
  echo Python was not found.
  echo Install Python or run this from a Codex environment with the bundled runtime.
  pause
  exit /b 1
)

echo Starting PersonaConsole Python Lab...
start "" "http://127.0.0.1:8012/start"
"%PYTHON_EXE%" -m uvicorn "persona_engine.ui:create_app" --factory --host 127.0.0.1 --port 8012
pause
