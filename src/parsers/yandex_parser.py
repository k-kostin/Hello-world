"""
Парсер для Яндекс Карт с использованием Selenium
"""
import random
from time import sleep
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseParser
from config import SELENIUM_CONFIG


class YandexMapsParser(BaseParser):
    """Парсер для Яндекс Карт"""
    
    def __init__(self, network_name: str, config: Dict[str, Any]):
        super().__init__(network_name, config)
        self.driver = None
        self.processed_urls = set()
        
    def _setup_driver(self):
        """Настройка Selenium WebDriver"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument(f"--user-agent={SELENIUM_CONFIG['user_agent']}")
        chrome_options.add_argument(f"--window-size={SELENIUM_CONFIG['window_size'][0]},{SELENIUM_CONFIG['window_size'][1]}")
        
        if SELENIUM_CONFIG.get('headless', True):
            chrome_options.add_argument("--headless")
        
        # Дополнительные опции для стабильности
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def _scroll_to_load_results(self):
        """Прокручивает страницу для загрузки всех результатов"""
        scroll_count = self.config.get('scroll_count', 3)
        
        for i in range(scroll_count):
            logger.debug(f"Прокрутка {i+1}/{scroll_count}")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)
    
    def _extract_organization_urls(self) -> List[str]:
        """Извлекает URL организаций из списка результатов"""
        try:
            # Ожидаем загрузки списка
            organizations_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'search-list-view__list'))
            )
            
            # Получаем все элементы списка
            org_elements = organizations_list.find_elements(By.TAG_NAME, 'li')
            logger.info(f"Найдено {len(org_elements)} элементов организаций")
            
            urls = []
            for org_element in org_elements:
                try:
                    link = org_element.find_element(By.TAG_NAME, 'a')
                    url = link.get_attribute("href")
                    if url and url not in self.processed_urls:
                        urls.append(url)
                        self.processed_urls.add(url)
                except (StaleElementReferenceException, NoSuchElementException):
                    continue
            
            logger.info(f"Извлечено {len(urls)} уникальных URL")
            return urls
            
        except TimeoutException:
            logger.error("Не удалось найти список организаций на странице")
            return []
    
    def _parse_organization_page(self, url: str) -> Dict[str, Any]:
        """Парсит страницу отдельной организации"""
        logger.debug(f"Парсинг организации: {url}")
        
        self.driver.get(url)
        sleep(random.uniform(2, 5))
        
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        
        # Извлекаем данные
        name = self._extract_name(soup)
        address = self._extract_address(soup)
        fuel_types, prices = self._extract_fuel_data(soup)
        
        return {
            'url': url,
            'name': name,
            'address': address,
            'fuel_types': fuel_types,
            'prices': prices
        }
    
    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Извлекает название организации"""
        try:
            name_element = soup.find("h1", {"class": "orgpage-header-view__header"})
            if name_element:
                return name_element.get_text().strip()
        except Exception as e:
            logger.warning(f"Ошибка извлечения названия: {e}")
        return ""
    
    def _extract_address(self, soup: BeautifulSoup) -> str:
        """Извлекает адрес организации"""
        try:
            address_element = soup.find("a", {"class": "business-contacts-view__address-link"})
            if address_element:
                return address_element.get_text().strip()
        except Exception as e:
            logger.warning(f"Ошибка извлечения адреса: {e}")
        return ""
    
    def _extract_fuel_data(self, soup: BeautifulSoup) -> tuple:
        """Извлекает данные о топливе и ценах"""
        fuel_types = []
        prices = []
        
        try:
            # Получаем список топлива
            fuel_elements = soup.find_all("div", {"class": "search-fuel-info-view__name"})
            for fuel_element in fuel_elements:
                fuel_types.append(fuel_element.get_text().strip())
            
            # Получаем список цен
            price_elements = soup.find_all("div", {"class": "search-fuel-info-view__value"})
            for price_element in price_elements:
                prices.append(price_element.get_text().strip())
                
        except Exception as e:
            logger.warning(f"Ошибка извлечения данных о топливе: {e}")
        
        return fuel_types, prices
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Основной метод получения данных"""
        logger.info("Запуск парсинга Яндекс Карт")
        
        try:
            self._setup_driver()
            self.driver.get(self.config['search_url'])
            
            # Прокручиваем для загрузки результатов
            self._scroll_to_load_results()
            
            # Извлекаем URL организаций
            organization_urls = self._extract_organization_urls()
            
            # Парсим каждую организацию
            all_data = []
            for i, url in enumerate(organization_urls):
                try:
                    logger.info(f"Обработка организации {i+1}/{len(organization_urls)}")
                    org_data = self._parse_organization_page(url)
                    all_data.append(org_data)
                    
                    # Возвращаемся к списку
                    self.driver.back()
                    sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Ошибка парсинга организации {url}: {e}")
                    self.errors.append(f"Organization parse error for {url}: {e}")
                    continue
            
            return all_data
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def parse_station_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Парсит данные одной станции"""
        try:
            url = raw_data.get('url', '')
            name = raw_data.get('name', '')
            address = raw_data.get('address', '')
            fuel_types = raw_data.get('fuel_types', [])
            prices = raw_data.get('prices', [])
            
            # Создаем ID станции
            station_id = f"yandex_{hash(url)}_{hash(name)}"
            
            fuel_entries = []
            
            # Объединяем топливо и цены
            for fuel_type, price_str in zip(fuel_types, prices):
                price = self.clean_price(price_str)
                
                fuel_entry = {
                    'station_id': station_id,
                    'station_name': name,
                    'address': self.clean_address(address),
                    'city': self.extract_city_from_address(address),
                    'fuel_type': fuel_type,
                    'price': price,
                    'source': url
                }
                fuel_entries.append(fuel_entry)
            
            return fuel_entries
            
        except Exception as e:
            logger.error(f"Ошибка парсинга данных станции: {e}, data: {raw_data}")
            return []