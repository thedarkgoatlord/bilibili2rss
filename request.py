from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timedelta, timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import subprocess

# Set up Chrome options
options = Options()
options.add_argument('--headless')

# Configure ChromeDriver
service = Service('./chromedriver')  # Update path if necessary
driver = webdriver.Chrome(service=service, options=options)
url = 'https://space.bilibili.com/478720594/video'
driver.get(url)

# Wait for page elements to load
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.small-item'))
    )
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select('li.small-item')
except Exception as e:
    print(f"Error waiting for page load: {e}")
    items = []

# Create RSS Feed
fg = FeedGenerator()
fg.title('Bilibili RSS Feed')
fg.link(href=url, rel='alternate')
fg.description('RSS feed for Bilibili videos')

# Define current year for date handling
current_year = datetime.now().year

# Create RSS items
for item in items:
    # Extract title
    title_element = item.select_one('a.title')
    title = title_element.text.strip() if title_element else 'No Title'

    # Extract link
    link_element = item.select_one('a.title')
    link = f"https:{link_element['href']}" if link_element and 'href' in link_element.attrs else ''

    # Extract publication date
    date_element = item.select_one('span.time')
    pub_date_raw = date_element.text.strip() if date_element else None

    # Extract thumbnail image
    img_element = item.select_one('img')
    img_url = f"https:{img_element['src']}" if img_element and 'src' in img_element.attrs else ''

    # Process the publication date
    try:
        if pub_date_raw:
            if '小时前' in pub_date_raw:  # "X hours ago" format
                hours_ago = int(pub_date_raw.replace('小时前', '').strip())
                pub_date = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            elif '-' in pub_date_raw:  # "Month-Day" or "Year-Month-Day" format
                parts = pub_date_raw.split('-')
                if len(parts) == 2:  # Month-Day format
                    month, day = map(int, parts)
                    pub_date = datetime(current_year, month, day, tzinfo=timezone.utc)
                elif len(parts) == 3:  # Year-Month-Day format
                    pub_date = datetime.strptime(pub_date_raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    pub_date = None  # Unrecognized format
            else:
                pub_date = None  # Unknown format
        else:
            pub_date = None  # No date available

        # Ensure pub_date has timezone info
        if pub_date:
            pub_date = pub_date.replace(tzinfo=timezone.utc)

        # Convert date to RSS format
        pub_date_rss = pub_date.strftime("%a, %d %b %Y %H:%M:%S %z") if pub_date else None
    except Exception as e:
        print(f"Error parsing publication date: {e}")
        pub_date_rss = None

    # Add to RSS entry if pub_date is available
    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=link)
    if img_url:
        fe.description(f'<img src="{img_url}" alt="{title}"><br>发布日期: {pub_date_rss if pub_date_rss else pub_date_raw}')
    else:
        fe.description(f'No image available<br>发布日期: {pub_date_rss if pub_date_rss else pub_date_raw}')
    if pub_date_rss:
        fe.pubDate(pub_date_rss)  # Use the date with timezone info
    elif pub_date:
        fe.pubDate(pub_date)  # Fallback to date without formatting

# Output RSS file
rss_file = './output/478720594.xml'
rss_feed = fg.rss_str(pretty=True)
with open(rss_file, 'wb') as f:
    f.write(rss_feed)

print(f'RSS feed generated: {rss_file}')
driver.quit()

# Git operations
try:
    # Add changes to the staging area
    subprocess.run(['git', 'add', rss_file], check=True)
    # Commit changes
    commit_message = f"Auto-update RSS feed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(['git', 'commit', '-m', commit_message], check=True)
    # Push to remote repository
    subprocess.run(['git', 'push'], check=True)
    print("RSS feed committed and pushed to the remote repository.")
except subprocess.CalledProcessError as e:
    print(f"Git operation failed: {e}")