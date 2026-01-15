@echo off
chcp 65001 >nul
echo MRシステムを起動しています...

:: フロントエンドをC:\tempにコピー（日本語パス対策）
if not exist "C:\temp\frontend" (
    echo フロントエンドをコピー中...
    xcopy "%~dp0frontend" "C:\temp\frontend" /E /I /Y /Q
)

:: バックエンド起動
start cmd /k "cd /d "%~dp0backend" && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: フロントエンド起動（C:\temp\frontendから）
start cmd /k "cd /d C:\temp\frontend && npm run dev -- -H 0.0.0.0"

:: IPアドレスを取得
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do set IP=%%a
set IP=%IP: =%

echo.
echo ========================================
echo   MRシステムが起動しました
echo ========================================
echo.
echo   PC からアクセス:
echo     http://localhost:3000
echo.
echo   スマホからアクセス:
echo     http://%IP%:3000
echo.
echo ========================================
pause
