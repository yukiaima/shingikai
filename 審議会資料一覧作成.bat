@echo on
setlocal
rem pythonソースコードのディレクトリへ移動
cd src

rem pythonコードを実行 ※終わったものは更新しない
python 100_需給調整市場検討小委員会.py
python 101_調整力の細分化及び広域調達の技術的検討に関する作業会.py
python 102_調整力及び需給バランス評価等に関する委員会.py
python 103_広域系統整備委員会.py
python 104_広域連系系統のマスタープラン及び系統利用ルールの在り方等に関する検討委員会.py
python 105_容量市場の在り方等に関する検討会・勉強会.py
python 106_地域間連系線及び地内送電系統の利用ルール等に関する検討会.py
python 107_グリッドコード検討会.py
rem python 108_電力レジリエンス等に関する小委員会.py
rem python 109_地内系統の混雑管理に関する勉強会.py
python 110_運用容量検討会.py
python 111_マージン検討会.py
python 112_将来の電力需給シナリオに関する検討会.py
python 113_将来の運用容量等の在り方に関する作業会.py
python 200_METI審議会.py
python 201_METI審議会（エネ庁）.py
rem python 300_制度設計専門会合.py
python 301_料金制度専門会合.py
rem python 302_電気料金審査専門会合.py
rem python 303_料金制度ワーキング・グループ.py
python 304_送配電効率化・計画進捗確認ワーキンググループ.py
rem python 305_送配電網の維持・運用費用の負担の在り方検討ワーキング・グループ.py
rem python 306_局地的電力需要増加と送配電ネットワークに関する研究会.py
python 307_制度設計・監視専門会合.py
python 308_長期脱炭素電源オークションにおける他市場収益の監視の在り方に関する検討会.py
python 400_GX実現に向けたカーボンプライシング専門ワーキンググループ.py
python 401_GX実行会議.py

rem 元のディレクトリへ移動
cd ..

rem githubからpullとpush
git pull origin main && ^
git add . && ^
git commit -m "%DATE% %TIME% update" && ^
git push -u origin main  

exit /b 0
