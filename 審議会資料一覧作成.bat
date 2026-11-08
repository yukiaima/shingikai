@echo off
setlocal
chcp 65001 >nul

echo [1/4] 最新の状態をGitHubから取得中...
git pull origin main
if %errorlevel% neq 0 (
    echo [エラー] git pull に失敗しました。競合が発生していないか確認してください。
    pause
    exit /b 1
)

echo [2/4] Pythonスクリプトを実行中...
cd src
python 010_審議会資料リンク集作成.py
if %errorlevel% neq 0 (
    echo [エラー] Pythonの実行中にエラーが発生しました。
    cd ..
    pause
    exit /b 1
)
cd ..

echo [3/4] 変更をステージング・コミット中...
git add .
git commit -m "Local update: %DATE% %TIME%"
:: 変更がない場合のコミットエラーを防ぐ処理を入れる場合はここで調整

echo [4/4] GitHubへプッシュ中...
git push origin main
if %errorlevel% neq 0 (
    echo [エラー] git push に失敗しました。
    pause
    exit /b 1
)

echo 処理が正常に完了しました。
pause
exit /b 0