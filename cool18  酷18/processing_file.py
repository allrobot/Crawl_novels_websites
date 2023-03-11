# -*- coding: utf-8 -*-
import  datetime, random, os, re, traceback, aiofiles, aiohttp, cchardet,asyncio
import sys
import time

from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

sensitive_words=''
if os.path.exists('敏感词.TXT'):
    with open('敏感词.TXT', 'r', encoding='utf-8') as f:
        sensitive_words = f'({f.read()})'.replace('\n', '|').replace('||', '')
        sensitive_words = re.sub('\|\|$', '', sensitive_words)
else:
    with open('../敏感词.TXT', 'r', encoding='utf-8') as f:
        sensitive_words = f'({f.read()})'.replace('\n', '|').replace('||', '')
        sensitive_words = re.sub('\|\|$', '', sensitive_words)

# 含有敏感词，返回False
async def check_sensitive(input):
    if re.search(f'(.*?){sensitive_words}(.*?)(作者|送达者|$)', input):
        return False
    else:
        return True

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
    text = re.sub(r'<font([^\t]*)font>', '', text)
    # text = re.sub(r'<center(.*?)center>', '', text)
    text = re.sub(r'<br/>', '\n', text)
    text = re.sub(r'<p(.*?)>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<b>(.*?)</b>', '\n', text)
    text = text.replace("<pre>", '')
    text = text.replace("<i>", '')
    text = text.replace("</pre>", '')
    return text




# 返回文件副本名
async def copy_name(filename):
    num = 0
    while os.path.exists(filename):
        copy_num = re.search('(.*?) - 副本（(.*?)）.txt', filename)
        num += 1
        if copy_num:
            if copy_num.group(2).isnumeric():
                num=int(copy_num.group(2))+1
                filename = copy_num.group(1) + ' - 副本（' + str(num) + '）.txt'
            else:
                filename = filename[:-4] + ' - 副本（' + str(num) + '）.txt'
        else:
            filename = filename[:-4] + ' - 副本（' + str(num) + '）.txt'
    return filename


# 用于保存文章，如果文件已存在，判断文件内容是否一致，不一致则新建文件副本保存内容
async def write_file(filename, content):
    content = await remove_html(content)
    try:
        if os.path.exists(filename):
            async with aiofiles.open(filename, 'rb') as f:
                encoding = cchardet.detect(await f.read())['encoding']
            async with aiofiles.open(filename, 'r', encoding=encoding, errors='ignore') as f:
                # 检查相似度
                loop = asyncio.get_running_loop()
                similarity_ratio = await loop.run_in_executor(None, fuzz.ratio, await f.read(), content)
                # 如果相似度高于95%，返回False
                if not similarity_ratio >= 95:
                    newname = await copy_name(filename)
                    # await loop.run_in_executor(None, os.rename, filename, newname)
                    async with aiofiles.open(newname, 'w', encoding='utf-8', errors='ignore') as file:
                        await file.write(content)
                        return True
                else:

                    return False
        else:
            async with aiofiles.open(filename, 'w', encoding='utf-8', errors='ignore') as file:
                await file.write(content)

                return True
    except:
        message = f'【{str(datetime.datetime.now())[:16]}】：write_file()函数\n' \
                  f'【{str(datetime.datetime.now())[:16]}】：文章开头\n\n{content[:100]}\n' \
                  f'【{str(datetime.datetime.now())[:16]}】：保存失败\n' \
                  f'【{str(datetime.datetime.now())[:16]}】：{traceback.format_exc()}\n'
        async with aiofiles.open('../错误日志.txt', 'a+') as file:
            await file.write(message)
        print(message)



