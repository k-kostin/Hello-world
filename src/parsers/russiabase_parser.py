"""
Парсер для сайта russiabase.ru - региональные цены на топливо и сети АЗС
"""
import requests
import re
import time
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseParser

@dataclass
class PriceData:
    """Структура данных для цены топлива"""
    region_id: int
    region_name: str
    fuel_prices: Dict[str, float]
    url: str
    timestamp: str
    status: str = "success"


class RussiaBaseParser(BaseParser):
    """
    Парсер для сетей АЗС с сайта russiabase.ru
    
    Парсит цены топлива для конкретных сетей АЗС (Лукойл, Башнефть и т.д.)
    """
    
    def __init__(self, network_name: str, config: Dict[str, Any]):
        super().__init__(network_name, config)
        self.brand_id = config.get('brand_id')
        self.base_url = config.get('base_url')
        self.max_pages = config.get('max_pages', 50)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Получает данные сети АЗС со всех страниц"""
        all_data = []
        
        for page in range(1, self.max_pages + 1):
            try:
                url = f"{self.base_url}&page={page}"
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                stations = self._extract_stations_from_page(soup)
                
                if not stations:
                    logger.info(f"Нет данных на странице {page}, прерываем парсинг")
                    break
                
                all_data.extend(stations)
                logger.info(f"Страница {page}: найдено {len(stations)} станций")
                
                self.add_delay()
                
            except Exception as e:
                logger.error(f"Ошибка при парсинге страницы {page}: {e}")
                break
        
        return all_data
    
    def _extract_stations_from_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлекает данные о станциях с одной страницы"""
        stations = []
        
        # Ищем элементы станций
        station_elements = soup.select('.station-item, .org-item, [data-station]')
        
        for element in station_elements:
            try:
                station_data = self._parse_station_element(element)
                if station_data:
                    stations.append(station_data)
            except Exception as e:
                logger.debug(f"Ошибка парсинга элемента станции: {e}")
                continue
        
        return stations
    
    def _parse_station_element(self, element) -> Optional[Dict[str, Any]]:
        """Парсит данные отдельной станции"""
        try:
            # Извлекаем название станции
            name_elem = element.select_one('.station-name, .org-name, h3, h4')
            station_name = name_elem.get_text().strip() if name_elem else "Неизвестно"
            
            # Извлекаем адрес
            address_elem = element.select_one('.address, .station-address')
            address = address_elem.get_text().strip() if address_elem else ""
            
            # Извлекаем координаты
            lat_elem = element.get('data-lat') or element.select_one('[data-lat]')
            lon_elem = element.get('data-lon') or element.select_one('[data-lon]')
            
            latitude = float(lat_elem) if lat_elem else None
            longitude = float(lon_elem) if lon_elem else None
            
            return {
                'station_name': station_name,
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                'element': element  # Сохраняем элемент для дальнейшего парсинга цен
            }
            
        except Exception as e:
            logger.debug(f"Ошибка извлечения данных станции: {e}")
            return None
    
    def parse_station_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Парсит данные станции и извлекает цены на топливо"""
        results = []
        
        try:
            element = raw_data.get('element')
            if not element:
                return results
            
            # Извлекаем цены на топливо
            fuel_prices = self._extract_fuel_prices(element)
            
            # Извлекаем город из адреса
            address = raw_data.get('address', '')
            city = self.extract_city_from_address(address)
            
            # Создаем записи для каждого типа топлива
            for fuel_type, price in fuel_prices.items():
                station_record = {
                    'station_id': f"{self.network_name}_{hash(raw_data.get('station_name', '') + address)}",
                    'station_name': raw_data.get('station_name', ''),
                    'address': self.clean_address(address),
                    'city': city,
                    'latitude': raw_data.get('latitude'),
                    'longitude': raw_data.get('longitude'),
                    'fuel_type': fuel_type,
                    'price': price,
                    'source': self.base_url
                }
                results.append(station_record)
                
        except Exception as e:
            logger.error(f"Ошибка парсинга данных станции: {e}")
            self.errors.append(f"Station parse error: {e}")
        
        return results
    
    def _extract_fuel_prices(self, element) -> Dict[str, float]:
        """Извлекает цены на топливо из элемента станции"""
        prices = {}
        
        try:
            # Ищем элементы с ценами
            price_elements = element.select('.price, .fuel-price, [data-price]')
            
            for price_elem in price_elements:
                # Пытаемся определить тип топлива
                fuel_text = price_elem.get_text() or price_elem.get('data-fuel', '')
                
                # Ищем тип топлива в тексте или атрибутах
                for fuel_type in ['АИ-92', 'АИ-95', 'АИ-98', 'АИ-100', 'ДТ', 'Пропан']:
                    if fuel_type.lower() in fuel_text.lower():
                        price = self.clean_price(price_elem.get_text())
                        if price:
                            prices[fuel_type] = price
                        break
                        
        except Exception as e:
            logger.debug(f"Ошибка извлечения цен: {e}")
        
        return prices


class RussiaBaseRegionalParser(BaseParser):
    """
    Региональный парсер цен на топливо с сайта russiabase.ru
    
    Извлекает актуальные средние цены на различные виды топлива для регионов России.
    Поддерживает автоматическое получение полной карты регионов из JSON структуры.
    """
    
    BASE_URL = "https://russiabase.ru/prices"
    
    # Маппинг названий топлива на сайте к стандартным названиям
    FUEL_TYPE_MAPPING = {
        'АИ-92': ['ai-92', 'аи-92', 'аи 92', '92', 'ai92', 'АИ-92', 'ай-92', 'ай 92', 'Аи-92+', 'аи92'],
        'АИ-95': ['ai-95', 'аи-95', 'аи 95', '95', 'ai95', 'АИ-95', 'ай-95', 'ай 95', 'Аи-95+', 'аи95'],
        'АИ-98': ['ai-98', 'аи-98', 'аи 98', '98', 'ai98', 'АИ-98', 'ай-98', 'ай 98', 'аи98'],
        'АИ-100': ['ai-100', 'аи-100', 'аи 100', '100', 'ai100', 'АИ-100', 'ай-100', 'ай 100', 'аи100'],
        'ДТ': ['дизель', 'диз', 'dt', 'дт', 'diesel', 'дизельное', 'ДТ', 'солярка', 'дизтопливо'],
        'Пропан': ['газ', 'lpg', 'gas', 'суг', 'пропан', 'Пропан', 'сжиженный газ', 'автогаз']
    }
    
    def __init__(self, network_name: str = "regional_prices", config: Dict[str, Any] = {}):
        """
        Инициализация парсера
        
        Args:
            network_name: Название сети (для совместимости с BaseParser)
            config: Конфигурация (для совместимости с BaseParser)
        """
        if not config:
            config = {
                'type': 'russiabase_regional',
                'base_url': self.BASE_URL,
                'delay': 1.0,
                'max_regions': None
            }
        
        super().__init__(network_name, config)
        self.delay = config.get('delay', 1.0)
        self.max_regions = config.get('max_regions')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self._regions_cache = None  # Кэш для карты регионов

    def fetch_data(self) -> List[Dict[str, Any]]:
        """Получает список всех регионов для дальнейшего парсинга"""
        all_regions = self.get_all_regions()
        
        if not all_regions:
            logger.error("Не удалось получить список регионов")
            return []
        
        logger.info(f"Найдено {len(all_regions)} регионов для парсинга")
        
        # Конвертируем в формат для базового класса
        regions_list = [
            {'id': region_id, 'name': region_name}
            for region_id, region_name in all_regions.items()
        ]
        
        # Ограничиваем количество регионов если задано
        if self.max_regions:
            regions_list = regions_list[:self.max_regions]
            logger.info(f"Ограничиваем парсинг до {self.max_regions} регионов")
        
        return regions_list

    def parse_station_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Парсит данные региона и извлекает средние цены на топливо"""
        results = []
        
        try:
            region_id = raw_data.get('id')
            region_name = raw_data.get('name', f'Регион {region_id}')
            
            if region_id is None:
                logger.warning(f"Пропущен регион без ID: {raw_data}")
                return results
            
            # Получаем цены для региона
            region_prices = self.get_region_prices(region_id, region_name)
            
            if region_prices and region_prices.fuel_prices:
                # Создаем записи для каждого типа топлива
                for fuel_type, price in region_prices.fuel_prices.items():
                    record = {
                        'station_id': f"region_{region_id}",
                        'station_name': f"Средние цены - {region_name}",
                        'address': region_name,
                        'city': region_name,
                        'region': region_name,
                        'region_id': region_id,
                        'latitude': None,  # Для региональных данных нет конкретных координат
                        'longitude': None,
                        'fuel_type': fuel_type,
                        'price': price,
                        'source': region_prices.url
                    }
                    results.append(record)
            
            # Добавляем задержку между запросами
            if self.delay > 0:
                time.sleep(self.delay)
                
        except Exception as e:
            logger.error(f"Ошибка парсинга региона {raw_data}: {e}")
            self.errors.append(f"Region parse error: {e}")
        
        return results

    def extract_regions_from_json(self, region_id: Optional[int] = None) -> Dict[int, str]:
        """
        Извлекает полную карту регионов из JSON структуры в HTML коде страницы
        
        Пример JSON структуры в HTML:
        "regions":[{"id":"18","value":"Алтайский край"},{"id":"72","value":"Амурская область"}...]
        
        Args:
            region_id: ID региона для запроса (по умолчанию 78 - Камчатский край)
            
        Returns:
            Словарь {region_id: region_name} со всеми регионами
        """
        if self._regions_cache:
            return self._regions_cache
            
        if region_id is None:
            region_id = 78  # Камчатский край как дефолтный регион
            
        url = f"{self.BASE_URL}?region={region_id}"
        
        try:
            logger.info("Извлекаю полную карту регионов из JSON структуры...")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Ищем JSON структуру с регионами в HTML коде
            regions_data = self._extract_json_from_html(response.text)
            
            if regions_data:
                self._regions_cache = regions_data
                logger.info(f"Успешно извлечено {len(regions_data)} регионов из JSON структуры")
                return regions_data
            else:
                logger.warning("Не удалось найти JSON структуру с регионами")
                return {}
                
        except Exception as e:
            logger.error(f"Ошибка при извлечении карты регионов: {e}")
            return {}
    
    def _extract_json_from_html(self, html_content: str) -> Dict[int, str]:
        """
        Извлекает JSON данные с регионами из HTML контента
        
        Args:
            html_content: HTML содержимое страницы
            
        Returns:
            Словарь {region_id: region_name}
        """
        regions = {}
        
        try:
            # Паттерны для поиска JSON структуры с регионами
            json_patterns = [
                r'"regions"\s*:\s*(\[.*?\])',
                r'regions\s*:\s*(\[.*?\])',
                r'window\.__NEXT_DATA__\s*=\s*({.*?});',
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
            ]
            
            for pattern in json_patterns:
                matches = re.finditer(pattern, html_content, re.DOTALL)
                
                for match in matches:
                    try:
                        json_str = match.group(1)
                        
                        # Если это полный объект, ищем regions внутри
                        if json_str.startswith('{'):
                            data = json.loads(json_str)
                            regions_list = self._find_regions_in_object(data)
                        else:
                            # Если это массив регионов
                            regions_list = json.loads(json_str)
                        
                        if regions_list and isinstance(regions_list, list):
                            for region in regions_list:
                                if isinstance(region, dict) and 'id' in region:
                                    region_id = int(region['id'])
                                    region_name = region.get('value', region.get('name', f'Регион {region_id}'))
                                    regions[region_id] = region_name
                            
                            if regions:
                                logger.info(f"Найдено {len(regions)} регионов в JSON структуре")
                                return regions
                                
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        logger.debug(f"Ошибка парсинга JSON для паттерна {pattern}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Общая ошибка извлечения JSON: {e}")
        
        return regions
    
    def _find_regions_in_object(self, data: Any) -> Optional[List]:
        """
        Рекурсивно ищет массив регионов в JSON объекте
        
        Args:
            data: JSON объект для поиска
            
        Returns:
            Список регионов или None
        """
        if isinstance(data, dict):
            # Ищем ключ 'regions'
            if 'regions' in data:
                return data['regions']
            
            # Рекурсивно ищем в вложенных объектах
            for key, value in data.items():
                result = self._find_regions_in_object(value)
                if result:
                    return result
                    
        elif isinstance(data, list):
            # Проверяем, не является ли этот список списком регионов
            if data and isinstance(data[0], dict) and 'id' in data[0] and 'value' in data[0]:
                return data
                
            # Рекурсивно ищем в элементах списка
            for item in data:
                result = self._find_regions_in_object(item)
                if result:
                    return result
        
        return None
    
    def get_all_regions(self) -> Dict[int, str]:
        """
        Возвращает полный список всех доступных регионов
        
        Returns:
            Словарь {region_id: region_name}
        """
        return self.extract_regions_from_json()
    
    def parse_all_regions(self, max_regions: Optional[int] = None) -> List[PriceData]:
        """
        Парсит цены для всех доступных регионов
        
        Args:
            max_regions: Максимальное количество регионов для парсинга (None = все)
            
        Returns:
            Список объектов PriceData
        """
        all_regions = self.get_all_regions()
        
        if not all_regions:
            logger.error("Не удалось получить список регионов")
            return []
        
        logger.info(f"Найдено {len(all_regions)} регионов для парсинга")
        
        # Конвертируем в формат для parse_multiple_regions
        regions_list = [
            {'id': region_id, 'name': region_name}
            for region_id, region_name in all_regions.items()
        ]
        
        # Ограничиваем количество регионов если задано
        if max_regions:
            regions_list = regions_list[:max_regions]
            logger.info(f"Ограничиваем парсинг до {max_regions} регионов")
        
        return self.parse_multiple_regions(regions_list)
    
    def get_region_prices(self, region_id: int, region_name: str) -> Optional[PriceData]:
        """
        Получает цены на топливо для конкретного региона
        
        Args:
            region_id: ID региона
            region_name: Название региона
            
        Returns:
            PriceData или None при ошибке
        """
        url = f"{self.BASE_URL}?region={region_id}"
        
        try:
            logger.info(f"Парсинг региона: {region_name} (ID: {region_id})")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Проверяем успешность ответа
            if response.status_code != 200:
                logger.warning(f"Неожиданный статус: {response.status_code} для региона {region_name}")
                return PriceData(
                    region_id=region_id,
                    region_name=region_name,
                    fuel_prices={},
                    url=url,
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    status="error"
                )
            
            # Парсим HTML страницы
            fuel_prices = self._extract_prices_from_html(response.text)
            
            logger.info(f"Найдены цены на топливо: {fuel_prices}")
            
            return PriceData(
                region_id=region_id,
                region_name=region_name,
                fuel_prices=fuel_prices,
                url=url,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса для региона {region_name}: {e}")
            return PriceData(
                region_id=region_id,
                region_name=region_name,
                fuel_prices={},
                url=url,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                status="error"
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка для региона {region_name}: {e}")
            return PriceData(
                region_id=region_id,
                region_name=region_name,
                fuel_prices={},
                url=url,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                status="error"
            )
    
    def _extract_prices_from_html(self, html_content: str) -> Dict[str, float]:
        """
        Извлекает цены на топливо из HTML контента
        
        Args:
            html_content: HTML содержимое страницы
            
        Returns:
            Словарь с ценами на топливо
        """
        fuel_prices = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Стратегия 1: Поиск по JSON данным в скриптах
            json_prices = self._extract_from_script_data(html_content)
            if json_prices:
                fuel_prices.update(json_prices)
            
            # Стратегия 2: Поиск по таблицам и структурированным элементам
            table_prices = self._extract_from_tables(soup)
            if table_prices and not fuel_prices:
                fuel_prices.update(table_prices)
            
            # Стратегия 3: Поиск по регулярным выражениям
            regex_prices = self._extract_with_regex(html_content)
            if regex_prices and not fuel_prices:
                fuel_prices.update(regex_prices)
            
            # Стратегия 4: Поиск по CSS селекторам
            css_prices = self._extract_with_css_selectors(soup)
            if css_prices and not fuel_prices:
                fuel_prices.update(css_prices)
                
        except Exception as e:
            logger.error(f"Ошибка при извлечении цен: {e}")
        
        return fuel_prices
    
    def _extract_from_script_data(self, html_content: str) -> Dict[str, float]:
        """Извлекает цены из JSON данных в script тегах"""
        prices = {}
        
        try:
            # Ищем JSON данные в скриптах
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'window\.__DATA__\s*=\s*({.*?});',
                r'data\s*:\s*({.*?"price".*?})',
                r'"prices"\s*:\s*(\{.*?\})',
                r'"fuel.*?"\s*:\s*(\d+\.?\d*)',
            ]
            
            for pattern in json_patterns:
                matches = re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    try:
                        data_str = match.group(1)
                        # Пытаемся найти цены в тексте
                        price_matches = re.findall(r'"(аи-?\d+|дизель|газ)"?\s*:?\s*"?(\d+\.?\d*)"?', data_str, re.IGNORECASE)
                        for fuel, price in price_matches:
                            normalized_fuel = self._normalize_fuel_name(fuel)
                            if normalized_fuel:
                                prices[normalized_fuel] = float(price)
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Ошибка извлечения из script данных: {e}")
        
        return prices
    
    def _extract_from_tables(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Извлекает цены из таблиц с использованием специфичных селекторов для russiabase.ru"""
        prices = {}
        
        try:
            # Стратегия 1: Специальные селекторы для russiabase.ru
            russiabase_prices = self._extract_from_russiabase_table(soup)
            if russiabase_prices:
                prices.update(russiabase_prices)
                logger.info(f"Извлечены цены через специальные селекторы russiabase.ru: {russiabase_prices}")
            
            # Стратегия 2: Общий поиск по таблицам (если первый способ не сработал)
            if not prices:
                general_prices = self._extract_from_general_tables(soup)
                if general_prices:
                    prices.update(general_prices)
                    logger.info(f"Извлечены цены через общий поиск по таблицам: {general_prices}")
                    
        except Exception as e:
            logger.debug(f"Ошибка извлечения из таблиц: {e}")
        
        return prices

    def _extract_from_russiabase_table(self, soup: BeautifulSoup) -> Dict[str, float]:
        """
        Извлекает цены из специфичной таблицы russiabase.ru
        """
        prices = {}
        
        try:
            # Ищем основную таблицу с ценами по селектору
            main_table = soup.select_one('div#__next main.mainPaddingTop div.OrgListing_listingContainer__TjFmQ div.OrgListing_listing__ieCof section.Table_table__QTCkj div.Table_tableWrapper__oUpPQ table.Table_tableInnerWrapper__AGg3H')
            
            if not main_table:
                # Пробуем более короткие селекторы
                main_table = soup.select_one('section.Table_table__QTCkj table.Table_tableInnerWrapper__AGg3H')
                
            if not main_table:
                # Пробуем найти по классам таблицы
                main_table = soup.select_one('table.Table_tableInnerWrapper__AGg3H')
                
            if not main_table:
                # Пробуем просто найти любую таблицу
                main_table = soup.select_one('table')
                
            if not main_table:
                logger.debug("Не найдена таблица russiabase.ru")
                return prices
                
            logger.debug("Найдена таблица для парсинга")
            
            # Извлекаем заголовки таблицы (названия видов топлива)
            headers = main_table.select('thead tr th')
            fuel_types = []
            
            for i, header in enumerate(headers):
                header_text = header.get_text().strip()
                logger.debug(f"Заголовок {i}: '{header_text}'")
                if header_text:
                    fuel_types.append(header_text)
                    
            logger.debug(f"Найдены заголовки таблицы: {fuel_types}")
            
            # Извлекаем все строки данных
            rows = main_table.select('tbody tr')
            logger.debug(f"Найдено строк в таблице: {len(rows)}")
            
            for row_idx, row in enumerate(rows):
                cells = row.select('td')
                if not cells:
                    continue
                    
                logger.debug(f"Строка {row_idx}: найдено ячеек {len(cells)}")
                
                # Выводим содержимое каждой ячейки для отладки
                cell_texts = []
                for i, cell in enumerate(cells):
                    cell_text = cell.get_text().strip()
                    cell_texts.append(cell_text)
                    logger.debug(f"  Ячейка {i}: '{cell_text}'")
                
                # Анализируем содержимое строки
                # Если первая ячейка содержит "Средняя цена" или похожее, берем эту строку
                first_cell = cell_texts[0].lower() if cell_texts else ""
                
                is_price_row = (
                    'средн' in first_cell or 
                    'average' in first_cell or
                    'цена' in first_cell or
                    any(re.search(r'\d+\.\d+', cell) for cell in cell_texts[1:])  # Есть числа с точкой в других ячейках
                )
                
                if is_price_row:
                    logger.debug(f"Обрабатываем строку {row_idx} как строку с ценами")
                    
                    # Пропускаем первую ячейку (обычно название)
                    for i, cell_text in enumerate(cell_texts[1:], 1):
                        price = self._extract_price_from_text(cell_text)
                        
                        if price and price > 30:  # Реальные цены больше 30 рублей
                            # Определяем тип топлива по позиции или заголовку
                            fuel_type = None
                            
                            # По заголовку
                            if i < len(fuel_types):
                                header_text = fuel_types[i]
                                fuel_type = self._normalize_fuel_name(header_text)
                                logger.debug(f"Заголовок '{header_text}' -> топливо: {fuel_type}")
                            
                            # По позиции если заголовок не распознался
                            if not fuel_type:
                                position_mapping = {
                                    1: 'АИ-92',
                                    2: 'АИ-95', 
                                    3: 'АИ-98',
                                    4: 'АИ-100',
                                    5: 'ДТ',
                                    6: 'Пропан'
                                }
                                fuel_type = position_mapping.get(i)
                                logger.debug(f"По позиции {i} -> топливо: {fuel_type}")
                            
                            if fuel_type:
                                prices[fuel_type] = price
                                logger.debug(f"✅ Найдена реальная цена: {fuel_type} = {price}")
                    
                    # Если нашли хотя бы одну цену в этой строке, прекращаем поиск
                    if prices:
                        break
            
            # Если не нашли цены в таблице, пробуем альтернативный подход
            if not prices:
                logger.debug("Не найдены цены в основной таблице, пробуем альтернативный поиск")
                
                # Ищем любые ячейки с классами, указывающими на цены
                price_cells = main_table.select('td[class*="price"], td[class*="cost"], td[class*="value"]')
                for cell in price_cells:
                    cell_text = cell.get_text().strip()
                    price = self._extract_price_from_text(cell_text)
                    if price and price > 30:
                        logger.debug(f"Найдена цена в специальной ячейке: {price}")
                        
                        # Пытаемся определить тип топлива из соседних ячеек
                        parent_row = cell.find_parent('tr')
                        if parent_row:
                            row_cells = parent_row.select('td')
                            for row_cell in row_cells:
                                fuel_type = self._normalize_fuel_name(row_cell.get_text().strip())
                                if fuel_type:
                                    prices[fuel_type] = price
                                    logger.debug(f"✅ Определен тип: {fuel_type} = {price}")
                                    break
                                    
        except Exception as e:
            logger.error(f"Ошибка извлечения из таблицы russiabase.ru: {e}")
        
        # Дополнительная проверка - если цены слишком подозрительные (92, 95, 98, 100), очищаем
        suspicious_prices = [92.0, 95.0, 98.0, 100.0]
        if all(price in suspicious_prices for price in prices.values()):
            logger.warning("⚠️ Обнаружены подозрительные цены (92, 95, 98, 100) - возможно, это номера топлива, а не цены")
            prices.clear()
        
        return prices

    def _extract_from_general_tables(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Общий метод извлечения цен из таблиц"""
        prices = {}
        
        try:
            logger.debug("Запуск общего поиска по таблицам")
            
            # Ищем все таблицы на странице
            tables = soup.find_all('table')
            logger.debug(f"Найдено таблиц: {len(tables)}")
            
            for table_idx, table in enumerate(tables):
                logger.debug(f"Анализируем таблицу {table_idx}")
                rows = table.find_all('tr')
                
                for row_idx, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    logger.debug(f"  Строка {row_idx}: {len(cells)} ячеек")
                    
                    # Стратегия 1: Ищем пары ячеек "тип топлива - цена"
                    for i, cell in enumerate(cells[:-1]):
                        fuel_text = cell.get_text().strip()
                        price_text = cells[i + 1].get_text().strip()
                        
                        logger.debug(f"    Проверяем пару: '{fuel_text}' -> '{price_text}'")
                        
                        # Проверяем, содержит ли текст название топлива
                        normalized_fuel = self._normalize_fuel_name(fuel_text)
                        if normalized_fuel:
                            price = self._extract_price_from_text(price_text)
                            if price and price > 30:  # Реальные цены больше 30 рублей
                                prices[normalized_fuel] = price
                                logger.debug(f"    ✅ Найдена пара: {normalized_fuel} = {price}")
                    
                    # Стратегия 2: Ищем цены в одной строке (разные колонки для разных видов топлива)
                    if len(cells) >= 4:  # Достаточно ячеек для нескольких видов топлива
                        potential_prices = []
                        for cell in cells[1:]:  # Пропускаем первую ячейку (обычно название)
                            price = self._extract_price_from_text(cell.get_text().strip())
                            if price and price > 30:
                                potential_prices.append(price)
                        
                        # Если нашли несколько цен в одной строке, присваиваем по порядку
                        if len(potential_prices) >= 2:
                            fuel_mapping = ['АИ-92', 'АИ-95', 'АИ-98', 'АИ-100', 'ДТ', 'Пропан']
                            for i, price in enumerate(potential_prices[:6]):
                                if i < len(fuel_mapping):
                                    prices[fuel_mapping[i]] = price
                                    logger.debug(f"    ✅ По позиции: {fuel_mapping[i]} = {price}")
                    
                    # Если нашли что-то, не ищем в других таблицах
                    if prices:
                        break
                        
                if prices:
                    break
                    
        except Exception as e:
            logger.debug(f"Ошибка общего извлечения из таблиц: {e}")
        
        return prices
    
    def _extract_with_regex(self, html_content: str) -> Dict[str, float]:
        """Извлекает цены с помощью регулярных выражений"""
        prices = {}
        
        try:
            logger.debug("Запуск поиска через регулярные выражения")
            
            # Более мощные паттерны для поиска цен
            patterns = [
                # Прямые паттерны с ценами
                r'АИ-?92[^\d]*?(\d{2}\.\d{1,2})',
                r'АИ-?95[^\d]*?(\d{2}\.\d{1,2})',
                r'АИ-?98[^\d]*?(\d{2}\.\d{1,2})',
                r'АИ-?100[^\d]*?(\d{2}\.\d{1,2})',
                r'(?:дизель|ДТ)[^\d]*?(\d{2}\.\d{1,2})',
                r'(?:газ|пропан)[^\d]*?(\d{2}\.\d{1,2})',
                
                # Обратные паттерны (цена перед топливом)
                r'(\d{2}\.\d{1,2})[^\d]*?АИ-?92',
                r'(\d{2}\.\d{1,2})[^\d]*?АИ-?95',
                r'(\d{2}\.\d{1,2})[^\d]*?АИ-?98',
                r'(\d{2}\.\d{1,2})[^\d]*?АИ-?100',
                r'(\d{2}\.\d{1,2})[^\d]*?(?:дизель|ДТ)',
                r'(\d{2}\.\d{1,2})[^\d]*?(?:газ|пропан)',
                
                # Паттерны с рублями
                r'АИ-?92[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)',
                r'АИ-?95[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)',
                r'АИ-?98[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)',
                r'АИ-?100[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)',
                r'(?:дизель|ДТ)[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)',
                r'(?:газ|пропан)[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)',
                
                # Средние цены
                r'средн[^\d]*?АИ-?92[^\d]*?(\d{2}\.\d{1,2})',
                r'средн[^\d]*?АИ-?95[^\d]*?(\d{2}\.\d{1,2})',
                r'средн[^\d]*?АИ-?98[^\d]*?(\d{2}\.\d{1,2})',
                r'средн[^\d]*?АИ-?100[^\d]*?(\d{2}\.\d{1,2})',
                r'средн[^\d]*?(?:дизель|ДТ)[^\d]*?(\d{2}\.\d{1,2})',
                r'средн[^\d]*?(?:газ|пропан)[^\d]*?(\d{2}\.\d{1,2})',
            ]
            
            fuel_type_patterns = {
                'АИ-92': [r'АИ-?92[^\d]*?(\d{2}\.\d{1,2})', r'(\d{2}\.\d{1,2})[^\d]*?АИ-?92', r'АИ-?92[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)', r'средн[^\d]*?АИ-?92[^\d]*?(\d{2}\.\d{1,2})'],
                'АИ-95': [r'АИ-?95[^\d]*?(\d{2}\.\d{1,2})', r'(\d{2}\.\d{1,2})[^\d]*?АИ-?95', r'АИ-?95[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)', r'средн[^\d]*?АИ-?95[^\d]*?(\d{2}\.\d{1,2})'],
                'АИ-98': [r'АИ-?98[^\d]*?(\d{2}\.\d{1,2})', r'(\d{2}\.\d{1,2})[^\d]*?АИ-?98', r'АИ-?98[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)', r'средн[^\d]*?АИ-?98[^\d]*?(\d{2}\.\d{1,2})'],
                'АИ-100': [r'АИ-?100[^\d]*?(\d{2}\.\d{1,2})', r'(\d{2}\.\d{1,2})[^\d]*?АИ-?100', r'АИ-?100[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)', r'средн[^\d]*?АИ-?100[^\d]*?(\d{2}\.\d{1,2})'],
                'ДТ': [r'(?:дизель|ДТ)[^\d]*?(\d{2}\.\d{1,2})', r'(\d{2}\.\d{1,2})[^\d]*?(?:дизель|ДТ)', r'(?:дизель|ДТ)[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)', r'средн[^\d]*?(?:дизель|ДТ)[^\d]*?(\d{2}\.\d{1,2})'],
                'Пропан': [r'(?:газ|пропан)[^\d]*?(\d{2}\.\d{1,2})', r'(\d{2}\.\d{1,2})[^\d]*?(?:газ|пропан)', r'(?:газ|пропан)[^0-9]*?(\d{2}[.,]\d{1,2})\s*(?:руб|₽)', r'средн[^\d]*?(?:газ|пропан)[^\d]*?(\d{2}\.\d{1,2})']
            }
            
            for fuel_type, patterns_list in fuel_type_patterns.items():
                for pattern in patterns_list:
                    matches = re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        try:
                            price_str = match.group(1).replace(',', '.')
                            price = float(price_str)
                            
                            if 30 <= price <= 200:  # Разумные границы цен
                                if fuel_type not in prices:  # Берем первое найденное значение
                                    prices[fuel_type] = price
                                    logger.debug(f"✅ Regex: {fuel_type} = {price}")
                                    
                        except (ValueError, AttributeError):
                            continue
            
            # Дополнительный поиск в JSON данных
            json_pattern = r'"price":\s*(\d{2}\.\d{1,2})'
            json_matches = re.finditer(json_pattern, html_content)
            found_json_prices = []
            
            for match in json_matches:
                try:
                    price = float(match.group(1))
                    if 30 <= price <= 200:
                        found_json_prices.append(price)
                except:
                    continue
            
            # Если нашли цены в JSON, присваиваем их по порядку
            if found_json_prices and not prices:
                fuel_mapping = ['АИ-92', 'АИ-95', 'АИ-98', 'АИ-100', 'ДТ', 'Пропан']
                for i, price in enumerate(found_json_prices[:6]):
                    if i < len(fuel_mapping):
                        prices[fuel_mapping[i]] = price
                        logger.debug(f"✅ JSON: {fuel_mapping[i]} = {price}")
                        
        except Exception as e:
            logger.debug(f"Ошибка regex извлечения: {e}")
        
        return prices
    
    def _extract_with_css_selectors(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Извлекает цены с помощью CSS селекторов"""
        prices = {}
        
        try:
            # Различные селекторы для поиска цен
            selectors = [
                '.price-item',
                '.fuel-price',
                '[data-fuel]',
                '.price-value',
                '.gas-price',
                'span[class*="price"]',
                'div[class*="fuel"]',
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    
                    # Ищем топливо и цену в тексте элемента
                    fuel_match = re.search(r'(АИ-?\d+|дизель|газ)', text, re.IGNORECASE)
                    price_match = re.search(r'(\d+\.?\d*)', text)
                    
                    if fuel_match and price_match:
                        normalized_fuel = self._normalize_fuel_name(fuel_match.group(1))
                        if normalized_fuel:
                            price = float(price_match.group(1))
                            if price > 10 and price < 200:  # Разумные границы цен
                                prices[normalized_fuel] = price
                                
        except Exception as e:
            logger.debug(f"Ошибка CSS селекторов: {e}")
        
        return prices
    
    def _normalize_fuel_name(self, fuel_text: str) -> Optional[str]:
        """
        Нормализует название топлива к стандартному виду
        
        Args:
            fuel_text: Исходное название топлива
            
        Returns:
            Стандартное название или None
        """
        if not fuel_text:
            return None
            
        # Очищаем текст от лишних символов
        fuel_text = re.sub(r'[^\w\-\+]', '', fuel_text.lower().strip())
        
        # Проверяем точные совпадения
        for standard_name, variants in self.FUEL_TYPE_MAPPING.items():
            for variant in variants:
                variant_clean = re.sub(r'[^\w\-\+]', '', variant.lower())
                if variant_clean == fuel_text:
                    return standard_name
        
        # Проверяем частичные совпадения
        for standard_name, variants in self.FUEL_TYPE_MAPPING.items():
            for variant in variants:
                variant_clean = re.sub(r'[^\w\-\+]', '', variant.lower())
                if variant_clean in fuel_text or fuel_text in variant_clean:
                    return standard_name
        
        # Дополнительные проверки для конкретных паттернов
        if re.search(r'92', fuel_text):
            return 'АИ-92'
        elif re.search(r'95', fuel_text):
            return 'АИ-95'
        elif re.search(r'98', fuel_text):
            return 'АИ-98'
        elif re.search(r'100', fuel_text):
            return 'АИ-100'
        elif re.search(r'(дт|диз|diesel)', fuel_text):
            return 'ДТ'
        elif re.search(r'(газ|lpg|пропан)', fuel_text):
            return 'Пропан'
        
        return None
    
    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """
        Извлекает числовую цену из текста
        
        Args:
            text: Текст, содержащий цену
            
        Returns:
            Цена как float или None
        """
        if not text:
            return None
            
        try:
            # Удаляем все кроме цифр, точек и запятых
            clean_text = re.sub(r'[^\d.,]', '', text.strip())
            
            if not clean_text:
                return None
            
            # Заменяем запятые на точки
            clean_text = clean_text.replace(',', '.')
            
            # Если несколько точек, берем только первую
            if clean_text.count('.') > 1:
                parts = clean_text.split('.')
                clean_text = parts[0] + '.' + ''.join(parts[1:])
            
            price = float(clean_text)
            
            # Проверяем разумность цены
            if 10 <= price <= 200:
                return price
                
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def parse_multiple_regions(self, regions: List[Dict[str, Any]]) -> List[PriceData]:
        """
        Парсит цены для нескольких регионов
        
        Args:
            regions: Список регионов с ключами 'id' и 'name'
            
        Returns:
            Список объектов PriceData
        """
        results = []
        
        for region in regions:
            region_id = region.get('id')
            region_name = region.get('name', f'Регион {region_id}')
            
            if region_id is None:
                logger.warning(f"Пропущен регион без ID: {region}")
                continue
            
            result = self.get_region_prices(region_id, region_name)
            if result:
                results.append(result)
            
            # Задержка между запросами
            if self.delay > 0:
                time.sleep(self.delay)
        
        return results

    def get_available_fuel_types(self) -> List[str]:
        """Возвращает список доступных типов топлива"""
        return list(self.FUEL_TYPE_MAPPING.keys())