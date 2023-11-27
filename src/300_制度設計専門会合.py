<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# 制度設計専門会合の関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -----------------------------------
# モジュールよみこみ
# -----------------------------------
import requests, bs4

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_HTML = '制度設計専門会合.html'
DIR_OUTPUT = r'../egmsc'

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
  <title>制度設計専門会合</title>
  <meta charset="UTF-8">
</head>
<h1>制度設計専門会合</h1>
<a href="https://www.emsc.meti.go.jp/activity/index_system.html" target="_blank">委員会ページ</a>
<body>
{body}
</body>
</html>
'''

# 本文
body = ''

## 開催回・資料リンク先の取得
name_url_list = ['https://www.emsc.meti.go.jp/activity/index_system.html', # 直近
                 'https://www.emsc.meti.go.jp/activity/index_systemlog.html'] # 過去分

for name_url in name_url_list:
    # html取得
    res = requests.get(name_url)
    
    if res.status_code == 404: # ページ接続出来なかった場合
        print(res.status_code, name_url) # URLアクセス状況表示 
    else: # ページ接続出来た場合
        #print(res.status_code, name_url) # URLアクセス状況表示  
        
        # html取得、異常処理
        res.raise_for_status()
        
        # BeautifulSoup（html解析）オブジェクト生成
        soup = bs4.BeautifulSoup(res.content, 'lxml')
        
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
                    
                    # html取得
                    res_papers = requests.get(papers_url)
        
                    if res_papers.status_code == 404: # ページ接続出来なかった場合
                        print(res_papers.status_code, papers_url) # URLアクセス状況表示
                        title += '（取得失敗）'
                    else: # ページ接続出来た場合
                        #print(res_papers.status_code, papers_url) # URLアクセス状況表示  
                        
                        # html取得、異常処理
                        res_papers.raise_for_status()
                        
                        # BeautifulSoup（html解析）オブジェクト生成
                        soup_papers = bs4.BeautifulSoup(res_papers.content, 'lxml')
                        
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
html_txt = html_txt.format(body = body)

# htmlファイルへ書き出し
with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
    html_file.write(html_txt) 
=======
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# 制度設計専門会合の関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -----------------------------------
# モジュールよみこみ
# -----------------------------------
import requests, bs4

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_HTML = '制度設計専門会合.html'
DIR_OUTPUT = r'../egmsc'

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
  <title>制度設計専門会合</title>
  <meta charset="UTF-8">
</head>
<h1>制度設計専門会合</h1>
<a href="https://www.emsc.meti.go.jp/activity/index_system.html" target="_blank">委員会ページ</a>
<body>
{body}
</body>
</html>
'''

# 本文
body = ''

## 開催回・資料リンク先の取得
name_url_list = ['https://www.emsc.meti.go.jp/activity/index_system.html', # 直近
                 'https://www.emsc.meti.go.jp/activity/index_systemlog.html'] # 過去分

for name_url in name_url_list:
    # html取得
    res = requests.get(name_url)
    
    if res.status_code == 404: # ページ接続出来なかった場合
        print(res.status_code, name_url) # URLアクセス状況表示 
    else: # ページ接続出来た場合
        #print(res.status_code, name_url) # URLアクセス状況表示  
        
        # html取得、異常処理
        res.raise_for_status()
        
        # BeautifulSoup（html解析）オブジェクト生成
        soup = bs4.BeautifulSoup(res.content, 'lxml')
        
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
                    
                    # html取得
                    res_papers = requests.get(papers_url)
        
                    if res_papers.status_code == 404: # ページ接続出来なかった場合
                        print(res_papers.status_code, papers_url) # URLアクセス状況表示
                        title += '（取得失敗）'
                    else: # ページ接続出来た場合
                        #print(res_papers.status_code, papers_url) # URLアクセス状況表示  
                        
                        # html取得、異常処理
                        res_papers.raise_for_status()
                        
                        # BeautifulSoup（html解析）オブジェクト生成
                        soup_papers = bs4.BeautifulSoup(res_papers.content, 'lxml')
                        
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
html_txt = html_txt.format(body = body)

# htmlファイルへ書き出し
with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
    html_file.write(html_txt) 
>>>>>>> a0feaa7f3d85d461e3a2a73b7dae87d8fe2851b3
