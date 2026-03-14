import csv
import os
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class CommitteeScraper:
    def __init__(self, base_output_dir='../'):
        self.base_output_dir = Path(base_output_dir)
        self._setup_logging()
        self.driver = self._setup_driver()

    def _setup_logging(self):
        """ログの設定：ファイル保存を廃止し、コンソール出力のみに限定"""
        self.logger = logging.getLogger("CommitteeScraper")
        self.logger.setLevel(logging.INFO)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # 画面出力用 (ch: Console Handler) のみの設定
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        
        self.logger.addHandler(ch)
        
        # 開始メッセージ
        self.logger.info("\n" + "="*50 + f"\n実行開始: {datetime.now()}\n" + "="*50)

    def _setup_driver(self):
        options = Options()
        # 基本設定
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # 高速化（画像オフ）
        options.add_argument('--blink-settings=imagesEnabled=false')
        
        # 検知回避
        options.add_argument('--disable-blink-features=AutomationControlled')
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        options.add_argument(f'user-agent={ua}')
        
        # 読み込み戦略（速さ優先）
        options.page_load_strategy = 'eager'
        
        driver = webdriver.Chrome(options=options)
        
        # navigator.webdriver=true を隠す魔法
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        
        driver.set_page_load_timeout(30)
        return driver
    
    # with構文の開始時に呼ばれる
    def __enter__(self):
        return self

    # with構文の終了時（エラー時含む）に必ず呼ばれる
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_soup(self, url, wait_time=1.0):
        try:
            self.driver.get(url)
            time.sleep(wait_time)
            return bs4.BeautifulSoup(self.driver.page_source, 'lxml')
        except Exception as e:
            self.logger.warning(f"取得失敗: {url} ({e})")
            return None

    def save_html(self, folder, name, body):
        out_dir = self.base_output_dir / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / f"{name}.html"
        
        html = f"""<!DOCTYPE html><html lang="ja"><head><title>{name}</title><meta charset="UTF-8">
        <style>body{{font-family:sans-serif;line-height:1.6;padding:30px;max-width:1000px;margin:auto;color:#333;}}
        h1{{border-left:10px solid #005aad;padding-left:15px;font-size:24px;color:#005aad;}}
        h2{{border-bottom:2px solid #005aad;color:#005aad;margin-top:40px;font-size:18px;}}
        a{{color:#005aad;text-decoration:none;}}a:hover{{text-decoration:underline;}}</style>
        </head><body>{body}</body></html>"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        self.logger.info(f"  完了: {file_path}")

    # --- 各組織ごとの解析ロジック ---
    # --- METI ---
    def parse_meti(self, name, main_url, extra_urls=None): # extra_urlsを追加
        self.logger.info(f"METI解析: {name}")
        try:
            soup = self.get_soup(main_url, wait_time=1.5)
            if not soup: return
    
            # 更新チェック
            should_proceed, update_text = self._check_update_meti(name, soup)
            if not should_proceed:
                self.logger.info(f"  ※ 更新なし: スキップ（{update_text}）")
                return
    
            # 【内容抽出】（元: extract_papers_meti の移植）
            # 比較用の生の値を data-update 属性に持たせておくと確実です
            body_content = [
                f"<h1>{name}</h1>",
                f'<p><a href="{main_url}" target="_blank">>> 委員会公式サイト</a></p>',
                f'<div id="update" data-update="{update_text}"><p>最終更新確認日: {update_text}</p></div><hr>'
            ]
            all_sources = [main_url] + (extra_urls if extra_urls else [])
            seen_sub_urls = set()
            
            TARGET_KEYWORDS = ["第", "回", "中間", "報告", "結論", "需給", "対策", "整理", "まとめ", "戦略", "方針", "ロードマップ", "方向", "改革", "貫徹", "設計"]

            for target_url in all_sources:
                list_soup = self.get_soup(target_url)
                main_area = (
                    list_soup.find('div', id=['__main_contents', 'main_contents']) or 
                    list_soup.find('div', class_=['main', 'main w1000']) or 
                    list_soup
                )
                
                if not main_area: continue
                
                for a_tag in main_area.find_all('a', href=True):
                    title = a_tag.get_text(strip=True)
                    sub_url = urljoin(target_url, a_tag.get('href'))
                    is_target = any(kw in title for kw in TARGET_KEYWORDS)
                    
                    if is_target and sub_url not in seen_sub_urls:
                        is_html = any(ext in sub_url.split('/')[-1] for ext in [".html", ".htm"]) or sub_url.endswith('/')
                        
                        if is_html:
                            self.logger.info(f"    解析中: {title}")
                            sub_soup = self.get_soup(sub_url, wait_time=0.5)
                            if sub_soup:
                                paper_links = self._extract_papers_meti(sub_soup, sub_url)
                                if paper_links:
                                    body_content.append(f"<h2>{title}</h2><ul>{''.join(paper_links)}</ul>")
                            seen_sub_urls.add(sub_url)
                        elif any(ext in sub_url.lower() for ext in ['.pdf', '.zip', '.xlsx']):
                            body_content.append(f'<h2>{title}</h2><ul><li><a href="{sub_url}" target="_blank">資料を開く</a></li></ul>')
                            seen_sub_urls.add(sub_url)
                
            # 【保存】
            self.save_html("meti", name, "".join(body_content))  
            self.logger.info(f"    完了: {name}")
            
        except Exception as e:
            self.logger.error(f"METI解析失敗({name}): {e}")
    
    def _check_update_meti(self, name, new_soup):
        file_path = self.base_output_dir / "meti" / f"{name}.html"
        current_update_div = new_soup.find('div', {'id': '__rdo_update'})
        if not current_update_div: 
            return True, "不明"
        
        new_date = current_update_div.get_text(strip=True)
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding="utf-8") as f:
                    old_soup = bs4.BeautifulSoup(f, 'lxml')
                    old_update_div = old_soup.find('div', {'id': 'update'})
                    # data-update属性から取得、なければテキストから判定
                    old_date = old_update_div.get('data-update') if old_update_div else None
                    
                    if old_date == new_date:
                        return False, new_date
            except Exception:
                return True, new_date
        return True, new_date

    def _extract_papers_meti(self, soup, base_url):
        links = []
        seen_files = set()
        
        target_area = (
            soup.find('div', id=['__main_contents', 'main_contents']) or 
            soup.find('div', class_=['main', 'main w1000', 'contents']) or
            soup.find('article') or 
            soup
        )
        
        if target_area:
            for a in target_area.find_all('a', href=True):
                txt = a.get_text(strip=True)
                href = urljoin(base_url, a.get('href'))
                
                if not txt: continue
                if "Adobe" in txt or "ダウンロード" in txt: continue
                if "第" in txt and "回" in txt and not any(ext in href.lower() for ext in ['.pdf', '.xlsx']):
                    continue

                is_doc = any(ext in href.lower() for ext in ['.pdf', '.zip', '.xlsx', '.docx', '.pptx', '.csv'])
                is_yt = "youtube.com" in href.lower() or "youtu.be" in href.lower()

                if (is_doc or is_yt) and href not in seen_files:
                    label = f"{txt} (YouTube)" if is_yt else txt
                    links.append(f'<li><a href="{href}" target="_blank">{label}</a></li>')
                    seen_files.add(href)
        return links
    
    # --- エネ庁 ---
    def parse_enecho(self, name, main_url, extra_urls=None):
        """エネ庁用ロジック"""
        self.logger.info(f"エネ庁解析: {name}")
        parsed_url = urlparse(main_url)
        anchor_id = parsed_url.fragment
        
        try:
            # メインページの取得
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
                                    row_links.extend(self._extract_papers_enecho(sub_soup, sub_url))
                            else:
                                # 直接リンク（議事録、YouTube、ニュース等）
                                if sub_url not in seen_urls:
                                    suffix = " (動画)" if "youtu" in sub_url.lower() else ""
                                    row_links.append(f'<li><a href="{sub_url}" target="_blank">{link_text}{suffix}</a></li>')
                                    seen_urls.add(sub_url)
                        
                        if row_links:
                            body_content.append(f"<h2>{row_title}</h2><ul>{''.join(row_links)}</ul>")

            # 【保存】
            self.save_html('meti', name, "".join(body_content))
            self.logger.info(f"    完了: {name}")
            
        except Exception as e:
            self.logger.error(f"エネ庁解析失敗({name}): {e}")
    
    def _extract_papers_enecho(self, soup, base_url):
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
    
    # --- 監視等委 ---
    def parse_egc(self, name, main_url, extra_urls=None):
        """電力・ガス取引監視等委員会(EGC)用ロジック"""
        self.logger.info(f"監視等委解析: {name}")
        try:
            # 引数の main_url を使って公式サイトへのリンクを作成
            body_content = [f"<h1>{name}</h1>", f'<p><a href="{main_url}" target="_blank">>> 委員会公式サイト</a></p><hr>']
            
            # メインページの取得
            soup = self.get_soup(main_url, wait_time=1.5)
            if not soup: return
            
            # メインページの解析
            table_contents = self._parse_table_egc(soup, main_url) # url -> main_url に修正
            body_content.extend(table_contents)

            # アーカイブリンクの収集
            archive_links = []
            for a in soup.find_all('a', href=True): # href=Trueを追加
                link_text = a.get_text(strip=True)
                if '第' in link_text and '回' in link_text and ('～' in link_text or '~' in link_text):
                    # ここで確実に絶対URLにする
                    archive_url = urljoin(main_url, a.get('href'))
                    if archive_url not in archive_links and archive_url != main_url:
                        archive_links.append(archive_url)

            # アーカイブのソートと解析
            archive_links.sort(reverse=True)

            for sub_url in archive_links:
                self.logger.info(f"    過去分アーカイブ解析中: {sub_url}")
                sub_soup = self.get_soup(sub_url)
                if sub_soup:
                    sub_contents = self._parse_table_egc(sub_soup, sub_url)
                    body_content.extend(sub_contents)
                
            # 保存
            self.save_html("egmsc", name, "".join(body_content))  
            self.logger.info(f"    完了: {name}")
            
        except Exception as e:
            # ログ出力時のラベルを修正 (METI -> 監視等委)
            self.logger.error(f"監視等委解析失敗({name}): {e}")
    
    def _parse_table_egc(self, soup, current_url):
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
                                papers_html = self._extract_papers_egc(href)
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

    def _extract_papers_egc(self, url):
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

    # --- 内閣府 ---
    def parse_cas(self, name, main_url, extra_urls=None):
        """内閣府用ロジック（共通メソッド get_soup を使用）"""
        self.logger.info(f"内閣府解析: {name}")
        try:
            # 1. 最初のページ取得
            soup = self.get_soup(main_url, wait_time=1.5)
            if not soup: return

            # 2. インデックスページから開催状況ページへの遷移が必要な場合
            if "index.html" in main_url:
                link = soup.find('a', string=lambda x: x and ('開催状況' in x or '開催実績' in x))
                if link:
                    main_url = urljoin(main_url, link.get('href'))
                    soup = self.get_soup(main_url, wait_time=1.5)
                    if not soup: return

            table = soup.find('table', class_=lambda x: x and 'tbl_giji' in x)
            if not table:
                self.logger.warning(f"{name}: 開催実績テーブルが見つかりません。")
                return

            html_body = f'<h1>{name}</h1>'
            html_body += f'<p><a href="{main_url}" target="_blank">⇒ 公式委員会ページはこちら</a></p>'
            
            rows = table.find_all('tr')
            for tr in reversed(rows):
                tds = tr.find_all('td')
                if len(tds) < 3: continue
                
                link_td = next((td for td in tds if td.find('a', string=lambda x: x and '資料' in x)), None)
                if not link_td or not link_td.a: continue
                
                title = tds[0].get_text(strip=True) + " " + tds[1].get_text(strip=True)
                papers_url = urljoin(main_url, link_td.a.get('href'))
                
                self.logger.info(f"  詳細取得中: {title}")
                
                # 3. 各回の詳細ページも get_soup で取得
                soup_sub = self.get_soup(papers_url, wait_time=1)
                if not soup_sub: continue
                
                html_body += f"<h2>{title}</h2><ul>"
                sub_table = soup_sub.find('table', class_=lambda x: x and 'tbl_giji' in x)
                if sub_table:
                    for tr2 in sub_table.find_all('tr'):
                        if tr2.a:
                            link_text = tr2.get_text(strip=True)
                            link_url = urljoin(papers_url, tr2.a.get('href'))
                            html_body += f'<li><a href="{link_url}" target="_blank">{link_text}</a></li>'
                html_body += "</ul>"
                
            # 保存
            self.save_html("cas", name, html_body)  
            self.logger.info(f"    完了: {name}")
            
        except Exception as e:
            self.logger.error(f"内閣府解析失敗({name}): {e}")

    def close(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            self.logger.info("ブラウザを終了しました。")

# --- 実行制御 ---
if __name__ == "__main__":
    csv_path = "all_committees.csv"
    if not os.path.exists(csv_path):
        print(f"エラー: {csv_path} が見つかりません。")
    else:
        # with構文を使えば、途中でエラーが起きても自動で close() が呼ばれる
        try:
            with CommitteeScraper() as scraper:
                with open(csv_path, mode='r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('enabled') != '1':
                            continue
                            
                        target_type = row.get('type')
                        name = row['name']
                        main_url = row['main_url']
                        extra_urls = []
                        for i in range(1, 6):
                            col_name = f'extra_url{i}'
                            url = row.get(col_name, "").strip()
                            if url:
                                extra_urls.append(url)
                        
                        if target_type == 'meti':
                            scraper.parse_meti(name, main_url, extra_urls)
                        elif target_type == 'enecho':
                            scraper.parse_enecho(name, main_url, extra_urls)
                        elif target_type == 'egc':
                            scraper.parse_egc(name, main_url, extra_urls)
                        elif target_type == 'cas':
                            scraper.parse_cas(name, main_url, extra_urls)
                        
        except Exception as e:
            print(f"致命的なエラーが発生しました: {e}")
            
