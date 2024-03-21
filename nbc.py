import csv
from collections import deque

from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Set up Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # To run Chrome in headless mode
chrome_options.add_argument("--no-sandbox")  # Required for running in Docker
chrome_options.add_argument("--disable-dev-shm-usage")  # Required for running in Docker

# Path to the Chrome WebDriver executable
webdriver_path = '/usr/local/bin/chromedriver'  # Adjust the path based on your system

# Initialize Chrome WebDriver
driver = webdriver.Chrome(executable_path=webdriver_path, options=chrome_options)

print("WebDriver initialized successfully")


def scrape_nbc_news(url):
    datas = []
    driver.get(url)
    html = driver.page_source
    article_soup = soup(html, 'html.parser')

    time_element = article_soup.find('time', {'class': 'relative z-1'})
    published_date = time_element['datetime'].split('T')[0] if time_element else "NaN"

    headline_element = article_soup.find('h1', {'class': 'article-hero-headline__htag'})
    headline = headline_element.text.strip() if headline_element else "NaN"

    publisher = "NBC News"

    article_content = ""
    for news in article_soup.findAll('div', {'class': 'article-body__content'}):
        article_content += news.text.strip()

    categories_element = article_soup.find('span', {'data-testid': 'unibrow-text'})
    category = categories_element.text.strip() if categories_element else "NaN"

    data = (published_date, headline, publisher, article_content, category)
    datas.append(data)

    links = []
    for link in article_soup.select('a[href*="https://www.nbcnews.com/"]'):
        if link['href'].startswith("https://www.nbcnews.com/news/"):
            links.append(link['href'])

    return datas, links


# Starting point for scraping
driver.get("https://www.nbcnews.com/")
html = driver.page_source
b = soup(html, 'html.parser')

links = []
for news in b.findAll('div', {'class': 'standard-layout__container-top'}):
    news_link = news.a['href']
    links.append(news_link)

print("First layer done")

# Queue for BFS
queue = deque(links)
visited_links = set(links)
scraped_data = []

# BFS traversal
while queue and len(scraped_data) < 1000:
    current_link = queue.popleft()
    print(f"Scraping: {current_link}")
    data, new_links = scrape_nbc_news(current_link)
    scraped_data.extend(data)
    print(f"Total data collected: {len(scraped_data)}")

    for link in new_links:
        if link not in visited_links:
            visited_links.add(link)
            queue.append(link)

# Save data to CSV
header = ["Published Date", "Headline", "Publisher", "Article Content", "Category"]
with open('nbc_news_articles.csv', 'a', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)
    writer.writerows(scraped_data)
