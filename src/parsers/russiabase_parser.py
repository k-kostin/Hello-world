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
        """Получает данные со всех страниц с динамическим определением количества страниц"""
        base_url = self.config["base_url"]
        all_data = []
        consecutive_errors = 0
        max_consecutive_errors = 3
        page = 1
        
        while True:
            # Строим URL для текущей страницы
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}&page={page}"
            
            try:
                logger.info(f"Обработка страницы {page}: {url}")
                page_data = self.retry_on_failure(self._fetch_page, url)
                
                # Если данные получены успешно
                if page_data:
                    all_data.extend(page_data)
                    consecutive_errors = 0  # Сбрасываем счетчик ошибок
                    logger.debug(f"Страница {page} обработана успешно, получено {len(page_data)} записей")
                else:
                    # Страница пустая - считаем это ошибкой
                    consecutive_errors += 1
                    logger.warning(f"Страница {page} пустая, consecutive_errors: {consecutive_errors}")
                
                # Добавляем задержку между запросами
                self.add_delay()
                
            except requests.exceptions.HTTPError as e:
                if "404" in str(e):
                    consecutive_errors += 1
                    logger.warning(f"Страница {page} не найдена (404), consecutive_errors: {consecutive_errors}")
                else:
                    logger.error(f"HTTP ошибка при загрузке страницы {url}: {e}")
                    self.errors.append(f"HTTP error for {url}: {e}")
                    consecutive_errors += 1
                    
            except Exception as e:
                logger.error(f"Ошибка при загрузке страницы {url}: {e}")
                self.errors.append(f"Page fetch error for {url}: {e}")
                consecutive_errors += 1
            
            # Проверяем, нужно ли остановить парсинг
            if consecutive_errors >= max_consecutive_errors:
                logger.info(f"Остановка парсинга: {consecutive_errors} consecutive ошибок подряд. "
                           f"Всего обработано страниц: {page}")
                break
            
            page += 1
            
            # Защита от бесконечного цикла - максимум 1000 страниц
            if page > 1000:
                logger.warning("Достигнут лимит в 1000 страниц, остановка парсинга")
                break
        
        logger.info(f"Парсинг завершен. Обработано страниц: {page-1}, получено записей: {len(all_data)}")
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