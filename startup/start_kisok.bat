@echo off

:: Chạy backend ở cửa sổ mới
::cd /d "C:\Users\CNCN\OneDrive\Desktop\Backend\Detect_seat"
::start "" cmd /c ""C:\Users\CNCN\AppData\Local\Programs\Python\Python39\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: Chờ 5 giây cho backend khởi động
::timeout /t 10 >nul

:: Chạy frontend ở cửa sổ mới
::cd /d "C:\Users\CNCN\OneDrive\Desktop\LaySoTuDong\LSTD_AUTOTICKET"
::start "" cmd /c "npm run dev"

:: Chờ frontend khởi động
timeout /t 30 >nul

:: Mở trình duyệt truy cập frontend
start chrome --start-fullscreen --test-type http://localhost:3000/
