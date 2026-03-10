import csv
import os
import time
from pathlib import Path
from urllib.parse import urljoin
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class MetiCommitteeScraper:
    # --- (既存の __init__, _setup_driver, get_soup, check_update, extract_papers, save_html はそのまま) ---
    def __init__(self, output_dir='../meti'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.driver = self._setup_driver()

    def _setup_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--disable-blink-features=AutomationControlled')
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        options.add_argument(f'user-agent={ua}')
        options.page_load_strategy = 'eager'
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        driver.set_page_load_timeout(30)
        return driver

    def get_soup(self, url, wait_time=0.8):
        try:
            self.driver.get(url)
            time.sleep(wait_time) 
            return bs4.BeautifulSoup(self.driver.page_source, 'lxml')
        except Exception:
            return bs4.BeautifulSoup(self.driver.page_source, 'lxml')

    def check_update(self, name, new_soup):
        file_path = self.output_dir / f"{name}.html"
        current_update_div = new_soup.find('div', {'id': '__rdo_update'})
        if not current_update_div: return True, "不明"
        update_text = current_update_div.get_text(strip=True)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding="utf-8") as f:
                    old_soup = bs4.BeautifulSoup(f, 'lxml')
                    old_update = old_soup.find('div', {'id': 'update'})
                    if old_update and update_text in old_update.get_text():
                        return False, update_text
            except: return True, update_text
        return True, update_text

    def extract_papers(self, soup, base_url):
        links = []
        seen_files = set()
        
        # 過去のコードで使われていた 'lnkLst' や 'main w1000' も含めて探索
        target_area = (
            soup.find('div', id=['__main_contents', 'main_contents']) or 
            soup.find('div', class_=['main', 'main w1000', 'contents']) or
            soup.find('article') or 
            soup
        )
        
        if target_area:
            # 過去のコードの ul class='lnkLst' 等の構造にも対応できるよう全てのaタグを精査
            for a in target_area.find_all('a', href=True):
                txt = a.get_text(strip=True)
                href = urljoin(base_url, a.get('href'))
                
                if not txt: continue
                
                # 過去のコードにあった除外条件「Adobeサイトへ」等を継承
                if "Adobe" in txt or "ダウンロード" in txt: continue
                # 回数リンクが重複してリストに入らないよう除外（既存ロジック）
                if "第" in txt and "回" in txt and not any(ext in href.lower() for ext in ['.pdf', '.xlsx']):
                    continue

                is_doc = any(ext in href.lower() for ext in ['.pdf', '.zip', '.xlsx', '.docx', '.pptx', '.csv'])
                is_yt = "youtube.com" in href.lower() or "youtu.be" in href.lower()

                if (is_doc or is_yt) and href not in seen_files:
                    label = f"{txt} (YouTube)" if is_yt else txt
                    links.append(f'<li><a href="{href}" target="_blank">{label}</a></li>')
                    seen_files.add(href)
        return links

    def process_committee(self, name, main_url, extra_urls=None):
        print(f"\n>>> 審議会開始: {name}")
        file_path = self.output_dir / f"{name}.html"
        soup = self.get_soup(main_url, wait_time=1.5)
        if not soup: return
        
        should_proceed, update_text = self.check_update(name, soup)
        if not should_proceed:
            print(f"    ※ 更新なし: スキップ（{update_text}）")
            return

        body_content = [f"<h1>{name}</h1>", f'<p><a href="{main_url}" target="_blank">>> 委員会公式サイト</a></p>', f'<div id="update"><p>最終更新確認日: {update_text}</p></div><hr>']
        all_sources = [main_url] + (extra_urls if extra_urls else [])
        seen_sub_urls = set()
        
        # 判定キーワード
        TARGET_KEYWORDS = ["第", "回", "中間", "報告", "結論", "需給", "対策", "整理", "まとめ", "戦略", "方針", "ロードマップ", "方向", "改革", "貫徹", "設計"]

        for target_url in all_sources:
            list_soup = self.get_soup(target_url)
            # 過去のコードにあった 'linkE', 'lnkLst' を持つ要素を広く探す
            main_area = (
                list_soup.find('div', id=['__main_contents', 'main_contents']) or 
                list_soup.find('div', class_=['main', 'main w1000']) or 
                list_soup
            )
            
            if not main_area: continue
            
            # 全てのaタグをチェック
            for a_tag in main_area.find_all('a', href=True):
                title = a_tag.get_text(strip=True)
                sub_url = urljoin(target_url, a_tag.get('href'))
                
                is_target = any(kw in title for kw in TARGET_KEYWORDS)
                
                if is_target and sub_url not in seen_sub_urls:
                    # サブページ(html)か、あるいは直接ファイルか
                    is_html = any(ext in sub_url.split('/')[-1] for ext in [".html", ".htm"]) or sub_url.endswith('/')
                    
                    if is_html:
                        print(f"    解析中: {title}")
                        sub_soup = self.get_soup(sub_url, wait_time=0.5)
                        if sub_soup:
                            paper_links = self.extract_papers(sub_soup, sub_url)
                            if paper_links:
                                body_content.append(f"<h2>{title}</h2><ul>{''.join(paper_links)}</ul>")
                        seen_sub_urls.add(sub_url)
                    elif any(ext in sub_url.lower() for ext in ['.pdf', '.zip', '.xlsx']):
                        # 直接リンクの場合
                        body_content.append(f'<h2>{title}</h2><ul><li><a href="{sub_url}" target="_blank">資料を開く</a></li></ul>')
                        seen_sub_urls.add(sub_url)
        
        self.save_html(file_path, name, "".join(body_content))
        print(f"    完了: {file_path.name}")

    def save_html(self, file_path, name, body):
        html = f"""<!DOCTYPE html><html lang="ja"><head><title>{name}</title><meta charset="UTF-8">
        <style>body{{font-family:sans-serif;line-height:1.6;padding:30px;max-width:1000px;margin:auto;color:#333;}}
        h1{{border-left:10px solid #005aad;padding-left:15px;font-size:24px;color:#005aad;}}
        h2{{border-bottom:2px solid #005aad;color:#005aad;margin-top:40px;font-size:18px;}}
        a{{color:#005aad;text-decoration:none;}}a:hover{{text-decoration:underline;}}</style>
        </head><body>{body}</body></html>"""
        with open(file_path, 'w', encoding='utf-8') as f: f.write(html)

    def close(self): self.driver.quit()

# --- メイン処理 ---
if __name__ == "__main__":
    csv_path = "committees_METI.csv"
    
    if not os.path.exists(csv_path):
        print(f"エラー: {csv_path} が見つかりません。")
    else:
        scraper = MetiCommitteeScraper()
        try:
            # newline='' はWindowsでの空行発生防止
            with open(csv_path, mode='r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # enabledフラグのチェック (1 の時だけ実行)
                    if row.get('enabled') != '1':
                        continue
                        
                    name = row['name']
                    main_url = row['main_url']
                    
                    # extra_url1 から extra_url5 までを収集
                    extra_urls = []
                    for i in range(1, 6):
                        col_name = f'extra_url{i}'
                        # 列が存在し、かつ値が空でない場合
                        url = row.get(col_name, "").strip()
                        if url:
                            extra_urls.append(url)
                    
                    scraper.process_committee(name, main_url, extra_urls)
        finally:
            scraper.close()
            print("\nすべて完了しました。")

 