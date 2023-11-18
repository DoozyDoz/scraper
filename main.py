import requests as r
from bs4 import BeautifulSoup

import re
import pandas as pd

import time
import json
import html

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_book_data_from_json_response(json_response):
 html_content = json_response[2]['data']
 unescaped_html = html.unescape(html_content)
 return get_book_data_from_page(soup)

resp = r.get("https://budget.finance.go.ug/all-documents")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

def robust_request(url, method='get', data=None, headers=None, max_retries=5, delay=3, timeout=10):
 retries = 0
 while retries < max_retries:
  try:
   if method == 'get':
    response = r.get(url, headers=headers, timeout=timeout)
   elif method == 'post':
    response = r.post(url, data=data, headers=headers, timeout=timeout)
   if response.status_code == 200:
    return response
   else:
    raise Exception(f"HTTP Error: {response.status_code}")
  except (r.exceptions.RequestException, r.exceptions.Timeout) as e:
   logging.warning(f"Request failed: {e}, retrying in {delay} seconds...")
   time.sleep(delay)
   retries += 1
 raise Exception("Max retries exceeded")

def get_book_data_from_page(page_content):
 soup = BeautifulSoup(page_content, "html.parser")
 book_tags = soup.find_all('tr', class_=lambda x: x is not None and x != '')
 return [extract_book_data(book_tag) for book_tag in book_tags]

# def get_book_tags(): 
#  book_tags = soup.find_all('tr', class_=lambda x: x is not None and x != '')
#  book_data = [extract_book_data(book_tag) for book_tag in book_tags]
#  export_to_csv(book_data)


def extract_book_data(book_tag): 
  doc_type_elem = book_tag.find("a")
  fin_year_elem = book_tag.find_all("a")[1] if len(book_tag.find_all("a")) > 1 else None
  title_elem = book_tag.find("span").find("a") if book_tag.find("span") else None
  link_elem = title_elem.get('href') if title_elem else None

  doc_type = doc_type_elem.text if doc_type_elem else "No Document Type"
  fin_year = fin_year_elem.text.strip() if fin_year_elem else "No Financial Year"
  title = title_elem.text if title_elem else "No Title"
  link = link_elem if link_elem else "No Link"

  return doc_type, fin_year, title, link

def get_last_page(soup):
 last_doc = soup.find("li", attrs="pager-last").find("a").get("href")
 max_page = number = re.search(r'\d+', last_doc).group() if re.search(r'\d+', last_doc) else None
 return max_page

def export_to_csv(bd):
 df = pd.DataFrame(bd)
 df.to_csv("books.csv")

def scrape_all_pages():
 initial_url = "https://budget.finance.go.ug/all-documents"
 ajax_url = "https://budget.finance.go.ug/views/ajax"

 initial_response = robust_request(initial_url, headers=headers)
 initial_soup = BeautifulSoup(initial_response.content, "html.parser")

 max_page = get_last_page(initial_soup)
 print(f"Total pages to scrape: {max_page}")
 all_data = get_book_data_from_page(initial_response.content)


 # for page in range(1, 3):
 for page in range(91, int(max_page)):
  print(f"Scraping page {page}/{max_page}...")
  form_data = {
   "page": str(page),
   "view_name": "all_documents",
   "view_display_id": "page",
   "view_args": "",
   "view_path": "all-documents",
   "view_base_path": "all-documents",
   "view_dom_id":"3765012f0d8624a5f7ea889d196c9232",
   "pager_element":"0"
  }
  response = robust_request(ajax_url, method='post', data=form_data, headers=headers)
  json_response = json.loads(response.text)
  for item in json_response:
   if item["command"] == "insert":
    html_content = item["data"]
    page_data = get_book_data_from_page(html_content)
    all_data.extend(page_data)

  print(f"Page {page} scraped successfully.")
  # time.sleep(1) 

 export_to_csv(all_data)
 print("Scraping completed. Data exported to CSV.")

if __name__ == "__main__":
 scrape_all_pages()


