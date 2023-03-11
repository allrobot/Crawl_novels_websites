# -*- coding: utf-8 -*-
import  datetime, random, os, re, traceback, aiofiles, aiohttp, asyncio,curses
import sys
from bs4 import BeautifulSoup

import processing_file


# 返回请求网页的源代码
async def fetch(session, url, contype,proxy=''):
    # 错误异常处理，如果超过1小时未请求到该网页资源，则抛出None
    error_counter = 0
    while True:
        error_counter += 1
        try:
            params = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0)'
                              ' Gecko/20100101 Firefox/106.0',
            }
            async with session.get(url, params=params, proxy=proxy) as response:
                # print(f'【{str(datetime.datetime.now())[:16]}】：正在访问{url}')
                encoding=contype.search(response.headers.get('Content-Type'))
                if encoding:
                    encoding=encoding.group(1)
                else:
                    encoding=None
                return [encoding,await response.text()]
        # 连接异常处理
        except aiohttp.ClientConnectorError or aiohttp.ClientTimeout or ConnectionResetError:
            if error_counter > 1000:
                message = f'【{str(datetime.datetime.now())[:16]}】：fetch()函数\n' \
                          f'【{str(datetime.datetime.now())[:16]}】：无法连接 {url}\n'
                async with aiofiles.open('../错误日志.txt', 'a+') as file:
                    await file.write(message)
                print('*'*50)
                print(message)
                print('*' * 50)

                return [url, None]
            else:
                print('*' * 50)
                print(f'【{str(datetime.datetime.now())[:16]}】：{url} 链接已超时，正在重试中...',end='\r',flush=True)
                print('*' * 50)
        # 其它异常处理
        except:
            if error_counter > 1000:
                message = f'【{str(datetime.datetime.now())[:16]}】：fetch()函数\n' \
                          f'【{str(datetime.datetime.now())[:16]}】：无法连接 {url}\n' \
                          f'【{str(datetime.datetime.now())[:16]}】：{traceback.format_exc()}\n'
                async with aiofiles.open('../错误日志.txt', 'a+') as file:
                    await file.write(message)
                print('*' * 50)
                print(message)
                print('*' * 50)
                return [url, None]
        await asyncio.sleep(random.randrange(5, 20))

# 生产函数，通过semaphore控制访问量，把获取的html添加到queue供消费函数访问
async def producer(session, url, semaphore, end_num,contype,proxy=''):
    tid=end_num.search(url).group(0)[4:]
    # 并发量，运行多个producer协程确保在semaphore控制的范围内
    async with semaphore:
        try:
            html = await asyncio.wait_for(fetch(session, url, contype,proxy), 12000.0)
            print(f'【{str(datetime.datetime.now())[:16]}】：已访问{url}',end='\r',flush=True)
            if not BeautifulSoup(html[1],'lxml').select_one('head>script'):
                async with aiofiles.open(f'{tid}.html', 'w',encoding=html[0]) as f:
                    await f.write(html[1])
                print(f'【{str(datetime.datetime.now())[:16]}】：已经保存{url}',end='\r',flush=True)

            # await queue.put(html)
        except asyncio.TimeoutError:
            message = f'【{str(datetime.datetime.now())[:16]}】：producer()函数\n' \
                      f'【{str(datetime.datetime.now())[:16]}】：半小时未成功连接，异常链接\n'
            async with aiofiles.open('../错误日志.txt', 'a+') as file:
                await file.write(message)
            print(message)




async def producers(concurrency_num: int):
    # 获取禁忌书屋网页编号
    end_num = re.compile('tid=\d+')
    # 获取网页编码
    contype = re.compile(r'charset=([\w-]+)')
    
    # 代理服务器
    proxy = 'http://127.0.0.1:7890'
    # 禁忌书屋主页
    index_url = 'https://www.cool18.com/bbs4/'
    # file_queue = asyncio.Queue(maxsize=2000)
    print(f'【{str(datetime.datetime.now())[:16]}】：并行访问量限制为{concurrency_num}，队列已创建')
    async with aiohttp.ClientSession() as session:
        index = 0
        num=0
        semaphore = asyncio.Semaphore(concurrency_num)
        index_url_code=BeautifulSoup((await fetch(session, index_url,contype, proxy=proxy))[1],'lxml')
        if index_url_code:
            newest_max_num = index_url_code \
            .select_one('#d_list > ul > li > a:nth-child(1)>font[color="grey"]') \
            .parent['href']
            newest_max_num = int(re.search('tid\=(.*?)$', newest_max_num).group(1).strip())
        else:
            f'【{str(datetime.datetime.now())[:16]}】：十分钟内未成功连接，请检查网络'
            sys.exit()
        tasks = []
        # 创建队列
        for i in range(index, newest_max_num+1):
            print(f'正在创建访问列表中...已添加第{num}页',end='\r',flush=True)
            num+=1
            url = f'https://www.cool18.com/bbs4/index.php?app=forum&act=threadview&tid={i}'
            tasks.append(producer( session, url, semaphore, end_num,contype,proxy))
        print(f'【{str(datetime.datetime.now())[:16]}】：爬虫程序开始运行')
        await asyncio.gather(*tasks)


async def main():
    # 限制并行访问量为100
    concurrency_num = 1000

    dir_name=f'禁忌书屋'
    processing_file.dir_name=dir_name
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    
    os.chdir(dir_name)
    print(f'【{str(datetime.datetime.now())[:16]}】：{dir_name} 目录已创建')
    await producers(concurrency_num)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
