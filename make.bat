@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  Directory Tree Viewer - Build System
::  Usage: make.bat [command]
::
::  Python resolution order:
::    1. py -3.12 (system Python 3.12) -> venv
::    2. conda (Anaconda/Miniconda)     -> conda env
::    3. Neither found                  -> error
:: ============================================================

set APP_NAME=DirectoryTree
set ENTRY=src\directory_tree\main.py
set ICON=assets\app.ico
set VENV_DIR=.venv
set CONDA_ENV_NAME=directory_tree

:: ---- Detect Python environment ----
set ENV_MODE=
set CONDA_CMD=

:: Try 1: system Python 3.12
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set ENV_MODE=venv
    goto :env_resolved
)

:: Try 2: conda
where conda >nul 2>&1
if not errorlevel 1 (
    set ENV_MODE=conda
    set CONDA_CMD=conda
    goto :env_resolved
)

:: Try 2b: conda not in PATH, check common locations
for %%P in (
    "%USERPROFILE%\anaconda3\condabin\conda.bat"
    "%USERPROFILE%\miniconda3\condabin\conda.bat"
    "%ProgramData%\anaconda3\condabin\conda.bat"
    "%ProgramData%\miniconda3\condabin\conda.bat"
) do (
    if exist %%P (
        set ENV_MODE=conda
        set CONDA_CMD=%%~P
        goto :env_resolved
    )
)

:: Nothing found - but allow help/clean without Python
if /i "%~1"=="help"  goto help
if /i "%~1"=="clean" goto clean
if /i "%~1"==""      goto help

echo.
echo  [ERROR] Python 3.12 or Anaconda/Miniconda not found!
echo.
echo  Install one of the following:
echo    Option A: Python 3.12  https://www.python.org/downloads/
echo              (check "Add to PATH" + "py launcher" during install)
echo    Option B: Anaconda     https://www.anaconda.com/download
echo              (or Miniconda: https://docs.conda.io/en/latest/miniconda.html)
echo.
exit /b 1

:env_resolved

:: ---- Set environment-specific paths ----
if "%ENV_MODE%"=="venv" (
    set ENV_PYTHON=%VENV_DIR%\Scripts\python.exe
    set ENV_PIP=%VENV_DIR%\Scripts\pip.exe
    set ENV_LABEL=venv (Python 3.12)
    set ENV_ACTIVATE=%VENV_DIR%\Scripts\activate
) else (
    for /f "tokens=*" %%i in ('call %CONDA_CMD% info --base 2^>nul') do set CONDA_ROOT=%%i
    set ENV_PYTHON=!CONDA_ROOT!\envs\%CONDA_ENV_NAME%\python.exe
    set ENV_LABEL=conda (%CONDA_ENV_NAME%)
    set ENV_ACTIVATE=conda activate %CONDA_ENV_NAME%
)

:: ---- Route to command ----
if "%~1"=="" goto help

if /i "%~1"=="setup"   goto setup
if /i "%~1"=="run"     goto run
if /i "%~1"=="build"   goto build
if /i "%~1"=="clean"   goto clean
if /i "%~1"=="rebuild" goto rebuild
if /i "%~1"=="freeze"  goto freeze
if /i "%~1"=="nuke"    goto nuke
if /i "%~1"=="info"    goto info
if /i "%~1"=="help"    goto help

echo [ERROR] Unknown command: %~1
goto help

:: ============================================================
::  setup
:: ============================================================
:setup
echo.
echo [SETUP] Mode: %ENV_LABEL%
echo.

if "%ENV_MODE%"=="venv" (
    echo [1/3] Creating virtual environment...
    py -3.12 -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        exit /b 1
    )

    echo [2/3] Upgrading pip...
    %ENV_PYTHON% -m pip install --upgrade pip --quiet

    echo [3/3] Installing dependencies...
    if exist requirements-dev.txt (
        %ENV_PIP% install -r requirements-dev.txt --quiet
    ) else if exist requirements.txt (
        %ENV_PIP% install -r requirements.txt --quiet
        %ENV_PIP% install "pyinstaller>=6.0" --quiet
    ) else (
        %ENV_PIP% install "pyinstaller>=6.0" --quiet
    )
) else (
    echo [1/3] Creating conda environment...
    call %CONDA_CMD% create -n %CONDA_ENV_NAME% python=3.12 -y --quiet
    if errorlevel 1 (
        echo [ERROR] Failed to create conda environment.
        exit /b 1
    )

    echo [2/3] Upgrading pip...
    call %CONDA_CMD% run -n %CONDA_ENV_NAME% pip install --upgrade pip --quiet

    echo [3/3] Installing dependencies...
    if exist requirements-dev.txt (
        call %CONDA_CMD% run -n %CONDA_ENV_NAME% pip install -r requirements-dev.txt --quiet
    ) else if exist requirements.txt (
        call %CONDA_CMD% run -n %CONDA_ENV_NAME% pip install -r requirements.txt --quiet
        call %CONDA_CMD% run -n %CONDA_ENV_NAME% pip install "pyinstaller>=6.0" --quiet
    ) else (
        call %CONDA_CMD% run -n %CONDA_ENV_NAME% pip install "pyinstaller>=6.0" --quiet
    )
)

echo.
echo ============================================================
echo [OK] Setup complete!  (%ENV_LABEL%)
echo      Activate:  %ENV_ACTIVATE%
echo      Or just:   make.bat run / make.bat build
echo ============================================================
goto :eof

