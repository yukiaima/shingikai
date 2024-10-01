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
python 200_電力・ガス基本政策小委員会.py
python 201_制度検討作業部会.py
python 202_ガス事業制度検討ワーキンググループ.py
python 203_再生可能エネルギー大量導入・次世代電力ネットワーク小委員会.py
rem python 204_持続可能な電力システム構築小委員会.py
python 205_系統ワーキンググループ.py
rem python 206_あるべき卸電力市場、需給調整市場及び需給運用の実現に向けた実務検討作業部会.py
rem python 207_卸電力市場、需給調整市場及び需給運用の在り方勉強会.py
python 208_石油・天然ガス小委員会.py
python 209_水素政策小委員会.py
python 210_アンモニア等脱炭素燃料政策小委員会.py
python 211_電力広域的運営推進機関検証ワーキンググループ.py 
python 212_次世代の分散型電力システムに関する検討会.py 
rem python 213_将来の電力需給に関する在り方勉強会.py
python 214_同時市場の在り方等に関する検討会.py
rem python 300_制度設計専門会合.py
python 301_料金制度専門会合.py
rem python 302_電気料金審査専門会合.py
rem python 303_料金制度ワーキング・グループ.py
python 304_送配電効率化・計画進捗確認ワーキンググループ.py
rem python 305_送配電網の維持・運用費用の負担の在り方検討ワーキング・グループ.py
rem python 306_局地的電力需要増加と送配電ネットワークに関する研究会.py
python 307_制度設計・監視専門会合.py
python 900_博士人材の産業界への入職経路の多様化に関する勉強会.py

rem 元のディレクトリへ移動
cd ..

rem githubへpush
git add . && ^
git commit -m "%DATE% %TIME% update" && ^
git push -u origin main  

exit /b 0
