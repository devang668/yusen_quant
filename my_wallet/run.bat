@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
pip install flask flask-cors -q
python app.py
pause
