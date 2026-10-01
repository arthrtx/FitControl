@echo off
setlocal
cd /d "%~dp0"

set "PY_VERSION=3.12.10"
set "PY_URL=https://www.python.org/ftp/python/%PY_VERSION%/python-%PY_VERSION%-amd64.exe"
set "LOCAL_PY=%LOCALAPPDATA%\FitControl\Python312\python.exe"
set "VENV_PY=.venv\Scripts\python.exe"

if exist "%VENV_PY%" goto :run

echo [FitControl] A procurar Python...
set "PY="
py -3 -c "print(1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "print(1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    if exist "%LOCAL_PY%" set "PY=%LOCAL_PY%"
)
if not defined PY call :bootstrap || goto :py_error

:create_venv
echo [FitControl] A criar ambiente virtual (.venv)...
if exist ".venv\Scripts\python.exe" goto :deps
"%PY%" -m venv .venv
if not exist "%VENV_PY%" goto :venv_error

:deps
echo [FitControl] A instalar dependencias (pode demorar na 1a vez)...
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -r requirements.txt --quiet
if errorlevel 1 goto :deps_error

:run
echo [FitControl] A iniciar a aplicacao...
"%VENV_PY%" run_gui.py
if errorlevel 1 goto :app_error
exit /b 0

:bootstrap
echo [FitControl] Python nao encontrado. A instalar Python %PY_VERSION% (so para este utilizador)...
set "TMP=%TEMP%\fitcontrol_python_installer.exe"
del /q "%TMP%" >nul 2>&1
curl -fsSL -o "%TMP%" "%PY_URL%"
if not exist "%TMP%" exit /b 1
echo [FitControl] A instalar, aguarde um momento...
start /wait "" "%TMP%" /quiet InstallAllUsers=0 TargetDir="%LOCALAPPDATA%\FitControl\Python312" PrependPath=0 Include_launcher=0 Shortcuts=0
del /q "%TMP%" >nul 2>&1
if not exist "%LOCAL_PY%" exit /b 1
exit /b 0

:py_error
echo.
echo [ERRO] Nao foi possivel instalar o Python automaticamente.
echo Instale o Python %PY_VERSION%+ (64 bits) de:
echo   %PY_URL%
echo e marque "Add Python to PATH" durante a instalacao.
pause
exit /b 1

:venv_error
echo.
echo [ERRO] Falha ao criar o ambiente virtual .venv
pause
exit /b 1

:deps_error
echo.
echo [ERRO] Falha ao instalar as dependencias de requirements.txt
pause
exit /b 1

:app_error
echo.
echo [ERRO] A aplicacao terminou com erro.
pause
exit /b 1
