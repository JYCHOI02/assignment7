@echo off
chcp 65001 > nul
echo ========================================================
echo  ngrok 고정 도메인 터널 실행
echo  도메인: https://cable-badly-blast.ngrok-free.dev
echo  포트: 5000 (플랜두씨 다이어리)
echo ========================================================
"C:\Users\user\AppData\Local\ngrok\ngrok.exe" http --url=cable-badly-blast.ngrok-free.dev 5000
pause
