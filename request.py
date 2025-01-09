from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import os
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread

# 配置 ChromeDriver
service = Service('/Users/cliviaminiata/Bilibili_crawler/chromedriver')  # 替换为您的路径
driver = webdriver.Chrome(service=service)

url = 'https://space.bilibili.com/478720594/video'
driver.get(url)

# 等待页面加载
driver.implicitly_wait(10)

# 获取动态加载后的 HTML
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
items = soup.select('li.small-item')  # 根据实际页面结构调整

# 创建 RSS Feed
fg = FeedGenerator()
fg.title('Bilibili RSS Feed')
fg.link(href=url, rel='alternate')
fg.description('RSS feed for Bilibili videos')

for item in items:
    # 提取标题、链接等信息
    title_element = item.select_one('a.title')
    title = title_element.text.strip() if title_element else '无标题'
    link_element = item.select_one('a.title')
    link = f"https:{link_element['href']}" if link_element and 'href' in link_element.attrs else ''
    date_element = item.select_one('span.time')
    pub_date = date_element.text.strip() if date_element else '未知时间'
    img_element = item.select_one('img')
    img_url = f"https:{img_element['src']}" if img_element and 'src' in img_element.attrs else ''

    # 创建 RSS 项目
    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=link)
    fe.description(f'<img src="{img_url}" alt="{title}"><br>发布日期: {pub_date}')

# 输出 RSS 文件
rss_file = '/Users/cliviaminiata/Documents/bilibili2rss/feed.xml'
rss_feed = fg.rss_str(pretty=True)
with open(rss_file, 'wb') as f:
    f.write(rss_feed)


print(f'RSS feed 已生成: {rss_file}')
driver.quit()
