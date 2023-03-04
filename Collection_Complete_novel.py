# -*- coding: utf-8 -*-
import os.path
import re
import sys
import time
import traceback
import cchardet
import requests
from bs4 import BeautifulSoup

encoding = ''

sensitive_words = []
with open('敏感词.TXT', 'r', encoding='utf-8') as f:
    [sensitive_words.append(word[:-1]) for word in f.readlines()]

index = 'https://www.cool18.com/bbs4/'


# 含有敏感词，返回False
def check_sensitive(input):
    if re.search('(.*?)(作者|送达者)', input):
        for sensitive_word in sensitive_words:
            if sensitive_word in re.search('(.*?)作者', input).group(1):
                return False
    else:
        for sensitive_word in sensitive_words:
            if sensitive_word in input:
                return False
    return True


# 去除非法字符
def rmsc(string):
    string = string.replace('\\', ' - ')
    string = string.replace('/', ' - ')
    string = string.replace(':', '：')
    string = string.replace('*', '•')
    string = string.replace('?', '？')
    string = string.replace('"', '\'')
    string = string.replace('<', '【]')
    string = string.replace('>', '】')
    string = string.replace('|', '-')
    string = string.replace('\t', ' ')
    string = string.replace('\r', ' ')
    string = string.replace('\n', ' ')
    string = string.strip()
    return string


# 正文去掉网页元素
def remove_html(text):
    text = re.sub(r'<font(.*?)font>', '', text)
    text = re.sub(r'<br/>', '\n', text)
    text = re.sub(r'<p>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<b>(.*?)</b>', '\n', text)
    text = text.replace("<pre>", '')
    text = text.replace("</pre>", '')
    return text


# 重复文件返回文件副本名
def return_copy_name(name):
    if os.path.exists(name):
        num = 0
        while os.path.exists(name):
            copy_num = re.search('(.*?)（(.*?)）.txt', name)
            if copy_num:
                if copy_num.group(2).isnumeric():
                    num += 1
                    name = copy_num.group(1) + ' - 副本（' + str(num) + '）.txt'
                else:
                    name = name[:-4] + ' - 副本（' + str(num) + '）.txt'
                    num += 1
            else:
                name = name[:-4] + ' - 副本（' + str(num) + '）.txt'
                num += 1
    return name


# 返回请求的网页元素
def request_url_source_code(url):
    HEADER = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0)'
                      ' Gecko/20100101 Firefox/106.0',
    }
    num = 0
    while num < 30:
        num += 1
        try:
            r = requests.get(url, headers=HEADER)
            global encoding
            encoding = cchardet.detect(r.content)['encoding']
            return BeautifulSoup(r.text, 'lxml')
        except:
            if num == 30:
                traceback.print_exc()
                print('超过最大重连次数')
                sys.exit()
            print(url + ' 获取失败，正在重连...')
            time.sleep(10 * num)


exclude_links = []


# 获取最新的最大文章数量
def get_max_num():
    num = request_url_source_code(index)
    limit_num = num.select_one('#d_list > ul > li > a:nth-child(1)>font[color="grey"]').parent['href']
    limit_num = int(re.search('tid\=(.*?)$', limit_num).group(1).strip())
    return limit_num


