"""
Парсер для сайта russiabase.ru (Лукойл, Башнефть и другие)
"""
import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any
from loguru import logger

from .base import BaseParser
from config import DEFAULT_HEADERS, TIMEOUT


class RussiaBaseParser(BaseParser):
    """Парсер для сайта russiabase.ru"""
    
    def __init__(self, network_name: str, config: Dict[str, Any]):
        super().__init__(network_name, config)
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        
    def _build_urls(self) -> List[str]:
        """Строит список URL для парсинга всех страниц"""
        base_url = self.config["base_url"]
        max_pages = self.config.get("max_pages", 1)
        
        urls = [base_url]
        for page in range(2, max_pages + 1):
            urls.append(f"{base_url}&page={page}")
        
        return urls
    
    def _fetch_page(self, url: str) -> List[Dict[str, Any]]:
        """Получает данные с одной страницы"""
        logger.debug(f"Fetching page: {url}")
        
        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Поиск JSON-LD данных в script тегах
        json_data = []
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and "@context" in script.string:
                try:
                    data_dict = json.loads(script.string.strip())
                    json_data.append(data_dict)
                except json.JSONDecodeError as e:
                    logger.warning(f"Ошибка декодирования JSON: {e}")
                    continue
        
        return json_data
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Получает данные со всех страниц"""
        urls = self._build_urls()
        all_data = []
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Обработка страницы {i+1}/{len(urls)}: {url}")
                page_data = self.retry_on_failure(self._fetch_page, url)
                all_data.extend(page_data)
                
                if i < len(urls) - 1:  # Добавляем задержку между запросами
                    self.add_delay()
                    
            except Exception as e:
                logger.error(f"Ошибка при загрузке страницы {url}: {e}")
                self.errors.append(f"Page fetch error for {url}: {e}")
                continue
        
        return all_data
    
    def parse_station_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Парсит данные одной станции"""
        try:
            # Извлекаем базовую информацию о станции
            legal_name = raw_data.get('legalName', '')
            address = raw_data.get('address', '')
            description = raw_data.get('description', '')
            
            # Создаем уникальный ID станции на основе названия и адреса
            station_id = f"{legal_name}_{address}"[:100]  # Ограничиваем длину
            
            # Парсим описание для извлечения топлива и цен
            fuel_entries = []
            if description:
                # Разбиваем описание по точке с запятой
                items = [item.strip() for item in description.split(';') if item.strip()]
                
                for item in items:
                    # Разбиваем по тире на топливо и цену
                    parts = item.split(' - ', 1)
                    if len(parts) == 2:
                        fuel_type = parts[0].strip()
                        price_str = parts[1].strip()
                        
                        price = self.clean_price(price_str)
                        
                        fuel_entry = {
                            'station_id': station_id,
                            'station_name': legal_name,
                            'address': self.clean_address(address),
                            'city': self.extract_city_from_address(address),
                            'fuel_type': fuel_type,
                            'price': price,
                            'source': raw_data.get('@context', '')
                        }
                        fuel_entries.append(fuel_entry)
            
            return fuel_entries
            
        except Exception as e:
            logger.error(f"Ошибка парсинга данных станции: {e}, data: {raw_data}")
            return []