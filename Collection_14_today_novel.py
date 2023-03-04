import os.path
import re
import sys
import time
import traceback

import cchardet
import requests
from bs4 import BeautifulSoup

limit_num=14316059

encoding=''
sensitive_words=[]
with open('敏感词.TXT','r',encoding='utf-8') as f:
    [sensitive_words.append(word[:-1]) for word in f.readlines()]

def check_sensitive(input):
    if re.search('(.*?)(作者|送达者)',input):
        for sensitive_word in sensitive_words:
            if sensitive_word in re.search('(.*?)作者',input).group(1):
                return False
    else:
        for sensitive_word in sensitive_words:
            if sensitive_word in input:
                return False
    return True

def remove_html(text):
    text=re.sub(r'<font(.*?)font>','',text)
    text = re.sub(r'<br/>', '\n', text)
    text = re.sub(r'<p></p>', '\n', text)
    text = re.sub(r'<b>(.*?)</b>', '\n', text)
    text=text.replace("<pre>",'')
    text=text.replace("</pre>",'')
    return text

# 去除非法字符
def rmsc (string):
    # string = string.replace(' ', '') # 空格
    string = string.replace('\\', ' - ')
    string = string.replace('/', ' - ')
    string = string.replace(':', '：')
    string = string.replace('*', '•')
    string = string.replace('?', '？')
    string = string.replace('"', '\'')
    string = string.replace('<', '《')
    string = string.replace('>', '》')
    string = string.replace('|', '-')
    string = string.replace('\t', ' ')
    string = string.replace('\r', ' ')
    string = string.replace('\n', ' ')
    return string

def request_url_source_code(url):
    HEADER = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0)'
                      ' Gecko/20100101 Firefox/106.0',
    }
    num=0
    while num<10:
        num+=1
        try:
            r = requests.get(url, headers=HEADER)
            global encoding
            encoding = cchardet.detect(r.content)['encoding']
            return BeautifulSoup(r.text, 'lxml')
        except:
            traceback.print_exc()
            time.sleep(10 * num)
        print('获取页面失败')


def get_catalogue(soup):

    links = soup.select('#d_list > ul > li > a:nth-child(1)>font[color="grey"]')
    list_ = []
    index='https://www.cool18.com/bbs4/'
    for item in links:
        new_list = []

        if item.text[1:-1] != '':
            classify = item.text[1:-1]
        else:
            classify = '其它'

        if check_sensitive(str(item.previousSibling)):
            new_list.append(classify)
            new_list.append(item.previousSibling)
            new_list.append(index + item.parent['href'])

            if isinstance(new_list[1], str):
                list_.append(new_list)

        if item.parent.parent.select('li>ul'):
            for li in item.parent.parent.select('li'):
                new_a = li.select_one('a')
                if int(re.search('\((.*?) bytes\)', new_a.next_sibling).group(1)) > 10000:
                    if check_sensitive(str(new_a.text)):
                        new_ = []
                        new_.append(classify)
                        new_.append(new_a.text)
                        new_.append(index + new_a['href'])
                        try:
                            if isinstance(new_list[1], str):
                                list_.append(new_)
                        except:
                            pass
    return list_

# 重复文件返回文件副本名
def return_copy_name(name):
    if os.path.exists(name):
        num = 0
        while os.path.exists(name):
            copy_num = re.search('(.*?)（(.*?)）.txt', name)
            if copy_num:
                if copy_num.group(2).isnumeric():
                    num += 1
                    name = copy_num.group(1) + '（' + str(num) + '）.txt'
                else:
                    name = name[:-4] + '（' + str(num) + '）.txt'
                    num += 1
            else:
                name = name[:-4] + '（' + str(num) + '）.txt'
                num += 1
    return name

if __name__ == '__main__':
    index='https://www.cool18.com/bbs4/'
    url='https://www.cool18.com/bbs4/index.php?app=forum&act=cachepage&cp=tree9'

    while True:
        try:
            print('正在收集',url)
            if 'nowpage=20' in url:
                print('截至14天前的小说已收集完毕')
                break
            source_code = request_url_source_code(url)
            if not source_code.select_one('head>script'):
                next = source_code.select('#d_list_foot >span[style="float:right;"] > a:nth-child(2)')
                for a in get_catalogue(source_code):
                    article_source_code = request_url_source_code(a[2])
                    content = article_source_code.select('td.show_content > pre')
                    new_text = remove_html(str(content[0]))
                    if not os.path.exists('./novel'):
                        os.mkdir('novel')
                    file_path = './novel/' + a[0] + '/' + rmsc(a[1]) + '.txt'
                    if not os.path.exists('./novel/' + a[0]):
                        os.mkdir('./novel/' + a[0])
                    if os.path.exists(rmsc(a[1]) + '.txt'):
                        file_path = './novel/' + a[0] + '/' + return_copy_name(rmsc(a[1])) + '.txt'
                    print(file_path)
                    with open(file_path, 'w', encoding=encoding, errors='ignore') as f:
                        f.write(new_text)
                if next:
                    url = index + next[0]['href']
                else:
                    break


        except:
            traceback.print_exc()
            print('url=',url)
            sys.exit()
            # print(next)










