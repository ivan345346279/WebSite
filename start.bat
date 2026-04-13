@echo off
chcp 65001 >nul
cd ai_chat_web
title AI Chat Web Server
echo.
echo ╔════════════════════════════════════════╗
echo ║   🚀 AI Chat Web Server - Запуск      ║
echo ╚════════════════════════════════════════╝
echo.
echo 📦 Установка зависимостей...
pip install -r requirements.txt -q
echo.
echo 🌐 Запуск сервера на http://localhost:5000
echo.
echo ⚡ Нажми Ctrl+C для остановки
echo.
python server.py
pause
