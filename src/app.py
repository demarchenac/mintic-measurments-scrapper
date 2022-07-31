from typing import Dict, List
from requests import head
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.remote.webelement import WebElement

import re
import time
import shutil
import logging

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


# URL to scrape.
SCRAPE_URL = 'https://gobiernodigital.mintic.gov.co/portal/Mediciones/'


def folder_setup() -> str:
    # Download folder.
    cwd = Path.cwd()
    download_folder = (cwd / './downloads').resolve()

    shutil.rmtree(download_folder)

    Path(download_folder).mkdir(exist_ok=True)

    return str(download_folder)


def init_driver(donwload_folder: str, headless=False) -> ChromeDriver:
    # Navigation options.
    options = webdriver.ChromeOptions()
    options.add_argument('--log-level=5')
    options.add_argument('--disable-extensions')
    if headless:
        options.add_argument('--headless')
    else:
        options.add_argument('--start-maximized')
        options.add_experimental_option('detach', True)

    driver = webdriver.Chrome(service=ChromeService(
        ChromeDriverManager().install()), options=options)

    # Set download folder
    params = {'behavior': 'allow', 'downloadPath': donwload_folder}
    driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

    driver.get(SCRAPE_URL)
    return driver


def document_formatter(document: WebElement) -> Dict[str, str]:
    text = document.text
    classes = document.get_attribute('class')
    unique_class = classes.split(' ')[-2]

    formatted = {
        "text": text,
        "class": unique_class
    }

    return formatted


def filter_docs(document: Dict[str, str]) -> bool:
    keyword = 'resultados'
    includesKeyword = keyword in document["text"].lower()

    numbersInText = [int(match)
                     for match in re.findall(r'\b\d+\b', document['text'])]
    isGreaterThan2017 = False
    if(len(numbersInText) > 0):
        isGreaterThan2017 = numbersInText[0] > 2017

    return includesKeyword and isGreaterThan2017


def get_docs_info(driver: ChromeDriver) -> List[Dict[str, str]]:
    # Navigate to tab.
    driver.find_element(By.LINK_TEXT, 'ÍNDICE TERRITORIAL').click()

    # Get docs.
    docs = driver.find_elements(By.CSS_SELECTOR, '.bajardoc.format-xlsx')
    formatted_docs = list(map(document_formatter, docs))
    filtered_docs = list(filter(filter_docs, formatted_docs))

    return filtered_docs


def download_docs(driver: ChromeDriver, documents: List[Dict[str, str]]):
    for document in documents:
        div = driver.find_element(By.CLASS_NAME, document['class'])
        anchor = div.find_element(By.TAG_NAME, 'a')
        anchor.click()
        # this is here to avoid bloating download requests to mintic.
        time.sleep(5)


def main():
    print('00. Setup donwload folder')
    donwload_folder = folder_setup()
    print('01. Init selenium chrome driver')
    driver = init_driver(donwload_folder, headless=True)
    print('02. Browse documents')
    documents = get_docs_info(driver)
    print('03. Download documents')
    download_docs(driver, documents)
    driver.quit()


if __name__ == '__main__':
    main()
