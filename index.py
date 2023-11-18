import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
import json
import html

def get_book_data_from_json_response(json_response):
    html_content = json_response[2]['data']
    unescaped_html = html.unescape(html_content)
    soup = BeautifulSoup(unescaped_html, "html.parser")
    return get_book_data_from_page(soup)

def robust_request(url, method='get', data=None, headers=None, max_retries=5, delay=3):
    retries = 0
    while retries < max_retries:
        try:
            if method == 'get':
                response = requests.get(url, headers=headers)
            elif method == 'post':
                response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()  # Raises HTTPError for bad status codes
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}, retrying in {delay} seconds...")
            time.sleep(delay)
            retries += 1
    raise Exception("Max retries exceeded")

def get_book_data_from_page(page_content):
    soup = BeautifulSoup(page_content, "html.parser")
    book_tags = soup.find_all('tr', class_=lambda x: x is not None and x != '')
    return [extract_book_data(book_tag) for book_tag in book_tags]

def extract_book_data(book_tag):
    doc_type = book_tag.find("a").text
    fin_year = book_tag.find_all("a")[1].text.strip()
    title = book_tag.find("span").find("a").text
    link = book_tag.find("span").find("a").get('href')
    return doc_type, fin_year, title, link

def get_last_page(soup):
    last_doc = soup.find("li", attrs="pager-last").find("a").get("href")
    return int(re.search(r'\d+', last_doc).group()) if re.search(r'\d+', last_doc) else None

def export_to_csv(book_data):
    df = pd.DataFrame(book_data, columns=['Document Type', 'Financial Year', 'Title', 'Link'])
    df.to_csv("books.csv", index=False)

def scrape_all_pages():
    initial_url = "https://budget.finance.go.ug/all-documents"
    ajax_url = "https://budget.finance.go.ug/views/ajax"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    initial_response = robust_request(initial_url, headers=headers)
    initial_soup = BeautifulSoup(initial_response.content, "html.parser")

    max_page = get_last_page(initial_soup)
    print(f"Total pages to scrape: {max_page}")
    all_data = get_book_data_from_page(initial_response.content)

    for page in range(1, max_page + 1):
        print(f"Scraping page {page}/{max_page}...")
        form_data = {
            "page": str(page),
            "view_name": "all_documents",
            "view_display_id": "page",
            "view_args": "",
            "view_path": "all-documents",
            "view_base_path": "all-documents",
            "view_dom_id": "3765012f0d8624a5f7ea889d196c9232",
            "pager_element": "0"
        }
        response = robust_request(ajax_url, method='post', data=form_data, headers=headers)
        json_response = json.loads(response.text)
        for item in json_response:
            if item["command"] == "insert":
                html_content = item["data"]
                page_data = get_book_data_from_json_response(item)
                all_data.extend(page_data)

        print(f"Page {page} scraped successfully.")
        time.sleep(1)  # Polite delay between requests

    export_to_csv(all_data)
    print("Scraping completed. Data exported to CSV.")

if __name__ == "__main__":
    scrape_all_pages()