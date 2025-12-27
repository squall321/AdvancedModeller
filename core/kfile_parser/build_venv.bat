@echo off
REM Build kfile_parser with venv Python and VS 2022

cd /d "%~dp0"

echo ===============================================
echo  Building kfile_parser (venv + VS 2022)
echo ===============================================
echo.

REM Setup Visual Studio environment
echo [1/4] Setting up Visual Studio 2022 environment...
call "D:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
if errorlevel 1 (
    echo [ERROR] Failed to setup VS environment
    pause
    exit /b 1
)

REM Activate venv
echo.
echo [2/4] Activating virtual environment...
call ..\..\venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] Failed to activate venv
    pause
    exit /b 1
)

echo.
echo [3/4] Installing pybind11...
python -m pip install pybind11 -q
if errorlevel 1 (
    echo [ERROR] Failed to install pybind11
    pause
    exit /b 1
)

echo.
echo [4/4] Building C++ extension...
python setup.py build_ext --inplace
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ===============================================
echo  Build Complete!
echo ===============================================
echo.

if exist kfile_parser\_kfile_parser*.pyd (
    echo Generated files:
    dir /b kfile_parser\_kfile_parser*.pyd
    echo.
    echo [SUCCESS] kfile_parser module built successfully!
) else (
    echo [WARNING] .pyd file was not created
)

echo.
echo Testing import...
python -c "from kfile_parser import KFileParser; print('[OK] Import successful')"

pause
