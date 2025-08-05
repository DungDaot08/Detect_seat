@echo off
REM === Cấu hình thông tin kết nối PostgreSQL ===
set HOST=dpg-d1r60amr433s739telgg-a.oregon-postgres.render.com
set PORT=5432
set USER=detect_seat_user
set DB=detect_seat
set PASSWORD=ixRpspwrkGkn4ylMjo222PIDFrVJghfD
set BACKUP_PATH=D:\HG.backup

REM === Đường dẫn tới pg_dump (PostgreSQL 15) ===
set PG_DUMP="C:\Program Files\PostgreSQL\16\pgAdmin 4\runtime\pg_dump.exe"

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
