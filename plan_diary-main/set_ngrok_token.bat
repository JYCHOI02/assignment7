@echo off
chcp 65001 > nul
echo ========================================================
echo  ngrok AuthToken 등록 유틸리티
echo  (https://dashboard.ngrok.com/get-started/your-authtoken)
echo ========================================================
set /p TOKEN="ngrok 대시보드의 Authtoken을 붙여넣고 엔터를 누르세요: "
if "%TOKEN%"=="" (
    echo 토큰이 입력되지 않았습니다.
    pause
    exit /b
)

set NGROK_CMD=ngrok
if exist "%LOCALAPPDATA%\ngrok\ngrok.exe" (
    set NGROK_CMD="%LOCALAPPDATA%\ngrok\ngrok.exe"
)

%NGROK_CMD% config add-authtoken %TOKEN%
echo.
echo [완료] ngrok 토큰이 정상적으로 등록되었습니다!
echo 이제 app.py를 실행하거나 start_ngrok.bat을 실행하시면 됩니다.
echo.
pause
