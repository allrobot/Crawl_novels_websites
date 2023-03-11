# cool18_novel
收集禁忌书屋的小说

## 敏感词
`敏感词.TXT`用于禁止下载匹配的小说

>如果小说名有令人不适的字眼，或者说和XP不符，比如绿帽、猎奇等，则停止下载这本小说。
>敏感词根据个人需求修改

## 环境配置

版本：python3.8

```CONSOLE
pip install beautifulsoup4 urllib3==1.25.11 cchardet aiofiles aiohttp fuzzywuzzy
```

## cool18

爬取禁忌书屋

- 执行脚本

```CONSOLE
python Collection_Complete_novel.py
```

已收集禁忌书屋从2010年至今的帖子源码：

>请控制main()的变量concurrency_num值，避免频繁访问堵塞服务器，导致封IP
>下载速率为1~2MB/s

>必须指定Proxy，main()的proxy变量指定为你的代理服务器地址，默认`http://127.0.0.1:7890`，如果网络无需代理即可正常访问禁忌书屋，请设proxy = ''
>查看代理服务器地址，如果你已安装clash，在主页上方可以看到端口



