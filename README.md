# cool18_novel
收集禁忌书屋的小说

## 敏感词
`敏感词.TXT`用于禁止下载匹配的小说

>如果小说名有令人不适的字眼，或者说和XP不符，比如绿帽、猎奇等，则停止下载这本小说。
>敏感词根据个人需求修改

## 环境配置

版本：python3.8

```CONSOLE
pip install requests beautifulsoup4 urllib3==1.25.11 cchardet
```

## 爬取截至14天内的小说

禁忌书屋网站：https://www.cool18.com/bbs4/

- 执行脚本

```CONSOLE
python Collection_14_today_novel.py
```

## 爬取禁忌书屋从2010年至今的小说

- 执行脚本

```CONSOLE
python Collection_Complete_novel.py
```

>请控制main()函数的`semaphore_num = 50`并发数量，避免频繁访问堵塞服务器，导致封IP
>请放在24小时运行的电脑/服务器使用该脚本，每次同时访问50个请求，预计9天下载完成

>必须指定Proxy，main()的proxy变量指定为你的代理服务器地址，格式`http://127.0.0.1:7890`，如果网络无需代理即可正常访问禁忌书屋，请手动删除脚本的所有proxy变量
>查看代理服务器地址，如果你已安装clash，在主页上方可以看到端口

![image](https://user-images.githubusercontent.com/43485379/223296700-df9e0402-4c02-4688-80a8-cfc22e691022.png)

运行图：
![image](https://user-images.githubusercontent.com/43485379/223296808-fe8e4db3-96a0-4ab2-9c5a-a0b58ae4ceae.png)


