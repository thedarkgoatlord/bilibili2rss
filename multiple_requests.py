from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import subprocess
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置 ChromeDriver
service = Service('./chromedriver')
driver = webdriver.Chrome(service=service)

# 读取 up 主列表
UIDs = []
with open("list_of_UID.txt",'r') as file:
    for line in file:
        UIDs.append(line[:-1])
file.close()
print("UIDs:",UIDs)

for uid in UIDs:
    driver = webdriver.Chrome(service=service)
    url = 'https://space.bilibili.com/'+uid+'/video'
    driver.get(url)
    print("getting url "+uid)
    # 等待页面加载
    driver.implicitly_wait(10000000)

    # 获取动态加载后的 HTML
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.small-item'))
        )
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('li.small-item')
    except Exception as e:
        print(f"等待加载时出错: {e}")

    print(items)
    # 创建 RSS Feed
    fg = FeedGenerator()
    fg.title(uid+" RSS feed")
    fg.link(href=url, rel='alternate')
    fg.description('RSS feed for '+uid)
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
            current_year = datetime.now().year
            if pub_date_raw:
                if '-' in pub_date_raw:  # 检查是否为月-日格式
                    parts = pub_date_raw.split('-')
                    if len(parts) == 2:  # 月-日格式
                        month, day = map(int, parts)
                        pub_date = datetime(current_year, month, day).strftime("%a, %d %b %Y 00:00:00 GMT")
                    else:  # 年-月-日格式
                        pub_date = datetime.strptime(pub_date_raw, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 GMT")
                else:
                    pub_date = None  # 如果格式不明，保留为空
            else:
                pub_date = None
        except ValueError:
            pub_date = None  # 处理异常情况

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
    rss_file = './output/'+uid+'.xml'
    rss_feed = fg.rss_str(pretty=True)
    with open(rss_file, 'wb') as f:
        f.write(rss_feed)

    print(f'RSS feed 已生成: {rss_file}')
    driver.quit()


# Git 操作
try:
    # 添加更改到暂存区
    subprocess.run(['git', 'add', rss_file], check=True)
    # 提交更改
    commit_message = f"Auto-update RSS feed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(['git', 'commit', '-m', commit_message], check=True)
    # 推送到远程仓库
    subprocess.run(['git', 'push'], check=True)
    print("RSS feed 已提交并推送到远程仓库。")
except subprocess.CalledProcessError as e:
    print(f"Git 操作失败: {e}")