# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# 次世代電力・ガス事業基盤構築小委員会の関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -*- coding: utf-8 -*-
import os
from pathlib import Path
from urllib.parse import urljoin
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_COMMITTEE = '次世代電力・ガス事業基盤構築小委員会'
URL_COMMITTEE = 'https://www.meti.go.jp/shingikai/enecho/denryoku_gas/jisedai_kiban/index.html'
DIR_OUTPUT = Path('../meti')
FILE_PATH = DIR_OUTPUT / f"{NAME_COMMITTEE}.html"

# -----------------------------------
# メイン処理
# -----------------------------------
def main():
    # ディレクトリ作成
    DIR_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Selenium設定
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    # ドライバー起動（お手元の動く方式を維持）
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)

    try:
        # 親ページ取得
        driver.get(URL_COMMITTEE)
        soup = bs4.BeautifulSoup(driver.page_source, 'lxml')

        # 更新確認
        current_update = soup.find('div', {'id': '__rdo_update'})
        update_text = current_update.get_text(strip=True) if current_update else "不明"

        if FILE_PATH.exists():
            with open(FILE_PATH, 'r', encoding="utf-8") as f:
                soup_old = bs4.BeautifulSoup(f, 'lxml')
                old_update = soup_old.find('div', {'id': 'update'})
                if old_update and old_update.get_text(strip=True) == update_text:
                    print("更新がないため、処理を終了します。")
                    return

        # HTML生成開始（スタイルを少しだけ整えています）
        body_content = [
            f"<h1>{NAME_COMMITTEE}</h1>",
            f'<a href="{URL_COMMITTEE}" target="_blank">委員会ページ</a>',
            f'<div id="update"><p>最終更新: {update_text}</p></div><hr>'
        ]

        # 各開催回のリストを取得
        main_area = soup.find('div', {'id': '__main_contents'})
        # METIの構造上、複数のulにまたがることがあるため全て取得
        links = main_area.find_all('ul', class_=['linkE', 'lnkLst', 'linkE clearfix mb0'])

        target_links = []
        for ul in links:
            for li in ul.find_all('li'):
                if li.a:
                    target_links.append({
                        'title': li.get_text(strip=True),
                        'url': urljoin(URL_COMMITTEE, li.a.get('href'))
                    })

        for item in target_links:
            print(f"取得中: {item['title']}")
            driver.get(item['url'])
            soup_papers = bs4.BeautifulSoup(driver.page_source, 'lxml')

            paper_items = []
            # 個別ページの資料リストを取得
            sub_main = soup_papers.find('div', class_='main')
            if sub_main:
                paper_lists = sub_main.find_all('ul', class_='lnkLst')
                for p_ul in paper_lists:
                    for p_li in p_ul.find_all('li'):
                        if not p_li.a: continue
                        text = p_li.a.get_text(strip=True)
                        if "Adobe" in text or not text: continue
                        
                        absolute_href = urljoin(item['url'], p_li.a.get('href'))
                        paper_items.append(f'<li><a href="{absolute_href}" target="_blank">{text}</a></li>')

            # 開催回ごとのセクションを追加
            section = f"<h2>{item['title']}</h2><ul>{''.join(paper_items)}</ul>"
            body_content.append(section)

        # 最終HTMLの組み立て
        full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<title>{NAME_COMMITTEE}</title>
<meta charset="UTF-8">
<style>
    body {{ font-family: sans-serif; line-height: 1.6; padding: 20px; }}
    h2 {{ border-bottom: 2px solid #005aad; color: #005aad; margin-top: 30px; }}
    li {{ margin-bottom: 5px; }}
</style>
</head>
<body>{"".join(body_content)}</body>
</html>"""

        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"完了しました。出力先: {FILE_PATH}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
