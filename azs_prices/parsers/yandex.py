from __future__ import annotations

import json
import random
from time import sleep
from typing import List

import polars as pl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from ..base import BaseParser


class YandexMapParser(BaseParser):
    """Experimental parser that scrapes Yandex.Maps search results using Selenium.

    NOTE: Requires Google Chrome to be installed in the environment.
    Parsing is intentionally rate-limited to avoid blocking.
    """

    SEARCH_URL_TEMPLATE = "https://yandex.ru/maps/{region_id}/{city}/search/заправки/"

    def __init__(self, city: str = "moscow", region_id: int = 213, limit: int = 20):
        self.city = city
        self.region_id = region_id
        self.limit = limit  # maximum stations to parse in one run

    def _setup_driver(self) -> webdriver.Chrome:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(1920, 1080)
        return driver

    def fetch_data(self) -> pl.DataFrame:  # type: ignore[override]
        driver = self._setup_driver()
        url = self.SEARCH_URL_TEMPLATE.format(region_id=self.region_id, city=self.city)
        driver.get(url)
        sleep(3)

        records: List[dict] = []
        processed: set[str] = set()

        try:
            while len(records) < self.limit:
                # Wait for list container
                org_list = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-list-view__list"))
                )
                items = org_list.find_elements(By.TAG_NAME, "li")
                for item in items:
                    href = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                    if href in processed:
                        continue
                    processed.add(href)
                    driver.execute_script("window.open(arguments[0]);", href)
                    driver.switch_to.window(driver.window_handles[-1])
                    sleep(random.uniform(2, 4))
                    soup = BeautifulSoup(driver.page_source, "lxml")
                    name = soup.find("h1", {"class": "orgpage-header-view__header"})
                    address = soup.find("a", {"class": "business-contacts-view__address-link"})
                    fuel_names = [d.get_text(strip=True) for d in soup.find_all("div", {"class": "search-fuel-info-view__name"})]
                    prices = [d.get_text(strip=True) for d in soup.find_all("div", {"class": "search-fuel-info-view__value"})]
                    records.append(
                        {
                            "url": href,
                            "name": name.get_text(strip=True) if name else None,
                            "address": address.get_text(strip=True) if address else None,
                            "fuel": json.dumps(fuel_names, ensure_ascii=False),
                            "prices": json.dumps(prices, ensure_ascii=False),
                        }
                    )
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    if len(records) >= self.limit:
                        break
                # scroll to load more items
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(2)
        finally:
            driver.quit()

        df = pl.DataFrame(records)
        return df