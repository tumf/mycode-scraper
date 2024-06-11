"""
This script processes local HTML files to download and localize their external web assets. It updates each HTML file to reference these assets locally, ensuring offline availability. The script handles CSS, JavaScript, and image files.
"""
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def download_file(url, save_dir):
    try:
        response = requests.get(url)
        response.raise_for_status()
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        save_path = os.path.join(save_dir, filename)
        # Skip if the file already exists
        if os.path.exists(save_path):
            print(f"File already exists, skipping: {save_path}")
            return filename
        with open(save_path, "wb") as file:
            file.write(response.content)
        return filename
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return None

def create_save_directory(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip("/").split("/")
    save_dir = os.path.join("localized-pages", parsed_url.netloc, *path_parts[:-1])
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    return save_dir

def download_assets(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    localized_html_file = os.path.join("localized-pages", html_file)
    os.makedirs(os.path.dirname(localized_html_file), exist_ok=True)

    for tag in soup.find_all(['link', 'script', 'img']):
        if tag.name == 'link' and 'href' in tag.attrs:
            url = tag['href']
            if url.startswith('http'):
                save_dir = create_save_directory(url)
                filename = download_file(url, save_dir)
                if filename:
                    # Convert asset save path to a relative path from the HTML file's location
                    relative_path = os.path.relpath(os.path.join(save_dir, filename), start=os.path.dirname(localized_html_file))
                    tag['href'] = relative_path
        elif tag.name == 'script' and 'src' in tag.attrs:
            url = tag['src']
            if url.startswith('http'):
                save_dir = create_save_directory(url)
                filename = download_file(url, save_dir)
                if filename:
                    relative_path = os.path.relpath(os.path.join(save_dir, filename), start=os.path.dirname(localized_html_file))
                    tag['src'] = relative_path
        elif tag.name == 'img' and 'src' in tag.attrs:
            url = tag['src']
            if url.startswith('http'):
                save_dir = create_save_directory(url)
                filename = download_file(url, save_dir)
                if filename:
                    relative_path = os.path.relpath(os.path.join(save_dir, filename), start=os.path.dirname(localized_html_file))
                    tag['src'] = relative_path

    with open(localized_html_file, 'w', encoding='utf-8') as file:
        file.write(str(soup))

    print(f"Saved offline version of {html_file} to {localized_html_file}")

def process_all_html_files(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                html_file = os.path.join(root, file)
                download_assets(html_file)

if __name__ == "__main__":
    html_directory = "saved_pages"  # Directory containing HTML files
    process_all_html_files(html_directory)
