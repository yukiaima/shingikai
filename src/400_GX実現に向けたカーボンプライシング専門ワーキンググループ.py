# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# GX実現に向けたカーボンプライシング専門ワーキンググループの関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -----------------------------------
# モジュールよみこみ
# -----------------------------------
import os
import bs4
from selenium import webdriver

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_COMMITTEE = 'GX実現に向けたカーボンプライシング専門ワーキンググループ'
URL_COMMITTEE = 'https://www.cas.go.jp/jp/seisaku/gx_jikkou_kaigi/carbon_pricing_wg/kaisai.html'
NAME_HTML = '{}.html'.format(NAME_COMMITTEE)
DIR_OUTPUT = r'../cas'

# -----------------------------------
# 関数
# -----------------------------------

# -----------------------------------
# main
# -----------------------------------
# selenium関係の初期設定
driver = webdriver.Chrome()
driver.minimize_window() # ウインドウの最小化

# html骨格の作成
html_txt = '''<!DOCTYPE html>
<html>
<head>
  <title>{name_committee}</title>
  <meta charset="UTF-8">
</head>
<body>
<h1>{name_committee}</h1>
<a href="{url}" target="_blank">委員会ページ</a>
{body}
</body>
</html>
'''

# 見出し1 周辺の作成
body = ''

## 開催回・資料リンク先の取得
name_url = URL_COMMITTEE

# ブラウザでwebページを開く
driver.get(name_url)

# BeautifulSoup（html解析）オブジェクト生成
soup = bs4.BeautifulSoup(driver.page_source, 'lxml')

for tr in soup.find('table', {'class', 'tbl_giji'}).find('tbody').find_all('tr'):
    # 開催回ごとのhtml文
    body_n_com = '''
    <h2>{title}</h2>
    <ul>{papers}</ul>
    <ul>{gijiroku}</ul>
    '''
    
    title = ''
    gijiroku = ''
    html_papers = ''
    
    gijiroku_hina = '<li><a href="{href}"  target="_blank">{txt}</a></li>'
    
    for td in tr.find_all('td'):
        if (td.get_text(strip=True) != '議事次第・資料'): # 配布資料以外
            if ''.join([a.get('href') for a in td.find_all('a')]) == '': # urlなし
                title += td.get_text(strip=True)
                
            else: # urlあり
                for a in td.find_all('a'):
                    # コンテンツのあるurl
                    if a.get('href')[:4] == 'http':
                        contents_url = a.get('href')
                    elif a.get('href')[0] == r'/':
                        contents_url = '{}{}'.format(
                            name_url[0:9+name_url[9:].find('/')], a.get('href')) 
                    else: 
                        contents_url = '{}{}'.format(
                            name_url[0:name_url.rfind('/')+1], a.get('href')) 

                    gijiroku += gijiroku_hina.format(href = contents_url, txt = a.get_text(strip=True))
                    
        else: # 配布資料
            # 資料のあるurl
            if td.a.get('href')[:4] == 'http':
                papers_url = td.a.get('href')
            elif td.a.get('href')[0] == r'/':
                papers_url = '{}{}'.format(
                    name_url[0:9+name_url[9:].find('/')], td.a.get('href')) 
            else: 
                papers_url = '{}{}'.format(
                    name_url[0:name_url.rfind('/')+1], td.a.get('href')) 
            
            # 資料ページから情報取得
            
            # ブラウザでwebページを開く
            driver.get(papers_url)
    
            # BeautifulSoup（html解析）オブジェクト生成
            soup_papers = bs4.BeautifulSoup(driver.page_source, 'lxml')
            
            # 資料名、資料urlを取り出し
            html_papers += '\n'.join(
                ['<li><a href={} target="_blank">{}</a></li>'.format(
                    tr2.a.get('href') if tr2.a.get('href')[:4] == 'http' 
                    else '{}{}'.format(papers_url[0:9+papers_url[9:].find('/')], tr2.a.get('href')
                        ) if tr2.a.get('href')[0] == r'/' else '{}{}'.format(
                            papers_url[0:papers_url.rfind('/')+1], tr2.a.get('href')
                            ), # 資料url
                    tr2.get_text(strip=True) # 資料名
                    ) for tr2 in soup_papers.find('table', {'class', 'tbl_giji_nl'}).find_all('tr')])
            
    # コンテンツを収納
    body_n_com = body_n_com.format(title = title, gijiroku = gijiroku, papers = html_papers)
                
    # bodyに追記
    body = body_n_com + body

# bodyを挿入
html_txt = html_txt.format(name_committee = NAME_COMMITTEE, url = URL_COMMITTEE, body = body)

# htmlファイルへ書き出し
with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
    html_file.write(html_txt) 

# seleniumのオブジェクトを閉じる
driver.quit()

