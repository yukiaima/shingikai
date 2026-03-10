# -*- coding: utf-8 -*-
"""
Created on 2024 (Updated)
次世代電力・ガス事業基盤構築小委員会の関係資料一覧のhtml作成
"""
import os
import time
from pathlib import Path
from urllib.parse import urljoin
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

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
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)

    try:
        # 1. 親ページ取得
        print(f"アクセス中: {URL_COMMITTEE}")
        driver.get(URL_COMMITTEE)
        soup = bs4.BeautifulSoup(driver.page_source, 'lxml')

        # 更新確認
        current_update = soup.find('div', {'id': '__rdo_update'})
        update_text = current_update.get_text(strip=True) if current_update else "不明"

        if FILE_PATH.exists():
            with open(FILE_PATH, 'r', encoding="utf-8") as f:
                soup_old = bs4.BeautifulSoup(f, 'lxml')
                old_update = soup_old.find('div', {'id': 'update'})
                if old_update and update_text in old_update.get_text():
                    print(f"更新がないため（{update_text}）、処理を終了します。")
                    return

        # HTML生成用リスト
        body_content = [
            f"<h1>{NAME_COMMITTEE}</h1>",
            f'<p><a href="{URL_COMMITTEE}" target="_blank">>> 委員会公式サイトへ</a></p>',
            f'<div id="update"><p>最終更新確認日: {update_text}</p></div><hr>'
        ]

        # 2. 各開催回のURLを抽出
        main_area = soup.find('div', {'id': '__main_contents'})
        if not main_area:
            print("メインコンテンツが見つかりませんでした。")
            return

        # 開催回へのリンクをすべて取得（METIの特有の構造に対応）
        target_links = []
        for a_tag in main_area.find_all('a', href=True):
            href = a_tag.get('href')
            title = a_tag.get_text(strip=True)
            # 「第〇回」などの文字が含まれるリンクを対象にする
            if "第" in title and "回" in title:
                target_links.append({
                    'title': title,
                    'url': urljoin(URL_COMMITTEE, href)
                })

        # 3. 各開催回の個別ページを巡回
        for item in target_links:
            print(f"解析中: {item['title']}")
            try:
                driver.get(item['url'])
                # 読み込み待ち（動的コンテンツ対策）
                time.sleep(1) 
                soup_papers = bs4.BeautifulSoup(driver.page_source, 'lxml')

                paper_items = []
                seen_urls = set() # 重複リンク排除用

                # 個別ページのメインエリアを特定
                sub_main = soup_papers.find('div', id='__main_contents') or \
                           soup_papers.find('div', class_='main') or \
                           soup_papers.find('main')

                if sub_main:
                    # PDF、Excel、Wordなどの資料リンクを網羅的に探す
                    for p_a in sub_main.find_all('a', href=True):
                        link_text = p_a.get_text(strip=True)
                        link_url = urljoin(item['url'], p_a.get('href'))

                        # 不要なリンクをスキップ
                        if not link_text or "Adobe" in link_text or link_url in seen_urls:
                            continue
                        
                        # 資料らしいリンク（拡張子やパスで判断）をリストへ
                        if any(ext in link_url.lower() for ext in ['.pdf', '.zip', '.xlsx', '.docx', '/pdf/']):
                            paper_items.append(f'<li><a href="{link_url}" target="_blank">{link_text}</a></li>')
                            seen_urls.add(link_url)

                # 開催回ごとのセクションを追加
                if paper_items:
                    section = f"<h2>{item['title']}</h2><ul>{''.join(paper_items)}</ul>"
                    body_content.append(section)
                else:
                    body_content.append(f"<h2>{item['title']}</h2><p>資料が見つかりませんでした。</p>")

            except Exception as e:
                print(f"エラー発生 ({item['title']}): {e}")
                continue

        # 4. 最終HTMLの組み立て
        full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <title>{NAME_COMMITTEE} - 資料一覧</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif; line-height: 1.6; padding: 30px; max-width: 900px; margin: auto; color: #333; }}
        h1 {{ border-left: 8px solid #005aad; padding-left: 15px; font-size: 24px; }}
        h2 {{ border-bottom: 2px solid #005aad; color: #005aad; margin-top: 40px; font-size: 20px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
        a {{ color: #005aad; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        #update {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>{"".join(body_content)}</body>
</html>"""

        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"\n--- 完了 ---\n出力先: {FILE_PATH.absolute()}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    