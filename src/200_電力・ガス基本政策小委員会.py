# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# 電力・ガス基本政策小委員会の関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -----------------------------------
# モジュールよみこみ
# -----------------------------------
import os
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_COMMITTEE = '電力・ガス基本政策小委員会'
URL_COMMITTEE = 'https://www.meti.go.jp/shingikai/enecho/denryoku_gas/denryoku_gas/index.html'
NAME_HTML = '{}.html'.format(NAME_COMMITTEE)
DIR_OUTPUT = r'../meti'

# -----------------------------------
# 関数
# -----------------------------------

# -----------------------------------
# main
# -----------------------------------
# selenium関係の初期設定
service = ChromeService(ChromeDriverManager().install()) # ドライバを自動でインストールする
driver = webdriver.Chrome(service=service) # ブラウザ操作・ページの要素検索を行うオブジェクト
driver.minimize_window() # ウインドウの最小化

## 開催回・資料リンク先の取得
name_url = URL_COMMITTEE

# ブラウザでwebページを開く
driver.get(name_url)

# BeautifulSoup（html解析）オブジェクト生成
soup = bs4.BeautifulSoup(driver.page_source, 'lxml')

# 既に審議会資料一覧のhtmlがある場合、最終更新日と一致するか確認して処理の継続するか判断
flag_proceed = True
if os.path.isfile(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML)): 
    # 現在の審議会資料一覧のhtml取得
    soup_old = bs4.BeautifulSoup(open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), encoding="utf-8"), 'lxml')
    
    # 現在の審議会資料一覧に最終更新日がある
    if soup_old.find('div', {'id': 'update'}) != None:
        # 最終更新日が一致する場合は、処理不要
        if soup_old.find('div', {'id': 'update'}).get_text(strip=True) == soup.find('div', {'id': '__rdo_update'}).get_text(strip=True):
            flag_proceed = False
            
if flag_proceed == True:
    # html骨格の作成
    html_txt = '''<!DOCTYPE html>
    <html>
    <head>
      <title>{name_committee}</title>
      <meta charset="UTF-8">
    </head>
    <body>
    {body}
    </body>
    </html>
    '''

    # 見出し1 周辺の作成
    body = '''<h1>{name_committee}</h1>
    <a href="{url}" target="_blank">委員会ページ</a>
    <div id="update">
    <p>{update}</p>
    </div>
    '''.format(name_committee = NAME_COMMITTEE, url = URL_COMMITTEE, 
    update = soup.find('div', {'id': '__rdo_update'}).get_text(strip=True))
    
    for ul in soup.find('div', {'id': '__main_contents', 'class': 'main w1000'}).find_all('ul', {'class': 'linkE clearfix mb0'}):
        for li in ul.find_all('li'):
            # 見出し2のタイトル
            h2_title = li.get_text(strip=True)
            
            # 資料のあるurl
            if li.a.get('href')[:4] == 'http':
                papers_url = li.a.get('href')
            elif li.a.get('href')[0] == r'/':
                papers_url = '{}{}'.format(
                    name_url[0:9+name_url[9:].find('/')], li.a.get('href')) 
            else: 
                papers_url = '{}{}'.format(
                    name_url[0:name_url.rfind('/')+1], li.a.get('href')) 
                
            # 資料ページの情報取得
            # 開催回ごとのhtml文
            body_n_com = '''
            <h2>{title}</h2>
            <ul>{papers}</ul>
            '''
            
            html_papers = ''
            
            # ブラウザでwebページを開く
            driver.get(papers_url)
    
            # BeautifulSoup（html解析）オブジェクト生成
            soup_papers = bs4.BeautifulSoup(driver.page_source, 'lxml')
                
            # lnkLstの情報を加工しながら取り出し
            for ul in soup_papers.find('div', {'class': 'main w1000'}).find_all('ul', {'class': 'lnkLst'}):
                # 資料名、資料urlを取り出し
                html_papers += '\n'.join(
                    ['<li><a href={} target="_blank">{}</a></li>'.format(
                        li.a.get('href') if li.a.get('href')[:4] == 'http' 
                        else '{}{}'.format(papers_url[0:9+papers_url[9:].find('/')], li.a.get('href')
                            ) if li.a.get('href')[0] == r'/' else '{}{}'.format(
                                papers_url[0:papers_url.rfind('/')+1], li.a.get('href')
                                ), # 資料url
                        li.a.get_text(strip=True) # 資料名
                        ) for li in ul.find_all('li') if (len(li.find_all('a'))!=0) and (li.a.get_text(strip=True) != 'ダウンロード（Adobeサイトへ）')])
                    
            # コンテンツを収納
            body_n_com = body_n_com.format(title = h2_title, papers = html_papers)
                        
            # bodyに追記
            body += body_n_com
    
    # bodyを挿入
    html_txt = html_txt.format(name_committee = NAME_COMMITTEE, body = body)
    
    # htmlファイルへ書き出し
    with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
        html_file.write(html_txt) 

# seleniumのオブジェクトを閉じる
driver.quit()