:: ============================================================
::  run
:: ============================================================
:run
call :check_env
if errorlevel 1 exit /b 1

echo [RUN] Starting Directory Tree Viewer...  (%ENV_LABEL%)
if "%ENV_MODE%"=="venv" (
    %ENV_PYTHON% %ENTRY%
) else (
    call %CONDA_CMD% run -n %CONDA_ENV_NAME% python %ENTRY%
)
goto :eof

:: ============================================================
::  build
:: ============================================================
:build
call :check_env
if errorlevel 1 exit /b 1

echo.
echo [BUILD] Building %APP_NAME%.exe ...  (%ENV_LABEL%)
echo.

set ICON_FLAG=
if exist %ICON% set ICON_FLAG=--icon=%ICON%

if "%ENV_MODE%"=="venv" (
    if exist %APP_NAME%.spec (
        %ENV_PYTHON% -m PyInstaller %APP_NAME%.spec --clean --noconfirm
    ) else (
        %ENV_PYTHON% -m PyInstaller ^
            --name %APP_NAME% ^
            --onefile ^
            --windowed ^
            --paths=src ^
            !ICON_FLAG! ^
            --clean ^
            --noconfirm ^
            %ENTRY%
    )
) else (
    if exist %APP_NAME%.spec (
        call %CONDA_CMD% run -n %CONDA_ENV_NAME% python -m PyInstaller %APP_NAME%.spec --clean --noconfirm
    ) else (
        call %CONDA_CMD% run -n %CONDA_ENV_NAME% python -m PyInstaller ^
            --name %APP_NAME% ^
            --onefile ^
            --windowed ^
            !ICON_FLAG! ^
            --clean ^
            --noconfirm ^
            %ENTRY%
    )
)

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    exit /b 1
)

echo.
echo ============================================================
echo [OK] Build successful!
echo      Output: dist\%APP_NAME%.exe
for %%F in (dist\%APP_NAME%.exe) do echo      Size:   %%~zF bytes
echo ============================================================
goto :eof

:: ============================================================
::  rebuild
:: ============================================================
:rebuild
call :clean
call :build
goto :eof

:: ============================================================
::  clean
:: ============================================================
:clean
echo [CLEAN] Removing build artifacts...
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
for /r %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"
echo [OK] Clean complete.
goto :eof

:: ============================================================
::  nuke - Remove the environment entirely
:: ============================================================
:nuke
echo.
if "%ENV_MODE%"=="venv" (
    if exist %VENV_DIR% (
        echo [NUKE] Removing .venv ...
        rmdir /s /q %VENV_DIR%
        echo [OK] .venv removed.
    ) else (
        echo [INFO] .venv not found, nothing to remove.
    )
) else (
    echo [NUKE] Removing conda env "%CONDA_ENV_NAME%" ...
    call %CONDA_CMD% remove -n %CONDA_ENV_NAME% --all -y
    echo [OK] Conda environment removed.
)
goto :eof

:: ============================================================
::  freeze
:: ============================================================
:freeze
call :check_env
if errorlevel 1 exit /b 1

if "%ENV_MODE%"=="venv" (
    %ENV_PIP% freeze > requirements.txt
) else (
    call %CONDA_CMD% run -n %CONDA_ENV_NAME% pip freeze > requirements.txt
)
echo [OK] requirements.txt updated.
goto :eof

:: ============================================================
::  info - Show detected environment info
:: ============================================================
:info
echo.
echo  Environment Info
echo  ================
echo  Mode:      %ENV_LABEL%
if "%ENV_MODE%"=="venv" (
    echo  Python:    %ENV_PYTHON%
    if exist "%ENV_PYTHON%" (
        %ENV_PYTHON% --version
    ) else (
        echo  Status:    NOT CREATED (run: make.bat setup)
    )
) else (
    echo  Conda:     %CONDA_CMD%
    echo  Env name:  %CONDA_ENV_NAME%
    if exist "!ENV_PYTHON!" (
        call %CONDA_CMD% run -n %CONDA_ENV_NAME% python --version
    ) else (
        echo  Status:    NOT CREATED (run: make.bat setup)
    )
)
echo.
goto :eof

:: ============================================================
::  help
:: ============================================================
:help
echo.
echo  Directory Tree Viewer - Build System
echo  =====================================
echo.
echo  Usage: make.bat [command]
echo.
echo  Commands:
echo    setup     Create environment (Python 3.12) + install dependencies
echo    run       Run the application
echo    build     Build single .exe with PyInstaller
echo    rebuild   Clean + Build
echo    clean     Remove build artifacts (build/, dist/)
echo    nuke      Remove environment entirely (venv or conda)
echo    freeze    Export pip packages to requirements.txt
echo    info      Show detected environment info
echo    help      Show this message
echo.
echo  Python resolution: py -3.12 (venv) ^> conda (env) ^> error
echo.
goto :eof

:: ============================================================
::  Utility: check if environment exists
:: ============================================================
:check_env
if "%ENV_MODE%"=="venv" (
    if not exist "%ENV_PYTHON%" (
        echo [ERROR] venv not found. Run: make.bat setup
        exit /b 1
    )
) else (
    if not exist "!ENV_PYTHON!" (
        echo [ERROR] Conda env "%CONDA_ENV_NAME%" not found. Run: make.bat setup
        exit /b 1
    )
)
exit /b 0
