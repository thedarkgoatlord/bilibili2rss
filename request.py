from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime


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
# 创建 RSS 项目
for item in items:
    # 提取标题
    title_element = item.select_one('a.title')
    title = title_element.text.strip() if title_element else '无标题'

    # 提取链接
    link_element = item.select_one('a.title')
    link = f"https:{link_element['href']}" if link_element and 'href' in link_element.attrs else ''

    # 提取发布日期
    date_element = item.select_one('span.time')
    pub_date_raw = date_element.text.strip() if date_element else None

    # 将发布日期转换为 RSS 标准格式
    try:
        if pub_date_raw:
            # 假设日期格式类似于 "2021-11-30"
            pub_date = datetime.strptime(pub_date_raw, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 GMT")
        else:
            pub_date = None
    except ValueError:
        pub_date = None  # 如果日期格式不匹配，保留为空

    # 提取缩略图
    img_element = item.select_one('img')
    img_url = f"https:{img_element['src']}" if img_element and 'src' in img_element.attrs else ''

    # 创建 RSS 项目
    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=link)
    fe.description(f'<img src="{img_url}" alt="{title}"><br>发布日期: {pub_date_raw}')

    if pub_date:
        fe.pubDate(pub_date)
# 输出 RSS 文件
rss_file = '/Users/cliviaminiata/Documents/bilibili2rss/feed.xml'
rss_feed = fg.rss_str(pretty=True)
with open(rss_file, 'wb') as f:
    f.write(rss_feed)


print(f'RSS feed 已生成: {rss_file}')
driver.quit()
