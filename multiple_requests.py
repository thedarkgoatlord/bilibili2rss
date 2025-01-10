from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime,timedelta
import subprocess
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')

# 配置 ChromeDriver
service = Service('./chromedriver')

# 读取 up 主列表
UIDs = []
with open("./list_of_UID.txt",'r') as file:
    for line in file:
        UIDs.append(line[:-1])
file.close()
print("UIDs:",UIDs)

for uid in UIDs:
    driver = webdriver.Chrome(service=service,options=options)
    url = 'https://space.bilibili.com/'+uid+'/video'
    driver.get(url)
    print("getting url "+uid)

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
                if '小时前' in pub_date_raw:  # 检查是否为 "X小时前" 格式
                    hours_ago = int(pub_date_raw.replace('小时前', '').strip())
                    pub_date = datetime.now() - timedelta(hours=hours_ago)
                elif '-' in pub_date_raw:  # 检查是否为 "月-日" 或 "年-月-日" 格式
                    parts = pub_date_raw.split('-')
                    if len(parts) == 2:  # 月-日格式
                        month, day = map(int, parts)
                        pub_date = datetime(current_year, month, day)
                    elif len(parts) == 3:  # 年-月-日格式
                        pub_date = datetime.strptime(pub_date_raw, "%Y-%m-%d")
                    else:
                        pub_date = None  # 无法识别的格式
                else:
                    pub_date = None  # 格式不明
            else:
                pub_date = None  # 如果没有时间信息

            # 将日期转换为 RSS 标准格式（RFC 822 格式）
            pub_date_rss = pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT") if pub_date else None
        except Exception as e:
            print(f"解析发布日期出错: {e}")
            pub_date_rss = None

        # 提取缩略图
        img_element = item.select_one('img')
        img_url = f"https:{img_element['src']}" if img_element and 'src' in img_element.attrs else ''

        # 创建 RSS 项目
        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(f'<img src="{img_url}" alt="{title}"><br>发布日期: {pub_date_raw}')

        if pub_date_rss:
            fe.pubDate(pub_date_rss)
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