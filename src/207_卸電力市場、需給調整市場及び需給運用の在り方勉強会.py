# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# 卸電力市場、需給調整市場及び需給運用の在り方勉強会の関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -----------------------------------
# モジュールよみこみ
# -----------------------------------
import requests, bs4

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_HTML = '卸電力市場、需給調整市場及び需給運用の在り方勉強会.html'
DIR_OUTPUT = r'../meti'
CONNECT_TIMEOUT = 30 # html接続のタイムアウト
READ_TIMEOUT = 30 # html読み込みのタイムアウト

# -----------------------------------
# 関数
# -----------------------------------

# -----------------------------------
# main
# -----------------------------------
# 見出し1まで作成
html_txt = '''<!DOCTYPE html>
<html>
<head>
  <title>卸電力市場、需給調整市場及び需給運用の在り方勉強会</title>
  <meta charset="UTF-8">
</head>
<body>
{body}
</body>
</html>
'''

# 見出し1
body = '''<h1>卸電力市場、需給調整市場及び需給運用の在り方勉強会</h1>
<a href="https://www.meti.go.jp/shingikai/energy_environment/oroshi_jukyu/index.html" target="_blank">委員会ページ</a>'''

## 開催回・資料リンク先の取得
name_url = 'https://www.meti.go.jp/shingikai/energy_environment/oroshi_jukyu/index.html'

# html取得
res = requests.get(name_url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))

if res.status_code == 404: # ページ接続出来なかった場合
    print(res.status_code, name_url) # URLアクセス状況表示 
else: # ページ接続出来た場合
    #print(res.status_code, name_url) # URLアクセス状況表示  
    
    # html取得、異常処理
    res.raise_for_status()
    
    # BeautifulSoup（html解析）オブジェクト生成
    soup = bs4.BeautifulSoup(res.content, 'lxml')
    
    for ul in soup.find('div', {'id': '__main_contents', 'class': 'main w1000'}).find_all('ul', {'class': 'linkE clearfix'}):
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
            
            # html取得
            res_papers = requests.get(papers_url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))

            if res_papers.status_code == 404: # ページ接続出来なかった場合
                print(res_papers.status_code, papers_url) # URLアクセス状況表示
                h2_title += '（取得失敗）'
            else: # ページ接続出来た場合
                #print(res_papers.status_code, papers_url) # URLアクセス状況表示  
                
                # html取得、異常処理
                res_papers.raise_for_status()
                
                # BeautifulSoup（html解析）オブジェクト生成
                soup_papers = bs4.BeautifulSoup(res_papers.content, 'lxml')
                
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
html_txt = html_txt.format(body = body)

# htmlファイルへ書き出し
with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
    html_file.write(html_txt) 