# 保存文章
async def processing_data(html, new_dir_name,byte,del_bracket,index,Currect_tid):
    try:
        content = html.select('td.show_content > pre')
        follow_up = html.select('body > table >  tr > td > ul li')
        if content:
            link = Currect_tid
            tid_num=int(re.search('=\d+',link).group(0)[1:])
            first_pre_article_content = await remove_html(str(content[0])) + '\n'
            article_name = await del_illegal_words(html.select('td.show_content>center>font')[0].text)
            # 检测文章名是否包含敏感词
            if await check_sensitive(article_name):
                article_filename = new_dir_name+'\\'+article_name + '.txt'
                valid = False
                if len(first_pre_article_content) > 0:
                    valid = True
                follow_up_links = []  # 回帖列表初始化
                if follow_up:  # 存在回帖
                    for li in follow_up:  # 遍历回帖，记录较多字符的回帖
                        new_a = li.select_one('a')
                        # 检查文章大小
                        if int(byte.search(new_a.next_sibling).group(1)) > 10000:
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
                else:
                    if len(first_pre_article_content) < 2000:  # 字数少，跳过
                        valid = False

                # 该页面字数较多，存为txt文件
                if valid:
                    # 文章
                    text = article_name + '\n' + first_pre_article_content + '\n'
                    # 获取回帖中的文章，并且添加到text
                    if follow_up_links:
                        follow_up_links = follow_up_links[::-1]
                        # 重命名文章名，整合文章的小说名总不能带（1）之类的字
                        # bracket_exist = del_bracket.search(article_filename)
                        # if bracket_exist:
                        #     article_filename = bracket_exist.group(1) + bracket_exist.group(5) + '.txt'
                        # 打开回帖，将文章内容加到列表中
                        for article_link in follow_up_links:
                            follow_up_file=str(re.search('\d+',article_link[1]).group(0))+'.html'
                            try:
                                async with aiofiles.open(follow_up_file,'r',encoding='utf-8') as f:
                                     article_source_code=BeautifulSoup(await f.read(),'lxml')
                                     article_bre = article_source_code.select('td.show_content > pre')
                                     article_text = await remove_html(str(article_bre[0]))
                                     text = f'{text}\n\n{article_link[0]}\n' \
                                   f'来源：{article_link[1]}\n{article_text}\n'
                            # 回帖获取文章出现异常，记录报错信息
                            except:
                                message = f'【{str(datetime.datetime.now())[:16]}】：' \
                                          f'processing_data()函数------>回帖处理异常\n' \
                                          f'【{str(datetime.datetime.now())[:16]}】：' \
                                          f'{article_link[1]} 该回帖链接无法访问\n' \
                                          f'【{str(datetime.datetime.now())[:16]}】：取消保存文章{article_name}\n' \
                                          f'【{str(datetime.datetime.now())[:16]}】：' \
                                          f'{traceback.format_exc()}\n'
                                async with aiofiles.open('../错误日志.txt', 'a+') as file:
                                    await file.write(message)
                                    valid = False
                                    print('*' * 50)
                                    print(message)
                                    print('*' * 50)
                                    break


                    if valid:
                        file = await write_file(article_filename, text)

                        if not file:
                            print(
                                f'【{str(datetime.datetime.now())[:16]}】：tid={tid_num} 保存过了 '
                                f'无需保存 {article_name}'
                            )
                        else:
                            print(
                                f'【{str(datetime.datetime.now())[:16]}】：tid={tid_num} 已保存 '
                                f' {article_name}'
                            )
                        # os.exit(0)
    except:
        traceback.print_exc()
        message = f'【{str(datetime.datetime.now())[:16]}】：processing_data()函数\n' \
                  f'【{str(datetime.datetime.now())[:16]}】：文章处理发生异常\n' \
                  f'【{str(datetime.datetime.now())[:16]}】：{traceback.format_exc()}\n'
        async with aiofiles.open('../错误日志.txt', 'a+') as file:
            await file.write(message)
        print('*' * 50)
        print(message)
        print(f'发生异常的文章链接：{Currect_tid}')
        print('*'*50)
        # sys.exit()

# 消费者，处理网页资源
async def consumer(file_name,new_dir_name,semaphore,byte,del_bracket,index):
    async with semaphore:
        async with aiofiles.open(file_name,'r',encoding='utf-8',errors='ignore') as f:
            html=BeautifulSoup(await f.read(),'lxml')
        if not html.select_one('head>script') and not html.select_one('td.show_content>p'):
            # print(f'【{str(datetime.datetime.now())[:16]}】：正在处理文章{html[0]}')
            # 提取页面链接
            Currect_tid = f'https://www.cool18.com/bbs4/index.php?app=forum&act=threadview&tid={file_name[:-4]}'

            # 7200/60/60=2小时，超时处理
            try:
                await asyncio.wait_for(
                    processing_data(html, new_dir_name,byte, del_bracket, index, Currect_tid), 1800)
            except asyncio.TimeoutError:
                # 撰写错误报告
                message = f'【{str(datetime.datetime.now())[:16]}】：consumer()函数\n' \
                          f'【{str(datetime.datetime.now())[:16]}】：超过半小时，文章处理未完成处理\n' \
                          f'【{str(datetime.datetime.now())[:16]}】：未完成处理的文章链接：{Currect_tid}\n'
                async with aiofiles.open('../错误日志.txt', 'a+') as file:
                    await file.write(message)
                print(f'{message}')


async def consumers(concurrency_num: int,new_dir_name):
    byte = re.compile('\((\d+) bytes\)')
    del_bracket = re.compile('(.*?)(\(|（)(.*?)(\)|）)(.*?)$')
    index = 'https://www.cool18.com/bbs4/'


    print(f'【{str(datetime.datetime.now())[:16]}】：解析文章并行协程限制为{concurrency_num}条，队列已创建')
    semaphore = asyncio.Semaphore(concurrency_num)
    files=os.listdir('.')
    # for file_name in files:
        # if file_name.endswith('html'):
    tasks=[]
    for x in files:
        print(f'创建访问列表，列表已添加 {x} 文件',end='\r',flush=True)
        tasks.append(consumer(x,new_dir_name,semaphore,byte,del_bracket,index))
    await asyncio.gather(*tasks)





async def main():
    # 限制并行访问量为100
    concurrency_num = 1000

    new_dir_name=f'禁忌书屋小说 {str(datetime.datetime.now())[:10]}'
    if not os.path.exists(new_dir_name):
        os.mkdir(new_dir_name)
    target_path='禁忌书屋'
    if os.path.exists(target_path):
        os.chdir(target_path)
    else:
        print('禁忌书屋目录并不存在！请确保你已完整保存禁忌书屋的全部帖子')
        sys.exit()

    print(f'【{str(datetime.datetime.now())[:16]}】：目录已创建')
    await consumers(concurrency_num,new_dir_name)

async def main1():
    # 限制并行访问量为100
    concurrency_num = 1000

    new_dir_name=f'禁忌书屋小说 {str(datetime.datetime.now())[:10]}'
    if not os.path.exists(new_dir_name):
        os.mkdir(new_dir_name)
    target_path='禁忌书屋'
    temp_path=r'C:\Users\li\PycharmProjects\禁忌书屋'
    temp_new_dir=r'C:\Users\li\Downloads\禁忌书屋'
    if os.path.exists(temp_path):
        os.chdir(temp_path)
    else:
        print('禁忌书屋目录并不存在！请确保你已完整保存禁忌书屋的全部帖子')
        sys.exit()

    print(f'【{str(datetime.datetime.now())[:16]}】：目录已创建')
    await consumers(concurrency_num,temp_new_dir)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
