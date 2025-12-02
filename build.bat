@echo off
chcp 65001 > nul
echo === KooMesh Modeller Build ===

cd /d "%~dp0"

call venv\Scripts\activate

pip install pyinstaller -q

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller ^
    --onefile ^
    --windowed ^
    --name KooMeshModeller ^
    --add-data "config;config" ^
    --hidden-import gui.modules.advanced_laminate ^
    --hidden-import gui.modules.advanced_contact ^
    gui/main.py

echo.
echo === Build Complete ===
echo Executable: dist\KooMeshModeller.exe
pause