if __name__ == '__main__':
    max_num = get_max_num()

    num = 1
    # 一直爬到最新的小说...
    while num < max_num:
        Current_url = 'https://www.cool18.com/bbs4/index.php?app=forum&act=threadview&tid=' + str(num)
        num += 1
        # 如果网址已经加载过了，后缀加1
        for exclude_url in exclude_links:
            if exclude_url == Current_url:
                Current_url = 'https://www.cool18.com/bbs4/index.php?app=forum&act=threadview&tid=' + str(num)
                exclude_links.remove(exclude_url)
                break
        try:
            source_code = request_url_source_code(Current_url)
            content = source_code.select('td.show_content > pre')
            follow_up = source_code.select('body > table >  tr > td > ul li')
            if not source_code.select_one('head>script') and not source_code.select('td.show_content>p'):
                if content:
                    first_pre_article_content = remove_html(str(content[0])) + '\n'
                    article_name = source_code.select('td.show_content>center>font')[0].text
                    if check_sensitive(article_name):
                        article_filename = article_name + '.txt'
                        valid = False
                        if len(first_pre_article_content) > 0:
                            valid = True
                        follow_up_links = []  # 回帖列表初始化
                        if follow_up:  # 存在回帖
                            for li in follow_up:  # 遍历回帖，记录较多字符的回帖
                                new_list = []
                                new_a = li.select_one('a')

                                # 防止重复添加链接
                                exist_exclude_url = True
                                for link in exclude_links:
                                    if index + new_a['href'] == link:
                                        # 回帖链接添加到排除列表，下次遍历链接无需再次打开
                                        exist_exclude_url = False
                                if exist_exclude_url:
                                    exclude_links.append(index + new_a['href'])

                                # 检查文章大小
                                if int(re.search('\((.*?) bytes\)', new_a.next_sibling).group(1)) > 10000:
                                    Valid = True
                                    if check_sensitive(str(new_a.text)):
                                        new_ = []
                                        # new_.append(classify)
                                        new_.append(new_a.text)
                                        new_.append(index + new_a['href'])
                                        try:
                                            if isinstance(new_[0], str):
                                                follow_up_links.append(new_)
                                        except:
                                            pass
                        elif len(first_pre_article_content) < 1000:  # 字数少，跳过
                            valid = False
                        # 该页面字数较多，存为txt文件
                        if Valid:
                            if follow_up_links:
                                follow_up_links = follow_up_links[::-1]
                                bracket_exist = re.search('(.*?)(\(|（)(.*?)(\)|）)(.*?).txt', article_filename)
                                if bracket_exist:
                                    article_filename = bracket_exist.group(1) + bracket_exist.group(5) + '.txt'
                                # 打开回帖，将回帖内容加到列表中
                                for article_link in follow_up_links:
                                    article_source_code = request_url_source_code(article_link[1])
                                    article_bre = article_source_code.select('td.show_content > pre')
                                    article_text = remove_html(str(article_bre[0]))
                                    article_link.append(article_text)
                            if not os.path.exists('禁忌书屋'):
                                os.mkdir('禁忌书屋')
                            filepath = '禁忌书屋/' + rmsc(article_filename)

                            # 合并文章
                            text = article_name + '\n' + first_pre_article_content + '\n'
                            if follow_up_links:
                                for article in follow_up_links:
                                    text += '\n' + article[0] + '\n\n来源：' + article[1] + '\n' + article[2] + '\n'

                            # 如果有重复文件，文件大小一致则跳过，否则新建xx（1）.txt，xx（2）.txt之类的文件
                            if os.path.exists(filepath):
                                with open(filepath, 'rb') as f:
                                    exists_encoding = cchardet.detect(f.read())['encoding']
                                with open(filepath, 'r', encoding=exists_encoding) as f:
                                    file_len = len(f.read())
                                if file_len != len(text):
                                    filepath = '禁忌书屋/' + return_copy_name(rmsc(article_filename))
                                    with open(filepath, 'w', encoding=encoding, errors='ignore') as f:
                                        f.write(text)
                                        print(Current_url, '爬取完毕，还有',
                                              str(max_num - int(
                                                  re.search('tid\=(.*?)$', Current_url).group(1).strip())), '页')

                            else:
                                with open(filepath, 'w', encoding=encoding, errors='ignore') as f:
                                    f.write(text)
                                print(Current_url, '爬取完毕，还有',
                                      str(max_num - int(re.search('tid\=(.*?)$', Current_url).group(1).strip())), '页')
        except:
            traceback.print_exc()
            print(Current_url)
