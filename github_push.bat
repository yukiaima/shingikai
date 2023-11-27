@echo on
cd C:\Users\Koichiro_ISHIKAWA\マイドライブ（k.isikawa48016@gmail.com）\010_プライベート\040_勉強・情報収集\010_プログラミングでの自動化\010_審議会資料一覧取得 && ^
git add . && ^
git commit -m "%DATE% %TIME% update" && ^
pause
git push -u origin main  && ^
pause
exit /b 0
