@echo off
REM === Cấu hình thông tin kết nối PostgreSQL ===
set HOST=dpg-d2ot633ipnbc73a7ivgg-a.oregon-postgres.render.com
set PORT=5432
set USER=lstd
set DB=lstd_dz27
set PASSWORD=DMYteWaJh8kAHhGXw6FAwp5lqnKSIs8A
set BACKUP_PATH=D:\HG.backup

REM === Đường dẫn tới pg_dump (PostgreSQL 15) ===
set PG_DUMP="C:\Program Files\PostgreSQL\17\pgAdmin 4\runtime\pg_dump.exe"

REM === Xuất biến môi trường PGPASSWORD để tự động đăng nhập ===
set PGPASSWORD=%PASSWORD%

REM === Thực hiện backup ===
%PG_DUMP% ^
  --host=%HOST% ^
  --port=%PORT% ^
  --username=%USER% ^
  --file="%BACKUP_PATH%" ^
  --format=c ^
  --blobs ^
  --verbose ^
  %DB%

REM === Dọn dẹp biến môi trường để tránh rò rỉ thông tin ===
set PGPASSWORD=

echo ✅ Backup hoàn tất: %BACKUP_PATH%
pause
