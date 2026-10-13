@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title FitControl - criar executavel

rem o executavel fica numa pasta separada, ao lado do projeto
set "DESTINO=%~dp0..\..\FitControl"
set "PY=.venv\Scripts\python.exe"
set "TRABALHO=%TEMP%\fitcontrol_build"
set "REGISTO=%~dp0construcao.log"

if not exist "%PY%" (
    echo [FitControl] Corre primeiro o run.bat para preparar o ambiente.
    pause
    exit /b 1
)

echo [FitControl] A preparar o PyInstaller...
"%PY%" -m pip install --upgrade pyinstaller --disable-pip-version-check > "%REGISTO%" 2>&1
if errorlevel 1 goto :erro

echo [FitControl] A criar o executavel (demora uns minutos)...
"%PY%" -m PyInstaller --noconfirm --clean --log-level WARN --distpath "%TRABALHO%\dist" --workpath "%TRABALHO%\work" empacotar\FitControl.spec >> "%REGISTO%" 2>&1
if errorlevel 1 goto :erro

rem copia para o destino sem apagar os dados (pasta dados) de quem ja usa
robocopy "%TRABALHO%\dist\FitControl" "%DESTINO%" /MIR /XD dados /XF fitcontrol.log /NFL /NDL /NJH /NJS /NP >> "%REGISTO%" 2>&1
if errorlevel 8 goto :erro

echo CONCLUIDO >> "%REGISTO%"
echo.
echo [FitControl] Pronto: %DESTINO%\FitControl.exe
exit /b 0

:erro
echo FALHOU >> "%REGISTO%"
echo.
echo [ERRO] Falhou. Ver %REGISTO%
pause
exit /b 1
