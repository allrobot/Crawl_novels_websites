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
