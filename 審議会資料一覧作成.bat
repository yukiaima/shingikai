@echo on
setlocal
rem pythonソースコードのディレクトリへ移動
cd src

rem pythonコードを実行 
python 010_審議会資料リンク集作成.py

rem 元のディレクトリへ移動
cd ..

rem githubからpullとpush
git pull origin main && ^
git add . && ^
git commit -m "%DATE% %TIME% update" && ^
git push -u origin main  

exit /b 0
