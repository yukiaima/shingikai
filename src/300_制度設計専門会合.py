# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# 制度設計専門会合の関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -----------------------------------
# モジュールよみこみ
# -----------------------------------
import bs4
from selenium import webdriver

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_COMMITTEE = '制度設計専門会合'
URL_COMMITTEE = 'https://www.emsc.meti.go.jp/activity/index_system.html'
NAME_HTML = '{}.html'.format(NAME_COMMITTEE)
DIR_OUTPUT = r'../egmsc'

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
{body}
</body>
</html>
'''

# 見出し1 周辺の作成
body = '''<h1>{name_committee}</h1>
<a href="{url}" target="_blank">委員会ページ</a>
'''.format(name_committee = NAME_COMMITTEE, url = URL_COMMITTEE)

## 開催回・資料リンク先の取得
name_url_list = ['https://www.emsc.meti.go.jp/activity/index_system.html', # 直近
                 'https://www.emsc.meti.go.jp/activity/index_systemlog.html'] # 過去分

for name_url in name_url_list:
    ## 開催回・資料リンク先の取得
    #name_url = URL_COMMITTEE

    # ブラウザでwebページを開く
    driver.get(name_url)

    # BeautifulSoup（html解析）オブジェクト生成
    soup = bs4.BeautifulSoup(driver.page_source, 'lxml')
        
    # 回ごとに処理
    for tr in soup.find('table', {'class': 'tableLayout borderdot', 'summary': '制度設計専門会合 開催一覧'}).find_all('tr'):
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
            if (td.get_text(strip=True) != '配付資料') and (td.get_text(strip=True) != '配布資料'): # 配布資料以外
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
                
                # lnkLstの情報を加工しながら取り出し
                ul = soup_papers.find('div', {'id': 'meti_or'}).find('ul', {'class': 'lnkLst'})
                
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
        body_n_com = body_n_com.format(title = title, gijiroku = gijiroku, papers = html_papers)
                    
        # bodyに追記（新しい回ほど、後ろに追加していく）
        body = body + body_n_com

# bodyを挿入
html_txt = html_txt.format(name_committee = NAME_COMMITTEE, body = body)

# htmlファイルへ書き出し
with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
    html_file.write(html_txt) 

# seleniumのオブジェクトを閉じる
driver.quit()
