import csv
import os
import time
import logging  # 追加
import re
from datetime import datetime  # 追加
from pathlib import Path
from urllib.parse import urljoin
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class MetiCommitteeScraper:
    def __init__(self, output_dir='../egmsc'):
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
    
    def parse_egc_table(self, soup, current_url):
        results_with_date = []  # (日付数値, HTMLコンテンツ) を入れるリスト
        tables = soup.find_all('table', class_='tableLayout')
        
        def convert_jp_date_to_int(text):
            """和暦の日付を YYYYMMDD の整数に変換する"""
            patterns = [
                r'(令和|平成)\s*(\d+|元)年\s*(\d+)月\s*(\d+)日',
                r'(\d{4})年\s*(\d+)月\s*(\d+)日'  # 西暦の場合も考慮
            ]
            
            for pattern in patterns:
                m = re.search(pattern, text)
                if m:
                    groups = m.groups()
                    if groups[0] == '令和':
                        year = (1 if groups[1] == '元' else int(groups[1])) + 2018
                    elif groups[0] == '平成':
                        year = (1 if groups[1] == '元' else int(groups[1])) + 1988
                    else:
                        year = int(groups[0])
                    
                    month = int(groups[-2])
                    day = int(groups[-1])
                    return year * 10000 + month * 100 + day
            return 0  # 日付が見つからない場合

        for target_table in tables:
            summary_text = target_table.get('summary', '')
            table_full_text = target_table.get_text()
            
            if "開催一覧" not in summary_text and "開催一覧" not in table_full_text:
                continue

            for tr in target_table.find_all('tr'):
                # 年度ナビゲーション行のスキップ
                row_text = tr.get_text(strip=True)
                if '第' in row_text and '回' in row_text and ('～' in row_text or '~' in row_text):
                    continue

                tds = tr.find_all('td')
                if len(tds) < 2: continue

                row_title_parts = []
                papers_html = ""
                other_links = []

                for td in tds:
                    links = td.find_all('a')
                    text = td.get_text(strip=True)
                    if links:
                        for a in links:
                            href = urljoin(current_url, a.get('href'))
                            link_text = a.get_text(strip=True)
                            if "配布資料" in link_text or "配付資料" in link_text:
                                papers_html = self.extract_egc_papers(href)
                            else:
                                other_links.append(f'<li><a href="{href}" target="_blank">{link_text}</a></li>')
                    
                    if text:
                        clean_text = text.replace("配布資料", "").replace("配付資料", "").replace("議事要旨", "").replace("議事録", "").replace("動画", "").strip()
                        if clean_text:
                            row_title_parts.append(clean_text)

                if row_title_parts or papers_html:
                    title = " ".join(row_title_parts)
                    
                    # 【修正】日付を数値化してソートキーにする
                    date_val = convert_jp_date_to_int(title)
                    
                    self.logger.info(f"      解析中: {title if title else '詳細不明の回'}")

                    content = f"<h2>{title}</h2>"
                    link_section = []
                    if papers_html: link_section.append(papers_html)
                    if other_links: link_section.append("\n".join(other_links))
                    
                    if link_section:
                        inner_html = '\n'.join(link_section)
                        content += f"<ul>{inner_html}</ul>"
                    
                    results_with_date.append((date_val, content))
        
        # 日付数値で降順（新しい順）にソート
        results_with_date.sort(key=lambda x: x[0], reverse=True)
        
        return [item[1] for item in results_with_date]

    def extract_egc_papers(self, url):
        """EGCの個別資料ページからPDFリストを抽出"""
        soup = self.get_soup(url, wait_time=0.5)
        if not soup: return ""
        
        paper_links = []
        # 監視等委員会の個別ページは 'meti_or' というIDの中に 'lnkLst' がある
        target_area = soup.find('div', id='meti_or') or soup
        ul = target_area.find('ul', class_='lnkLst')
        
        if ul:
            for li in ul.find_all('li'):
                a = li.find('a')
                if not a: continue
                txt = a.get_text(strip=True)
                if "Adobe" in txt or not txt: continue
                
                href = urljoin(url, a.get('href'))
                paper_links.append(f'<li><a href="{href}" target="_blank">{txt}</a></li>')
        
        return "\n".join(paper_links)

    def process_committee_egc(self, name, url):
        self.logger.info(f"審議会開始: {name}")
        body_content = [f"<h1>{name}</h1>", f'<p><a href="{url}" target="_blank">>> 委員会公式サイト</a></p><hr>']
        
        soup = self.get_soup(url)
        if not soup: return
        
        # メインページの解析
        table_contents = self.parse_egc_table(soup, url)
        body_content.extend(table_contents)

        # アーカイブリンクの収集
        archive_links = []
        for a in soup.find_all('a'):
            link_text = a.get_text(strip=True)
            # 「第」と「回」を含み、かつ「〜」や「-」を含むものをアーカイブとみなす
            if '第' in link_text and '回' in link_text and ('～' in link_text or '~' in link_text):
                archive_url = urljoin(url, a.get('href'))
                if archive_url not in archive_links and archive_url != url:
                    archive_links.append(archive_url)

        # 【修正ポイント】ファイル名の数字で降順にソート (log5.html -> log4.html ... の順)
        # 監視等委のURL規則（...logN.html）に基づき、逆順でループを回します
        archive_links.sort(key=lambda x: x, reverse=True)

        for sub_url in archive_links:
            self.logger.info(f"    過去分アーカイブ解析中: {sub_url}")
            sub_soup = self.get_soup(sub_url)
            if sub_soup:
                sub_contents = self.parse_egc_table(sub_soup, sub_url)
                body_content.extend(sub_contents)

        file_path = self.output_dir / f"{name}.html"
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
    csv_path = "committees_監視等委.csv"
    
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
                    
                    scraper.process_committee_egc(name, main_url)

        finally:
            scraper.close()
            # メイン処理の終了ログはscraper.loggerを通じて出すか、直接print
            print("\nすべて完了しました。詳細は log フォルダを確認してください。")