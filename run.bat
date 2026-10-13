@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title FitControl

set "PY_VERSION=3.12.10"
set "PY_URL=https://www.python.org/ftp/python/%PY_VERSION%/python-%PY_VERSION%-amd64.exe"
set "LOCAL_PY=%LOCALAPPDATA%\FitControl\Python312\python.exe"
set "VENV_PY=.venv\Scripts\python.exe"
set "MARCA=.venv\requisitos_instalados.txt"
set "TESTE=import sys,struct; sys.exit(0 if sys.version_info[:2]>=(3,12) and struct.calcsize('P')==8 else 1)"

rem ambiente ja preparado e com as mesmas dependencias -> arranca logo
if not exist "%VENV_PY%" goto :procurar_python
if not exist "%MARCA%" goto :deps
fc /b requirements.txt "%MARCA%" >nul 2>&1
if errorlevel 1 goto :deps
goto :run

:procurar_python
echo [FitControl] A procurar Python 3.12 ou superior (64 bits)...
set "PY_CMD="

py -3.12 -c "%TESTE%" >nul 2>&1
if not errorlevel 1 set "PY_CMD=py -3.12"
if defined PY_CMD goto :create_venv

py -3 -c "%TESTE%" >nul 2>&1
if not errorlevel 1 set "PY_CMD=py -3"
if defined PY_CMD goto :create_venv

python -c "%TESTE%" >nul 2>&1
if not errorlevel 1 set "PY_CMD=python"
if defined PY_CMD goto :create_venv

if exist "%LOCAL_PY%" set PY_CMD="%LOCAL_PY%"
if defined PY_CMD goto :create_venv

call :bootstrap
if errorlevel 1 goto :py_error
set PY_CMD="%LOCAL_PY%"

:create_venv
echo [FitControl] A criar ambiente virtual (.venv)...
if exist ".venv" rmdir /s /q ".venv"
%PY_CMD% -m venv .venv
if not exist "%VENV_PY%" goto :venv_error

:deps
echo [FitControl] A instalar dependencias (pode demorar na 1a vez)...
if exist "%MARCA%" del /q "%MARCA%"
"%VENV_PY%" -m pip install --upgrade pip --disable-pip-version-check
"%VENV_PY%" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 goto :deps_error
copy /y requirements.txt "%MARCA%" >nul

:run
echo [FitControl] A iniciar a aplicacao...
"%VENV_PY%" run_gui.py
if errorlevel 1 goto :app_error
exit /b 0

:bootstrap
echo [FitControl] Python nao encontrado. A instalar Python %PY_VERSION% (so para este utilizador)...
set "INSTALADOR=%TEMP%\fitcontrol_python_installer.exe"
del /q "%INSTALADOR%" >nul 2>&1
curl -fsSL -o "%INSTALADOR%" "%PY_URL%"
if not exist "%INSTALADOR%" exit /b 1
echo [FitControl] A instalar, aguarde um momento...
start /wait "" "%INSTALADOR%" /quiet InstallAllUsers=0 TargetDir="%LOCALAPPDATA%\FitControl\Python312" PrependPath=0 Include_launcher=0 Shortcuts=0
del /q "%INSTALADOR%" >nul 2>&1
if not exist "%LOCAL_PY%" exit /b 1
exit /b 0

:py_error
echo.
echo [ERRO] Nao foi possivel instalar o Python automaticamente.
echo Instale o Python %PY_VERSION% (64 bits) de:
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
echo Verifique a ligacao a internet e volte a abrir o run.bat.
pause
exit /b 1

:app_error
echo.
echo [ERRO] A aplicacao terminou com erro (ver mensagens acima).
pause
exit /b 1
