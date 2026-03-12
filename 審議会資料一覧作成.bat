@echo on
setlocal
rem pythonソースコードのディレクトリへ移動
cd src

rem pythonコードを実行 ※終わったものは更新しない
python 200_METI審議会.py
python 201_METI審議会（エネ庁）.py
python 300_監視等委審議会.py
python 400_内閣府審議会.py

rem 元のディレクトリへ移動
cd ..

rem githubからpullとpush
git pull origin main && ^
git add . && ^
git commit -m "%DATE% %TIME% update" && ^
git push -u origin main  

exit /b 0
