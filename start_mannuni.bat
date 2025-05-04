@echo off
title Launch Mannuni - WhatsApp Bot
echo.
echo 🚀 Starting Flask Server...
start cmd /k "cd /d D:\MANNUNI && python app.py"

timeout /t 5

echo 🚀 Starting Ngrok Tunnel...
start cmd /k "cd /d D:\MANNUNI && ngrok http 5000"

echo.
echo ✅ All services started. Open your browser at http://localhost:5000
pause
