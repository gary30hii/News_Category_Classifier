import csv
from collections import deque

from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import re

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


def scrape_abc_news(url):
    datas = []
    new_links = []  # Initialize new_links list

    try:
        driver.get(url)
    except TimeoutException:
        print("Timeout occurred while loading the page:", url)
        return datas, new_links

    html = driver.page_source
    article_soup = soup(html, 'html.parser')

    time_element = article_soup.find('div', class_='xAPpq ZdbeE jTKbV pCRh')
    published_date = time_element.get_text(strip=True) if time_element else "NaN"

    headline_element = article_soup.find('h1', class_='vMjAx')
    headline = headline_element.get_text(strip=True) if headline_element else "NaN"

    publisher = "ABC News"

    # Find the div element with id 'story-body'
    story_body_div = article_soup.find('div', class_='xvlfx ZRifP TKoO eaKKC bOdfO ')

    if story_body_div:
        # Find all <p> elements within the story body and concatenate their text content
        article_content = '\n'.join(paragraph.get_text(strip=True) for paragraph in story_body_div.find_all('p'))
    else:
        article_content = "NaN"

    # Pattern to match the part after the link
    pattern = re.compile(r'https://abcnews.go.com/(\w+)/')

    # Search for the pattern in the URL
    match = pattern.search(url)

    # Extract the first word after the link if there is a match
    if match:
        category = match.group(1)
    else:
        category = "NaN"

    data = (published_date, headline, publisher, article_content, category)
    datas.append(data)

    links = []
    for link in article_soup.select('a[href*="https://abcnews.go.com"]'):
        if url.startswith("https://abcnews.go.com/") and not any(
                excluded_url in url for excluded_url in ["/live", "/videos", "/pictures"]):
            links.append(link['href'])

    return datas, links


# Starting point for scraping
driver.get("https://abcnews.go.com/")
html = driver.page_source
b = soup(html, 'html.parser')

links = []
for news in b.find_all('a', attrs={'class': 'AnchorLink'}):
    # Check if 'href' attribute exists before accessing it
    if 'href' in news.attrs:
        news_link = news['href']
        if news_link.startswith("https://abcnews.go.com/"):
            links.append(news_link)
            print(news_link)

print("First layer done")

# Queue for BFS
queue = deque(links)
visited_links = set(links)
scraped_data = []

# BFS traversal
while queue and len(scraped_data) < 1000:
    current_link = queue.popleft()

    # Skip the link if it doesn't start with the desired prefix
    if not current_link.startswith("https://abcnews.go.com/") or "photos" in current_link:
        continue

    print(f"Scraping: {current_link}")
    data, new_links = scrape_abc_news(current_link)
    scraped_data.extend(data)
    print(f"Total data collected: {len(scraped_data)}")

    for link in new_links:
        if link not in visited_links:
            visited_links.add(link)
            queue.append(link)

# Save data to CSV
header = ["Published Date", "Headline", "Publisher", "Article Content", "Category"]
with open('abc_news_articles.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)
    writer.writerows(scraped_data)

print("done")
