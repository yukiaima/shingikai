# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# 持続可能な電力システム構築小委員会の関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -----------------------------------
# モジュールよみこみ
# -----------------------------------
import requests, bs4

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_HTML = '持続可能な電力システム構築小委員会.html'
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
  <title>持続可能な電力システム構築小委員会</title>
  <meta charset="UTF-8">
</head>
<body>
{body}
</body>
</html>
'''

# 見出し1
body = '''<h1>持続可能な電力システム構築小委員会</h1>
<a href="https://www.enecho.meti.go.jp/committee/council/basic_policy_subcommittee/#system_kouchiku" target="_blank">委員会ページ</a>'''

## 開催回・資料リンク先の取得
name_url = 'https://www.enecho.meti.go.jp/committee/council/basic_policy_subcommittee/#system_kouchiku'

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
    
    for c in soup.find('div', {'id': 'main'}).find('h2', {'id': 'system_kouchiku'}).next_siblings:
        if type(c) is bs4.element.Tag: 
            if (c.name == 'h2'): # 次の委員会の見出しになったら終了
                break
            elif (c.name == 'dl') and (c.get('class') == ['dlist']): # リストの場合
                ind_dd = 0
                for dd in c.find_all('dd'):
                    # 開催回ごとのhtml文
                    body_n_com = '''
                    <h2>{title}</h2>
                    <ul>{papers}</ul>
                    <ul>{annnai_gijiroku}</ul>
                    '''

                    html_annnai = ''
                    html_papers = ''
                    
                    # 見出し2のタイトル
                    title = c.find_all('dt')[ind_dd]
                    
                    for a in dd.find_all('a'):
                        if a.get_text(strip=True)[:4]!='配布資料': #配布資料以外
                            if a.get('href') == '': # urlなし
                                html_annnai += '<li><a>{}</a></li>'.format(a.get_text(strip=True))
                            else: # urlあり
                                # コンテンツのあるurl
                                if a.get('href')[:4] == 'http':
                                    contents_url = a.get('href')
                                elif a.get('href')[0] == r'/':
                                    contents_url = '{}{}'.format(
                                        name_url[0:9+name_url[9:].find('/')], a.get('href')) 
                                else: 
                                    contents_url = '{}{}'.format(
                                        name_url[0:name_url.rfind('/')+1], a.get('href')) 
                            
                                html_annnai += '<li><a href={} target="_blank">{}</a></li>'.format(
                                    contents_url, a.get_text(strip=True))
                        else: # 配布資料
                            # 資料のあるurl
                            if a.get('href')[:4] == 'http':
                                papers_url = a.get('href')
                            elif a.get('href')[0] == r'/':
                                papers_url = '{}{}'.format(
                                    name_url[0:9+name_url[9:].find('/')], a.get('href')) 
                            else: 
                                papers_url = '{}{}'.format(
                                    name_url[0:name_url.rfind('/')+1], a.get('href')) 
                                
                            # 資料ページから情報取得
                            
                            # html取得
                            res_papers = requests.get(papers_url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
                
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
                                if len(soup_papers.find('div', {'id': 'main'}).find_all('dd')) == 0:
                                    for ul in soup_papers.find('div', {'id': 'main'}).find_all('ul'):
                                        # 資料名、資料urlを取り出し
                                        html_papers += '\n'.join(
                                            ['<li><a href={} target="_blank">{}</a></li>'.format(
                                                li.a.get('href') if li.a.get('href')[:4] == 'http' 
                                                else '{}{}'.format(papers_url[0:9+papers_url[9:].find('/')], li.a.get('href')
                                                    ) if li.a.get('href')[0] == r'/' else '{}{}'.format(
                                                        papers_url[0:papers_url.rfind('/')+1], li.a.get('href')
                                                        ), # 資料url
                                                li.get_text() # 資料名
                                                ) for li in ul.find_all('li') if len(li.find_all('a'))!=0])
                                else: # 古いページ
                                    for dd in soup_papers.find('div', {'id': 'main'}).find_all('dd'):
                                        # 資料名、資料urlを取り出し
                                        html_papers += '\n'.join(
                                            ['<li><a href={} target="_blank">{}</a></li>'.format(
                                                a.get('href') if a.get('href')[:4] == 'http' 
                                                else '{}{}'.format(papers_url[0:9+papers_url[9:].find('/')], a.get('href')
                                                    ) if a.get('href')[0] == r'/' else '{}{}'.format(
                                                        papers_url[0:papers_url.rfind('/')+1], a.get('href')
                                                        ), # 資料url
                                                dd.get_text() # 資料名
                                                ) for a in dd.find_all('a') if len(dd.find_all('a'))!=0])
                                
                    # コンテンツを収納
                    body_n_com = body_n_com.format(title = title, papers = html_papers, annnai_gijiroku = html_annnai)
                                
                    # bodyに追記
                    body += body_n_com
                    
                    # ind_ddを増やす
                    ind_dd += 1
                        
# bodyを挿入
html_txt = html_txt.format(body = body)

# htmlファイルへ書き出し
with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
    html_file.write(html_txt) 
    