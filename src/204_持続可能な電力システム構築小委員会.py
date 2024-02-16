# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# 持続可能な電力システム構築小委員会の関係資料一覧のhtml作成
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
NAME_COMMITTEE = '持続可能な電力システム構築小委員会'
URL_COMMITTEE = 'https://www.enecho.meti.go.jp/committee/council/basic_policy_subcommittee/#system_kouchiku'
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

# 既に審議会資料一覧のhtmlがある場合、最終更新日と一致するか確認して処理の継続するか判断 ※構築小委のページには更新日情報がない
flag_proceed = True
'''
if os.path.isfile(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML)): 
    # 現在の審議会資料一覧のhtml取得
    soup_old = bs4.BeautifulSoup(open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), encoding="utf-8"), 'lxml')
    
    # 現在の審議会資料一覧に最終更新日がある
    if soup_old.find('div', {'id': 'update'}) != None:
        # 最終更新日が一致する場合は、処理不要
        if soup_old.find('div', {'id': 'update'}).get_text(strip=True) == soup.find('div', {'id': '__rdo_update'}).get_text(strip=True):
            flag_proceed = False
'''            

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

    # 見出し1 周辺の作成 ※構築小委のページには更新日情報がない
    body = '''<h1>{name_committee}</h1>
    <a href="{url}" target="_blank">委員会ページ</a>
    '''.format(name_committee = NAME_COMMITTEE, url = URL_COMMITTEE)
    
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
                            
                            # ブラウザでwebページを開く
                            driver.get(papers_url)
                    
                            # BeautifulSoup（html解析）オブジェクト生成
                            soup_papers = bs4.BeautifulSoup(driver.page_source, 'lxml')
                            
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
    html_txt = html_txt.format(name_committee = NAME_COMMITTEE, body = body)
    
    # htmlファイルへ書き出し
    with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
        html_file.write(html_txt) 

# seleniumのオブジェクトを閉じる
driver.quit()
