# -*- coding: utf-8 -*-
import asyncio
import datetime
import os
import re
import socket
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import aiofiles
from aiohttp.resolver import AsyncResolver
import aiohttp
import cchardet
import requests

from bs4 import BeautifulSoup

with open('敏感词.TXT', 'r', encoding='utf-8') as f:
    sensitive_words = '('
    for word in f.readlines():
        sensitive_words = sensitive_words + word[:-1] + '|'
sensitive_words = sensitive_words[:-1] + ')'


# 去除非法字符
async def del_illegal_words(string):
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
    string = string.replace('\r', '')
    string = string.replace('\n', '')
    string = string.strip()
    return string


# 正文去掉网页元素
async def remove_html(text):
    text = re.sub(r'<font(.*?)font>', '', text)
    text = re.sub(r'<br/>', '\n', text)
    text = re.sub(r'<p>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<b>(.*?)</b>', '\n', text)
    text = text.replace("<pre>", '')
    text = text.replace("</pre>", '')
    return text


# 含有敏感词，返回False
async def check_sensitive(input):
    if re.search(f'(.*?){sensitive_words}(.*?)(作者|送达者|$)', input):
        return False
    else:
        return True


# 返回文件副本名
async def copy_name(filename):
    num = 0
    while os.path.exists(filename):
        copy_num = re.search('(.*?)（(.*?)）.txt', filename)
        num += 1
        if copy_num:
            if copy_num.group(2).isnumeric():
                filename = copy_num.group(1) + ' - 副本（' + str(num) + '）.txt'
            else:
                filename = filename[:-4] + ' - 副本（' + str(num) + '）.txt'
        else:
            filename = filename[:-4] + ' - 副本（' + str(num) + '）.txt'
    return filename


# 用于保存文章，如果文件已存在，判断文件内容是否一致，不一致则重命名文件保存内容
async def write_file(filename, content):
    content = await remove_html(content)
    if os.path.exists(filename):
        async with aiofiles.open(filename, 'rb') as f:
            encoding = cchardet.detect(await f.read())['encoding']
        async with aiofiles.open(filename, 'r', encoding=encoding, errors='ignore') as f:
            if await f.read() != content:
                newname = await copy_name(filename)
                # await loop.run_in_executor(None, os.rename, filename, newname)
                async with aiofiles.open(newname, 'w', errors='ignore') as file:
                    await file.write(content)
    else:
        async with aiofiles.open(filename, 'w', errors='ignore') as file:
            await file.write(content)


async def fetch(session, url, semaphore, proxy):
    error = 0
    while error < 30:
        error += 1
        try:
            params = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0)'
                              ' Gecko/20100101 Firefox/106.0',
            }
            async with semaphore:
                async with session.get(url, params=params, proxy=proxy) as response:
                    source_code = BeautifulSoup(await response.text(), 'lxml')
                    # loop.run_in_executor()
                    # print(f'正在访问{url}中。。。')
                    await article_save(source_code, session, semaphore, proxy, url)
                    error = 30

        except:
            if not error < 30:
                message = f'【{datetime.datetime.now()}】：无法连接 {url}\n错误日志: {traceback.format_exc()}\n'
                async with aiofiles.open('../错误日志.txt', 'a+') as file:
                    await file.write(message)
                print(message)


async def get_link_pre(session, url, semaphore, proxy):
    error = 0
    while error < 30:
        error += 1
        try:
            params = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0)'
                              ' Gecko/20100101 Firefox/106.0',
            }
            async with semaphore:
                async with session.get(url, params=params, proxy=proxy) as response:
                    source_code = BeautifulSoup(await response.text(), 'lxml')
                    return source_code
        except:
            if not error < 30:
                message = f'【{datetime.datetime.now()}】：无法连接 {url}\n错误日志: {traceback.format_exc()}\n'
                async with aiofiles.open('../错误日志.txt', 'a+') as file:
                    await file.write(message)
                print(message)


