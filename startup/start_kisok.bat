@echo off

:: Chờ frontend khởi động
timeout /t 30 >nul

:: Mở trình duyệt truy cập frontend
start chrome --start-fullscreen --test-type http://localhost:3000/
