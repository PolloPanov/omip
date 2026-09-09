@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo ==========================================
echo       GRAFICAS HISTORICAS OMIP
echo ==========================================
echo.
echo 1 - Ultimos 30 dias
echo 2 - Un mes concreto
echo 3 - Salir
echo.
set /p OPCION=Elige una opcion: 

echo.
if "%OPCION%"=="1" goto TREINTA
if "%OPCION%"=="2" goto MES
if "%OPCION%"=="3" goto FIN

echo Opcion no valida.
pause
goto FIN

:TREINTA
echo Generando grafica de los ultimos 30 dias...
echo.
"%PYTHON%" historico_omip.py --30-dias
echo.
pause
goto FIN

:MES
set /p ANIO=Introduce el ano (ej. 2026): 
set /p MES=Introduce el mes (1-12): 
echo.
echo Generando grafica de %MES%/%ANIO%...
echo.
"%PYTHON%" historico_omip.py --mes %ANIO% %MES%
echo.
pause
goto FIN

:FIN
endlocal
