import csv
import os
import time
import logging  # 追加
from datetime import datetime  # 追加
from pathlib import Path
from urllib.parse import urljoin, urlparse
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class MetiCommitteeScraper:
    def __init__(self, output_dir='../meti'):
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

    def get_soup(self, url, wait_time=0.8):
        try:
            self.driver.get(url)
            time.sleep(wait_time) 
            return bs4.BeautifulSoup(self.driver.page_source, 'lxml')
        except Exception as e:
            self.logger.warning(f"ページ取得失敗: {url} ({e})")
            return bs4.BeautifulSoup(self.driver.page_source, 'lxml')

    def extract_papers_enecho(self, soup, base_url):
        """配布資料ページ等からPDFや動画リンクを抽出"""
        links = []
        seen = set()
        # 探したいリンクの条件
        for a in soup.find_all('a', href=True):
            href = urljoin(base_url, a.get('href'))
            text = a.get_text(strip=True)
            if not text or "戻る" in text: continue
            
            is_doc = any(ext in href.lower() for ext in ['.pdf', '.zip', '.xlsx', '.docx', '.pptx'])
            is_yt = any(kw in href.lower() for kw in ["youtube.com", "youtu.be", "metilive"])
            
            if (is_doc or is_yt) and href not in seen:
                label = f"{text} (動画)" if is_yt else text
                links.append(f'<li><a href="{href}" target="_blank">{label}</a></li>')
                seen.add(href)
        return links

    def process_committee_enecho(self, name, main_url):
        self.logger.info(f"審議会開始: {name}") # loggerに変更
        file_path = self.output_dir / f"{name}.html"
        parsed_url = urlparse(main_url)
        anchor_id = parsed_url.fragment
        
        soup = self.get_soup(main_url, wait_time=1.5)
        if not soup: return

        body_content = [f"<h1>{name}</h1>", f'<p><a href="{main_url}" target="_blank">>> 公式サイトへ</a></p><hr>']

        # --- 開始位置の特定 ---
        start_node = None
        if anchor_id:
            start_node = soup.find(id=anchor_id)
        
        # アンカーがない、または見つからない場合は見出しテキストで検索
        if not start_node:
            for h2 in soup.find_all('h2'):
                if name in h2.get_text():
                    start_node = h2
                    break
        
        # 範囲を特定（次のh2が出るまで）
        target_elements = []
        if start_node:
            for sibling in start_node.next_siblings:
                if isinstance(sibling, bs4.element.Tag):
                    if sibling.name == 'h2': break
                    target_elements.append(sibling)
        else:
            # どちらの方法でも見つからない場合はメインコンテンツ全体
            area = soup.find('div', id=['main', '__main_contents'])
            target_elements = [area] if area else []

        # --- データ抽出 ---
        seen_urls = set()
        for element in target_elements:
            # dlタグ構造の処理
            dls = element.find_all('dl') if element.name != 'dl' else [element]
            for dl in dls:
                dts = dl.find_all('dt')
                dds = dl.find_all('dd')
                for dt, dd in zip(dts, dds):
                    row_title = dt.get_text(strip=True)
                    row_links = []
                    
                    for a in dd.find_all('a', href=True):
                        link_text = a.get_text(strip=True) or dd.get_text(strip=True).split('｜')[0]
                        sub_url = urljoin(main_url, a.get('href'))
                        
                        if any(kw in link_text for kw in ["配布資料", "配付資料"]):
                            # 子ページ（配布資料ページ）の解析
                            self.logger.info(f"    解析中: {row_title}")
                            sub_soup = self.get_soup(sub_url, wait_time=0.6)
                            if sub_soup:
                                row_links.extend(self.extract_papers_enecho(sub_soup, sub_url))
                        else:
                            # 直接リンク（議事録、YouTube、ニュース等）
                            if sub_url not in seen_urls:
                                suffix = " (動画)" if "youtu" in sub_url.lower() else ""
                                row_links.append(f'<li><a href="{sub_url}" target="_blank">{link_text}{suffix}</a></li>')
                                seen_urls.add(sub_url)
                    
                    if row_links:
                        body_content.append(f"<h2>{row_title}</h2><ul>{''.join(row_links)}</ul>")

        self.save_html(file_path, name, "".join(body_content))
        self.logger.info(f"    完了: {file_path.name}")

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

# --- メイン処理 ---
if __name__ == "__main__":
    csv_path = "committees_エネ庁.csv"
    
    if not os.path.exists(csv_path):
        print(f"エラー: {csv_path} が見つかりません。")
    else:
        scraper = MetiCommitteeScraper()
        try:
            with open(csv_path, mode='r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('enabled') != '1':
                        continue
                        
                    name = row['name']
                    main_url = row['main_url']
                    
                    scraper.process_committee_ENECHO(name, main_url)
        finally:
            scraper.close()
            # メイン処理の終了ログはscraper.loggerを通じて出すか、直接print
            print("\nすべて完了しました。詳細は log フォルダを確認してください。")

