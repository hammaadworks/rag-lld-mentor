import json
import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.NOTSET)
log = logging.getLogger(__name__)
log.setLevel(level=logging.NOTSET)
BASE_URL_LIST = ["https://lldcoding.com/",
                 "https://refactoring.guru/design-patterns"]
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/50.0.2661.102 Safari/537.36'}


def extract_urls_from_webpage(url) -> set:
    print(f"extract_urls_from_webpage: {url}")
    try:
        # Send a GET request to the URL
        response = requests.get(url=url, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad requests

        # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all URLs from the page
        urls = set()  # Using a set to avoid duplicates
        for tag in soup.find_all(['a', 'img', 'script', 'link']):
            # Extract URLs from 'a' (links), 'img' (images), 'script', and 'link' tags
            if 'href' in tag.attrs:
                urls.add(urljoin(url, tag['href']))
            if 'src' in tag.attrs:
                urls.add(urljoin(url, tag['src']))
        url_set = filter_urls(urls)
        print(f"{url_set=}")
        return url_set

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return set()


def extract_nested_urls(url) -> set:
    # Extract URLs from the initial webpage
    initial_urls: set = extract_urls_from_webpage(url)
    initial_urls = filter_urls(initial_urls)
    initial_urls_iterable = set(initial_urls)
    print(f"extract_nested_urls>> Internal URLs: {initial_urls}")
    # Iterate through each URL and extract nested URLs
    for initial_url in initial_urls_iterable:
        nested_urls = extract_urls_from_webpage(initial_url)
        initial_urls |= nested_urls
    print(f"{initial_urls=}")
    return initial_urls


def filter_urls(url_set) -> set:
    filtered_url_set = set()
    for extracted_url in url_set:
        if ('.js' not in extracted_url
                and '.css' not in extracted_url
                and '.png' not in extracted_url
                and '.jpeg' not in extracted_url
                and '.jpg' not in extracted_url
                and 'appmifile' not in extracted_url
                and any(d in extracted_url for d in BASE_URL_LIST)):
            filtered_url_set.add(extracted_url)
    print(f"{filtered_url_set=}")
    return filtered_url_set


def write_scraped_urls(webpage_url) -> list:
    # Extract all URLs, including nested ones
    print(f"{webpage_url=}")
    extracted_urls = extract_nested_urls(webpage_url)
    print("Total No. of URLS extracted:", len(extracted_urls))
    print(f"{extracted_urls=}")
    filtered_url_set = filter_urls(extracted_urls)
    print("Filtered URLs: ", len(filtered_url_set))
    print(f"{filtered_url_set=}")
    return list(filtered_url_set)


def extract_main():
    url_list = list()
    for base_url in BASE_URL_LIST:
        scraped_urls = write_scraped_urls(base_url)
        print(f"{scraped_urls=}")
        url_list.extend(scraped_urls)
    # Write to a json file
    print(f"Writing the URL list to file: {len(url_list)} urls")
    with open('my_list.json', 'w') as file:
        json.dump(url_list, file)


if __name__ == "__main__":
    extract_main()
