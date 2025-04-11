@echo on
git pull origin main && ^
git add . && ^
git commit -m "%DATE% %TIME% update" && ^
git push -u origin main  && ^
pause
exit /b 0
