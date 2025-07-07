"""
Парсер для сайта russiabase.ru - региональные цены на топливо
"""
import requests
import re
import time
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup

@dataclass
class PriceData:
    """Структура данных для цены топлива"""
    region_id: int
    region_name: str
    fuel_prices: Dict[str, float]
    url: str
    timestamp: str
    status: str = "success"

class RussiaBaseRegionalParser:
    """
    Улучшенный парсер региональных цен на топливо с сайта russiabase.ru
    
    Извлекает актуальные цены на различные виды топлива для регионов России.
    Поддерживает автоматическое получение полной карты регионов из JSON структуры.
    """
    
    BASE_URL = "https://russiabase.ru/prices"
    
    # Маппинг названий топлива на сайте к стандартным названиям
    FUEL_TYPE_MAPPING = {
        'АИ-92': ['ai-92', 'аи-92', 'аи 92', '92', 'ai92', 'АИ-92'],
        'АИ-95': ['ai-95', 'аи-95', 'аи 95', '95', 'ai95', 'АИ-95'],
        'АИ-98': ['ai-98', 'аи-98', 'аи 98', '98', 'ai98', 'АИ-98'],
        'АИ-100': ['ai-100', 'аи-100', 'аи 100', '100', 'ai100', 'АИ-100'],
        'Дизель': ['дизель', 'диз', 'dt', 'дт', 'diesel', 'дизельное'],
        'Газ': ['газ', 'lpg', 'gas', 'суг', 'пропан']
    }
    
    def __init__(self, delay: float = 1.0):
        """
        Инициализация парсера
        
        Args:
            delay: Задержка между запросами в секундах
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = logging.getLogger(__name__)
        self._regions_cache = None  # Кэш для карты регионов
        
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
            self.logger.info("Извлекаю полную карту регионов из JSON структуры...")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Ищем JSON структуру с регионами в HTML коде
            regions_data = self._extract_json_from_html(response.text)
            
            if regions_data:
                self._regions_cache = regions_data
                self.logger.info(f"Успешно извлечено {len(regions_data)} регионов из JSON структуры")
                return regions_data
            else:
                self.logger.warning("Не удалось найти JSON структуру с регионами")
                return {}
                
        except Exception as e:
            self.logger.error(f"Ошибка при извлечении карты регионов: {e}")
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
                                self.logger.info(f"Найдено {len(regions)} регионов в JSON структуре")
                                return regions
                                
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        self.logger.debug(f"Ошибка парсинга JSON для паттерна {pattern}: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Общая ошибка извлечения JSON: {e}")
        
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
            self.logger.error("Не удалось получить список регионов")
            return []
        
        self.logger.info(f"Найдено {len(all_regions)} регионов для парсинга")
        
        # Конвертируем в формат для parse_multiple_regions
        regions_list = [
            {'id': region_id, 'name': region_name}
            for region_id, region_name in all_regions.items()
        ]
        
        # Ограничиваем количество регионов если задано
        if max_regions:
            regions_list = regions_list[:max_regions]
            self.logger.info(f"Ограничиваем парсинг до {max_regions} регионов")
        
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
            self.logger.info(f"Парсинг региона: {region_name} (ID: {region_id})")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Проверяем успешность ответа
            if response.status_code != 200:
                self.logger.warning(f"Неожиданный статус: {response.status_code} для региона {region_name}")
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
            
            self.logger.info(f"Найдены цены на топливо: {fuel_prices}")
            
            return PriceData(
                region_id=region_id,
                region_name=region_name,
                fuel_prices=fuel_prices,
                url=url,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка запроса для региона {region_name}: {e}")
            return PriceData(
                region_id=region_id,
                region_name=region_name,
                fuel_prices={},
                url=url,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                status="error"
            )
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка для региона {region_name}: {e}")
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
            self.logger.error(f"Ошибка при извлечении цен: {e}")
        
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
            self.logger.debug(f"Ошибка извлечения из script данных: {e}")
        
        return prices
    
    def _extract_from_tables(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Извлекает цены из таблиц"""
        prices = {}
        
        try:
            # Ищем таблицы с ценами
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        for i, cell in enumerate(cells[:-1]):
                            fuel_text = cell.get_text().strip()
                            price_text = cells[i + 1].get_text().strip()
                            
                            # Проверяем, содержит ли текст название топлива
                            normalized_fuel = self._normalize_fuel_name(fuel_text)
                            if normalized_fuel:
                                price = self._extract_price_from_text(price_text)
                                if price:
                                    prices[normalized_fuel] = price
                                    
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения из таблиц: {e}")
        
        return prices
    
    def _extract_with_regex(self, html_content: str) -> Dict[str, float]:
        """Извлекает цены с помощью регулярных выражений"""
        prices = {}
        
        try:
            # Различные паттерны для поиска цен
            patterns = [
                # АИ-92: 55.5 или АИ-92</td><td>55.5
                r'(АИ-?\d+|дизель|газ)[^\d]*?(\d+\.?\d*)\s*руб',
                r'(АИ-?\d+|дизель|газ)[^>]*?[>:][\s]*(\d+\.?\d*)',
                r'"(ai-?\d+|diesel|gas)"[^:]*?[:\s]*(\d+\.?\d*)',
                # Для средних цен
                r'средняя\s+цена[^:]*?(АИ-?\d+|дизель|газ)[^:]*?(\d+\.?\d*)',
                # Цены в рублях
                r'(\d+\.?\d*)\s*₽[^a-zA-Zа-яА-Я]*?(АИ-?\d+|дизель|газ)',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    try:
                        if len(match.groups()) >= 2:
                            fuel_raw = match.group(1)
                            price_raw = match.group(2)
                            
                            # Иногда порядок может быть обратным
                            if not re.match(r'\d+\.?\d*', price_raw):
                                fuel_raw, price_raw = price_raw, fuel_raw
                            
                            normalized_fuel = self._normalize_fuel_name(fuel_raw)
                            if normalized_fuel:
                                price = self._extract_price_from_text(price_raw)
                                if price and price > 10 and price < 200:  # Разумные границы цен
                                    prices[normalized_fuel] = price
                    except:
                        continue
                        
        except Exception as e:
            self.logger.debug(f"Ошибка regex извлечения: {e}")
        
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
            self.logger.debug(f"Ошибка CSS селекторов: {e}")
        
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
            
        fuel_text = fuel_text.lower().strip()
        
        for standard_name, variants in self.FUEL_TYPE_MAPPING.items():
            for variant in variants:
                if variant.lower() in fuel_text:
                    return standard_name
        
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
                self.logger.warning(f"Пропущен регион без ID: {region}")
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