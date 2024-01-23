# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:04:38 2022
# マージン検討会の関係資料一覧のhtml作成
@author: Koichiro_ISHIKAWA
"""

# -----------------------------------
# モジュールよみこみ
# -----------------------------------
import requests, bs4
import CONST

# -----------------------------------
# 定数定義
# -----------------------------------
NAME_HTML = 'マージン検討会.html'
DIR_OUTPUT = r'../occto'
CONNECT_TIMEOUT = CONST.CONNECT_TIMEOUT # html接続のタイムアウト
READ_TIMEOUT = CONST.READ_TIMEOUT # html読み込みのタイムアウト

# -----------------------------------
# 関数
# -----------------------------------
def conv_abs_url(url_obj, url_page):
    if url_obj[:4] == 'http': # 先頭がhttpの場合は、既に絶対パス
        abs_url = url_obj
    elif url_obj[0] == r'/': # 先頭が/の場合、ルートディレクトリ起点にパス
        abs_url = '{}{}'.format(
            url_page[0:9+url_page[9:].find('/')], url_obj) # 'https://'(8文字)は除いて/を探す
    else: # それ以外は、現在のページディレクトリ起点にパス
        if '.' in url_obj: # 拡張子がある場合は、そのまま
            abs_url = '{}{}'.format(
                url_page[0:url_page.rfind('/')+1], url_obj) 
        else: # 拡張子がない場合は、後ろに/
            abs_url = '{}{}/'.format(
                url_page[0:url_page.rfind('/')+1], url_obj) 
    
    return abs_url

# -----------------------------------
# main
# -----------------------------------
# 見出し1まで作成
html_txt = '''<!DOCTYPE html>
<html>
<head>
  <title>マージン検討会</title>
  <meta charset="UTF-8">
</head>
<body>
{body}
</body>
</html>
'''

# 見出し1
body = '''<h1>マージン検討会</h1>
<a href="https://www.occto.or.jp/iinkai/margin/index.html" target="_blank">委員会ページ</a>'''

# 情報を取得する対象ページ（今年度）
name_url = 'https://www.occto.or.jp/iinkai/margin/index.html'

# 過去分の情報を入れておく配列
old_url_list = []

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
    
    # 広域系統整備委員会（頭から）に関係する部分から探索し、今年度に該当する部分を取得
    for c in soup.find('main', {'id': 'contents'}).find('h1').next_siblings:
        if type(c) is bs4.element.Tag: 
            if (c.name == 'h2') and (c.get('id') == 'study'): # 特にとめない（左の条件は意味なし）
                break
            elif (c.name == 'ul') and (c.get('class') == ['list2', 'index']): # リストの場合
                for li in c.find_all('li'):
                    if li.get_text(strip=True)[-2:] == '年度': # 過去分
                        # urlを絶対パスに変換
                        old_url = conv_abs_url(li.a.get('href'), name_url)
                        
                        # 過去分のリストに追加
                        old_url_list += [old_url]
                    else: # 過去分以外
                        # 開催回ごとのhtml文
                        body_n_com = '''
                        <h2>{title}</h2>
                        <ul>{papers}</ul>
                        <ul>{annnai_gijiroku}</ul>
                        '''
                        title = ''
                        html_annnai = ''
                        html_papers = ''
                        
                        for a in li.find_all('a'):
                            # liからa部分を削除
                            a = a.extract()
                            
                            if a.get_text(strip=True)[:4]!='配布資料': #配布資料以外
                                if a.get('href') == '': # urlなし
                                    html_annnai += '<li><a>{}</a></li>'.format(a.get_text(strip=True))
                                else: # urlあり
                                    # コンテンツのあるurl
                                    contents_url = conv_abs_url(a.get('href'), name_url)
                                
                                    html_annnai += '<li><a href={} target="_blank">{}</a></li>'.format(
                                        contents_url, a.get_text(strip=True))
                                    
                            else: # 配布資料
                                # 資料のあるurl
                                papers_url = conv_abs_url(a.get('href'), name_url)
                                    
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
                                    
                                    if len(soup_papers.find('div', {'id': 'main'}).find_all('ul')) != 0: #ulにより分けている            
                                        # lnkLstの情報を加工しながら取り出し
                                        ul = soup_papers.find('div', {'id': 'main'}).find('ul')
                                        # 資料名、資料urlを取り出し
                                        html_papers += '\n'.join(
                                            ['<li><a href={} target="_blank">{}</a></li>'.format(
                                                conv_abs_url(li.a.get('href'), papers_url), # 資料url
                                                li.get_text() # 資料名
                                                ) for li in ul.find_all('li') if len(li.find_all('a'))!=0])
                                    else: #ulにより分けていない。aで区切る
                                        # lnkLstの情報を加工しながら取り出し
                                        div = soup_papers.find('div', {'id': 'main'})
                                        # 資料名、資料urlを取り出し
                                        html_papers += '\n'.join(
                                            ['<li><a href={} target="_blank">{}</a></li>'.format(
                                                conv_abs_url(a.get('href'), papers_url), # 資料url
                                                a.get_text() # 資料名
                                                ) for a in div.find_all('a') if len(div.find_all('a'))!=0])
                                                    
                            
                        # <a>を除いて残ったもの
                        title = li.get_text(strip=True)
                        
                        # bodyに追加
                        body += body_n_com.format(title=title, annnai_gijiroku=html_annnai, papers=html_papers)

# 情報を取得する対象ページ（過去分）
for name_url in old_url_list:
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
        
        # 広域系統整備委員会（頭から）に関係する部分から探索し、今年度に該当する部分を取得
        for li in soup.find('div', {'id': 'main'}).find('ul').find_all('li'):
            # 開催回ごとのhtml文
            body_n_com = '''
            <h2>{title}</h2>
            <ul>{papers}</ul>
            <ul>{annnai_gijiroku}</ul>
            '''
            title = ''
            html_annnai = ''
            html_papers = ''
            
            for a in li.find_all('a'):
                # liからa部分を削除
                a = a.extract()
                
                if a.get_text(strip=True)[:4]!='配布資料': #配布資料以外
                    if a.get('href') == '': # urlなし
                        html_annnai += '<li><a>{}</a></li>'.format(a.get_text(strip=True))
                    else: # urlあり
                        # コンテンツのあるurl
                        contents_url = conv_abs_url(a.get('href'), name_url)
                    
                        html_annnai += '<li><a href={} target="_blank">{}</a></li>'.format(
                            contents_url, a.get_text(strip=True))
                        
                else: # 配布資料
                    # 資料のあるurl
                    papers_url = conv_abs_url(a.get('href'), name_url)
                        
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
                        
                        if len(soup_papers.find('div', {'id': 'main'}).find_all('ul')) != 0: #ulにより分けている            
                            # lnkLstの情報を加工しながら取り出し
                            ul = soup_papers.find('div', {'id': 'main'}).find('ul')
                            # 資料名、資料urlを取り出し
                            html_papers += '\n'.join(
                                ['<li><a href={} target="_blank">{}</a></li>'.format(
                                    conv_abs_url(li.a.get('href'), papers_url), # 資料url
                                    li.get_text() # 資料名
                                    ) for li in ul.find_all('li') if len(li.find_all('a'))!=0])
                        else: #ulにより分けていない。aで区切る
                            # lnkLstの情報を加工しながら取り出し
                            div = soup_papers.find('div', {'id': 'main'})
                            # 資料名、資料urlを取り出し
                            html_papers += '\n'.join(
                                ['<li><a href={} target="_blank">{}</a></li>'.format(
                                    conv_abs_url(a.get('href'), papers_url), # 資料url
                                    a.get_text() # 資料名
                                    ) for a in div.find_all('a') if len(div.find_all('a'))!=0])          
                
            # <a>を除いて残ったもの
            title = li.get_text(strip=True)
            
            # bodyに追加
            body += body_n_com.format(title=title, annnai_gijiroku=html_annnai, papers=html_papers)                    
    
    
# bodyを挿入
html_txt = html_txt.format(body = body)

# htmlファイルへ書き出し
with open(r'{}\{}'.format(DIR_OUTPUT, NAME_HTML), 'w', encoding='utf-8' ) as html_file: 
    html_file.write(html_txt) 