async def get_max(session, url, proxy):
    error = 0
    while error < 30:
        error += 1
        try:
            params = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0)'
                              ' Gecko/20100101 Firefox/106.0',
            }
            async with session.get(url, params=params, proxy=proxy) as response:
                source_code = BeautifulSoup(await response.text(), 'lxml')
                max_num = source_code.select_one('#d_list > ul > li > a:nth-child(1)>font[color="grey"]').parent[
                    'href']
                return int(re.search('tid\=(.*?)$', max_num).group(1).strip())

        except:
            if not error < 30:
                message = f'【{datetime.datetime.now()}】：无法连接 {url}\n错误日志: {traceback.format_exc()}\n'
                async with aiofiles.open('../错误日志.txt', 'a+') as file:
                    await file.write(message)
                print(message)


'''
提取正文进行一些操作
提取某元素的正文，查看是否有回帖
    存在回帖，提取里面的文章
合并文章并且保存
'''
byte = re.compile('\d+')
del_bracket = re.compile('(.*?)(\(|（)(.*?)(\)|）)(.*?)$')
end_num = re.compile('tid=(\d+)')
index = 'https://www.cool18.com/bbs4/'


async def article_save(source_code, session, semaphore, proxy, Currect_url):
    try:
        content = source_code.select('td.show_content > pre')
        follow_up = source_code.select('body > table >  tr > td > ul li')

        # 判断网址是否合法的文章
        if not source_code.select_one('head>script') and not source_code.select('td.show_content>p'):
            if content:
                first_pre_article_content = await remove_html(str(content[0])) + '\n'
                article_name = source_code.select('td.show_content>center>font')[0].text
                if await check_sensitive(article_name):
                    article_filename = await del_illegal_words(article_name) + '.txt'
                    valid = False
                    if len(first_pre_article_content) > 0:
                        valid = True
                    follow_up_links = []  # 回帖列表初始化
                    if follow_up:  # 存在回帖
                        for li in follow_up:  # 遍历回帖，记录较多字符的回帖
                            new_a = li.select_one('a')
                            # 检查文章大小
                            if int(byte.search(new_a.next_sibling).group(0)) > 10000:
                                valid = True
                                if await check_sensitive(str(new_a.text)):
                                    new_ = []
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
                    if valid:
                        # 文章字符串
                        text = article_name + '\n' + first_pre_article_content + '\n'
                        if follow_up_links:
                            follow_up_links = follow_up_links[::-1]
                            bracket_exist = del_bracket.search(article_filename)
                            if bracket_exist:
                                article_filename = bracket_exist.group(1) + bracket_exist.group(5) + '.txt'
                            # 打开回帖，将文章内容加到列表中
                            for article_link in follow_up_links:
                                article_source_code = await asyncio.ensure_future(
                                    get_link_pre(session, article_link[1], semaphore, proxy))
                                article_bre = article_source_code.select('td.show_content > pre')
                                article_text = await remove_html(str(article_bre[0]))
                                text += '\n' + article_link[0] + '\n\n来源：' + article_link[
                                    1] + '\n' + article_text + '\n'

                        await write_file(article_filename, text)

                        print(f'{Currect_url} 已访问\n已保存 {article_name}\t')

    except:
        traceback.print_exc()
        message = f'【{datetime.datetime}】：{traceback.format_exc()}\n' + Currect_url + '\n'
        async with aiofiles.open('../错误日志.txt', 'a+') as file:
            await file.write(message)
        print(Currect_url)
        # sys.exit()


async def main():
    proxy = 'http://127.0.0.1:1162'
    new_file = await del_illegal_words(f'禁忌书屋 {str(datetime.datetime.now())[:-16]}')
    if not os.path.exists(new_file):
        os.mkdir(new_file)
    os.chdir(new_file)
    semaphore_num = 50
    semaphore = asyncio.Semaphore(semaphore_num)
    async with aiohttp.ClientSession() as session:
        tasks = []
        # 获取最新的页数
        max_index = await asyncio.ensure_future(get_max(session, index, semaphore, proxy))
        index_num = 0
        while index_num < max_index:
            if index_num + 600 >= max_index:
                index_num += (max_index - index_num)
            else:
                index_num += 600

            for i in range(index_num - 600, index_num):
                print(f'正在创建访问列表中...已添加第{i}页', end='\r', flush=True)
                url = f'https://www.cool18.com/bbs4/index.php?app=forum&act=threadview&tid={i}'
                tasks.append(asyncio.ensure_future(fetch(session, url, semaphore, proxy)))
            await asyncio.gather(*tasks)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
