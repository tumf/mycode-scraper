"""
The provided Python script is a web crawler that uses Selenium WebDriver and the requests library to automate the process of logging into a website,
 crawling its pages, and downloading content such as HTML and images. 
"""
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from collections import deque
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

# Setup Selenium WebDriver using Chrome
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Navigate to the login page
login_url = "https://mycode.jp/login.html"
driver.get(login_url)
# Retrieve email and password from environment variables
email = os.getenv("MYCODE_EMAIL")
password = os.getenv("MYCODE_PASSWORD")

# Validate presence of email and password
if not email or not password:
    raise ValueError("Environment variables MYCODE_EMAIL and MYCODE_PASSWORD must be set")

# Input credentials into the form fields
username = driver.find_element(By.NAME, "email")
password = driver.find_element(By.NAME, "pwd")
username.send_keys(email)
password.send_keys(password)

# Click the login button (adjust selector as needed)
login_button = driver.find_element(By.XPATH, '//button[@id="btn-login"]')
login_button.click()

# Manual intervention required for reCAPTCHA
print("Please solve the reCAPTCHA manually and press Enter.")
input()

# Wait for login to complete
time.sleep(5)

# Extract session cookies
session_cookies = driver.get_cookies()

# Create a session in requests using the extracted cookies
session = requests.Session()
for cookie in session_cookies:
    session.cookies.set(cookie["name"], cookie["value"])

# Create directories to save crawled pages and images
save_dir = "saved_pages"
os.makedirs(save_dir, exist_ok=True)
image_dir = os.path.join(save_dir, "images")
os.makedirs(image_dir, exist_ok=True)

# Initialize URL queue and visited set for crawling
base_url = "https://mycode.jp/"
visited_urls = set()
url_queue = deque([base_url])

ignore_query_keys = ["int", "redirectUrl", "%3Factive_tab_data%3Dfactor-advice"]
# Crawl and save pages recursively
while url_queue:
    current_url = url_queue.popleft()
    if current_url in visited_urls:
        continue

    driver.get(current_url)
    time.sleep(2)  # Wait for the page to load completely

    # Convert URL to a safe file name for saving
    def url_to_file_name(url):
        parsed_url = urlparse(url)
        query = parsed_url.query.replace("/", "_")
        path = parsed_url.path.lstrip('/').replace('/', '_')
        if not path:
            path = 'index'
        if query:
            return f"{path.removesuffix('.html')}.{query}.html"
        return f"{path}"

    # Retrieve and save the page source
    page_source = driver.page_source
    file_name = f"{save_dir}/{url_to_file_name(current_url)}"
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(page_source)
    print(f"Saved: {file_name}")

    # Download images and replace their paths in the HTML
    images = driver.find_elements(By.TAG_NAME, "img")
    for img in images:
        img_url = img.get_attribute("src")
        img_url = urljoin(base_url, img_url)
        img_name = os.path.basename(urlparse(img_url).path)
        img_path = os.path.join(image_dir, img_name)

        # Download the image
        try:
            img_response = requests.get(img_url)
            if img_response.status_code == 200:
                with open(img_path, "wb") as img_file:
                    img_file.write(img_response.content)
                    # Replace image path in HTML
                page_source = page_source.replace(img_url, os.path.join("images", img_name))
            else:
                print(f"Failed to download image: {img_url}")
        except Exception as e:
            print(e)

    # Update and re-save the HTML file with new image paths
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(page_source)

    # Add internal links to the queue
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        link_url = link.get_attribute("href")
        if not link_url:
            continue
        parsed_url = urlparse(link_url)
        query_items = parse_qs(parsed_url.query)
        filtered_query_items = {k: v for k, v in query_items.items if k not in ignore_query_keys}
        filtered_query = urlencode(filtered_query_items, doseq=True)
        clean_url = parsed_url._replace(fragment='', query=filtered_query).geturl()
        if clean_url and base_url in clean_url and clean_url not in visited_urls:
            if parsed_url.path.startswith("/my"):
                url_queue.append(clean_url)

    visited_urls.add(current_url)

# Close the browser
driver.quit()
