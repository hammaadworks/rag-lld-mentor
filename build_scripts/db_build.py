import json
import os
from time import sleep

from bs4 import BeautifulSoup
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from requests_html import HTMLSession

from constants.constants import (NON_BREAKING_ELEMENTS, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, SENTENCE_LENGTH,
                                 MAX_BLANK_COUNT, RENDER_TIMEOUT, DEL_TAGS, SOUP_HTML_PARSER, FAISS_STORE)


# get url list to scrape
def get_url_list_to_scrape():
    with open('my_list.json', 'r') as file:
        loaded_list = json.load(file)
    return loaded_list


def html_to_text(soup, preserve_new_lines=True, strip_tags=None):
    if strip_tags is None:
        strip_tags = ['style', 'script', 'code']
    for element in soup(strip_tags):
        element.extract()
    if preserve_new_lines:
        for element in soup.find_all():
            if element.name not in NON_BREAKING_ELEMENTS:
                element.append('\n') if element.name == 'br' else element.append('\n\n')
    return soup.get_text(" ")


def strip_new_lines(text_list):
    while True:
        if text_list and not text_list[0].strip():
            text_list.pop(0)
        elif text_list and not text_list[-1].strip():
            text_list.pop(-1)
        else:
            break
    return text_list


def clean_text_content_list(text_list):
    cleaned_text_content_list = []
    cleaned_sentence = ''
    blank_count = 0

    # Remove leading and trailing whitespaces
    for text in text_list:
        text = text.strip()

        if text and len(text) < SENTENCE_LENGTH:
            # If the line is not blank and its length is less than 30
            cleaned_sentence += f' {text}'
        elif blank_count >= MAX_BLANK_COUNT or (text and len(text) > SENTENCE_LENGTH):
            # MAX_BLANK_COUNT or more consecutive blank lines or the line is not blank and its length > SENTENCE_LENGTH
            blank_count = 0
            cleaned_text_content_list.append(cleaned_sentence.strip() + '\n')
            cleaned_sentence = ''
            if text:
                cleaned_sentence += f' {text}'
        else:
            blank_count += 1

    # Append the last cleaned sentence if any
    if cleaned_sentence:
        cleaned_text_content_list.append(cleaned_sentence.strip() + '\n')
    cleaned_text_content_list = strip_new_lines(cleaned_text_content_list)
    return cleaned_text_content_list


# scrape the url for markdown
def scrape_url(url, index):
    if os.path.isfile(f'../scraped_data/{index}.txt'):
        with open(f'../scraped_data/{index}.txt', 'r', encoding='utf-8') as f:
            cleaned_content = f.read()
        return Document(page_content=cleaned_content, metadata={"source": url})

    session = HTMLSession()
    response = session.get(url)
    sleep(1)
    response.html.render(timeout=RENDER_TIMEOUT)
    soup = BeautifulSoup(response.html.html, SOUP_HTML_PARSER)
    session.close()

    for name in ['head', 'footer']:
        del_tag = soup.find(name=name)
        if del_tag is not None:
            del_tag.decompose()

    for name, class_ in DEL_TAGS:
        del_tag = soup.find(name=name, class_=class_)
        if del_tag is not None:
            del_tag.decompose()

    text_content = html_to_text(soup)
    cleaned_text_content_list = clean_text_content_list(text_content.split("\n"))
    cleaned_content = ''.join(cleaned_text_content_list)
    with open(f'../scraped_data/{index}.txt', 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    return Document(page_content=cleaned_content, metadata={"source": url})


# Build vector database
def run_db_build():
    documents = list()
    url_list_to_scrape = get_url_list_to_scrape()

    # PDF Documents
    pdf_documents = ['../data/lld_interview.pdf']
    for file in pdf_documents:
        loader = PyPDFLoader(file)
        loaded_documents = loader.load()
        documents.extend(loaded_documents)

    # Web Pages using requests-html
    for index, url in enumerate(url_list_to_scrape):
        try:
            total = len(url_list_to_scrape)
            documents.append(scrape_url(url, index))
            print(f"Done {index}/{total - 1}: {url}")
        except Exception as e:
            print(f"Unable to fetch url: {url} at index {index}>> {str(e)}")

    print("Building Vector DB")
    text_splitter = CharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    texts = text_splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'})
    vectorstore = FAISS.from_documents(texts, embeddings)
    vectorstore.save_local(f"../{FAISS_STORE}")


if __name__ == "__main__":
    run_db_build()
