import csv
import re
from collections import deque

from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

# Set up Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # To run Chrome in headless mode
chrome_options.add_argument("--no-sandbox")  # Required for running in Docker
chrome_options.add_argument("--disable-dev-shm-usage")  # Required for running in Docker

# Path to the Chrome WebDriver executable
webdriver_path = '/usr/local/bin/chromedriver'  # Adjust the path based on your system

# Initialize Chrome WebDriver with page load timeout
driver = webdriver.Chrome(executable_path=webdriver_path, options=chrome_options)
driver.set_page_load_timeout(30)  # Set page load timeout to 30 seconds

print("WebDriver initialized successfully")


def scrape_cnn_news(url):
    datas = []
    new_links = []  # Initialize new_links list

    try:
        driver.get(url)
    except TimeoutException:
        print("Timeout occurred while loading the page:", url)
        return datas, new_links

    html = driver.page_source
    article_soup = soup(html, 'html.parser')

    time_element = article_soup.find('div', class_='timestamp')
    published_date = time_element.get_text(strip=True) if time_element else "NaN"

    # Regular expression pattern to match the date pattern
    date_pattern = re.compile(
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2},\s\d{4}')

    # Find the date pattern in the published_date text
    match = date_pattern.search(published_date)

    # Extract the matched date if found
    if match:
        published_date = match.group()
    else:
        published_date = "NaN"

    headline_element = article_soup.find('h1', id='maincontent')
    headline = headline_element.get_text(strip=True) if headline_element else "NaN"

    publisher = "CNN"

    # Find the div element with class 'article-body'
    story_body_div = article_soup.find('div', class_='article__content')

    if story_body_div:
        # Find all <p> elements within the story body and concatenate their text content
        article_content = '\n'.join(paragraph.get_text(strip=True) for paragraph in story_body_div.find_all('p'))
    else:
        article_content = "NaN"

    pattern = re.compile(r'https://cnn.com/\d+/\d+/\d+/(?P<category>\w+)/')

    match = pattern.search(url)

    if match:
        category = match.group('category')
    else:
        pattern2 = re.compile(r'https://cnn.com/(\w+)/')
        match2 = pattern2.search(url)
        if match2:
            category = match2.group(1)
        else:
            category = "NaN"

    data = (published_date, headline, publisher, article_content, category)
    datas.append(data)

    container_div = article_soup.find('div', class_='container__field-links')
    if container_div:
        for link in container_div.find_all('a'):
            href = link.get('href')
            if href:
                links.append(href)

    return datas, links


# Starting point for scraping
driver.get("https://cnn.com/")
html = driver.page_source
b = soup(html, 'html.parser')

links = []
for news in b.find_all('a', attrs={'class': 'container__link'}):
    news_link = news.get('href') if news else None
    if news_link and "photo" not in news_link and "video" not in news_link:
        full_link = "https://cnn.com" + news_link
        if full_link not in links:
            print(full_link)
            links.append(full_link)

# Queue for BFS
queue = deque(links)
visited_links = set(links)
scraped_data = []

# BFS traversal
while len(scraped_data) < 100:
    current_link = queue.pop()
    print(len(queue))
    # Skip the link if it doesn't start with the desired prefix
    if not current_link.startswith("https://cnn.com"):
        continue

    print(f"Scraping: {current_link}")
    data, new_links = scrape_cnn_news(current_link)
    scraped_data.extend(data)
    # print(len(new_links))
    print(f"Total data collected: {len(scraped_data)}")

    for link in new_links:
        if link not in visited_links:
            visited_links.add(link)
            queue.append(link)
            print(len(queue))

    print("next")

# Save data to CSV
header = ["Published Date", "Headline", "Publisher", "Article Content", "Category"]
with open('cnn_news_articles.csv', 'a', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)
    writer.writerows(scraped_data)
print("done")
