import csv
import os
import time
import logging  # 追加
from datetime import datetime  # 追加
from pathlib import Path
from urllib.parse import urljoin
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class CasCommitteeScraper:
    def __init__(self, output_dir='../cas'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # --- ログの設定（追記形式） ---
        self.log_dir = Path('log')
        self.log_dir.mkdir(exist_ok=True)
        log_file = self.log_dir / "latest_log.txt"
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # 二重出力を防ぐためのハンドラクリア
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        
        # 1. ファイル出力用 (fh: File Handler)
        fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        fh.setFormatter(formatter)
        
        # 2. コンソール出力用 (ch: Console Handler) ← ここが漏れていました
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        
        # 両方のハンドラを追加することで、ファイルと画面の両方にログが出るようになります
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # 区切り線を入れて開始
        self.logger.info("\n" + "="*50)
        self.logger.info(f"実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*50)
        # ----------------

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

    def process_committee_cas(self, name, url):
        self.logger.info(f"開始: {name}")
        file_path = self.output_dir / f"{name}.html"
        current_url = url
        try:
            self.driver.get(current_url)
            time.sleep(3)
            
            if "index.html" in current_url:
                soup_home = bs4.BeautifulSoup(self.driver.page_source, 'lxml')
                link = soup_home.find('a', string=lambda x: x and ('開催状況' in x or '開催実績' in x))
                if link:
                    current_url = urljoin(current_url, link.get('href'))
                    self.driver.get(current_url)
                    time.sleep(2)

            soup = bs4.BeautifulSoup(self.driver.page_source, 'lxml')
            table = soup.find('table', class_=lambda x: x and 'tbl_giji' in x)
            
            if not table:
                self.logger.warning(f"{name}: 開催実績テーブルが見つかりません。")
                return

            # --- body（中身）の構築を開始 ---
            # 冒頭にタイトルと公式ページへのリンクを挿入
            html_body = f'<h1>{name}</h1>'
            html_body += f'<p><a href="{url}" target="_blank">⇒ 公式委員会ページはこちら</a></p>'
            
            rows = table.find_all('tr')
            # 降順にするために reversed を使用
            for tr in reversed(rows):
                tds = tr.find_all('td')
                if len(tds) < 3: continue
                
                link_td = None
                for td in tds:
                    if td.find('a', string=lambda x: x and '資料' in x):
                        link_td = td
                        break
                
                if not link_td or not link_td.a: continue
                
                title = tds[0].get_text(strip=True) + " " + tds[1].get_text(strip=True)
                papers_url = urljoin(current_url, link_td.a.get('href'))
                
                self.logger.info(f"  詳細取得中: {title}")
                self.driver.get(papers_url)
                time.sleep(1)
                soup_sub = bs4.BeautifulSoup(self.driver.page_source, 'lxml')
                
                html_body += f"<h2>{title}</h2><ul>"
                sub_table = soup_sub.find('table', class_=lambda x: x and 'tbl_giji' in x)
                if sub_table:
                    for tr2 in sub_table.find_all('tr'):
                        if tr2.a:
                            link_text = tr2.get_text(strip=True)
                            link_url = urljoin(papers_url, tr2.a.get('href'))
                            html_body += f'<li><a href="{link_url}" target="_blank">{link_text}</a></li>'
                html_body += "</ul>"

            # 200番台と同じ形式で呼び出し
            self.save_html(file_path, name, html_body)
            self.logger.info(f"    完了: {file_path.name}")
            
        except Exception as e:
            self.logger.error(f"{name} でエラー発生: {e}")
    
    def save_html(self, file_path, name, body):
        html = f"""<!DOCTYPE html><html lang="ja"><head><title>{name}</title><meta charset="UTF-8">
        <style>body{{font-family:sans-serif;line-height:1.6;padding:30px;max-width:1000px;margin:auto;color:#333;}}
        h1{{border-left:10px solid #005aad;padding-left:15px;font-size:24px;color:#005aad;}}
        h2{{border-bottom:2px solid #005aad;color:#005aad;margin-top:40px;font-size:18px;}}
        a{{color:#005aad;text-decoration:none;}}a:hover{{text-decoration:underline;}}</style>
        </head><body>{body}</body></html>"""
        with open(file_path, 'w', encoding='utf-8') as f: f.write(html)

    def close(self):
        self.logger.info("WebDriverを終了します。")
        self.driver.quit()

if __name__ == "__main__":
    csv_path = "committees_内閣府.csv"
    
    if not os.path.exists(csv_path):
        print(f"エラー: {csv_path} が見つかりません。")
    else:
        scraper = CasCommitteeScraper()
        try:
            with open(csv_path, mode='r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('enabled') != '1':
                        continue
                        
                    name = row['name']
                    main_url = row['main_url']
                    
                    scraper.process_committee_cas(name, main_url)
        finally:
            scraper.close()
            # メイン処理の終了ログはscraper.loggerを通じて出すか、直接print
            print("\nすべて完了しました。詳細は log フォルダを確認してください。")
            