@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python -m gui.main
