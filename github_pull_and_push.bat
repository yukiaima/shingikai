@echo on
git pull origin main && ^     :: GitHubから最新の変更をプル
git add . && ^                :: ステージングエリアに変更を追加
git commit -m "%DATE% %TIME% update" && ^  :: 現在の日付と時刻を含むコミット
git push -u origin main && ^  :: リモートに変更をプッシュ
pause                         :: 結果を確認するために一時停止
exit /b 0                     :: スクリプトの終了
