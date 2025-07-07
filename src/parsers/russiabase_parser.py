"""
Парсер для сайта russiabase.ru - региональные цены на топливо
"""
import requests
import re
import time
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

    def _extract_region_name(self, html_content: str, region_id: int) -> str:
        """
        Извлекает правильное название региона со страницы russiabase.ru
        
        Args:
            html_content: HTML содержимое страницы
            region_id: ID региона
            
        Returns:
            str: Корректное название региона
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Стратегия 1: Извлечение из title
            title = soup.find('title')
            if title:
                title_text = title.get_text().strip()
                if ' в ' in title_text:
                    region_name = title_text.split(' в ')[-1].strip()
                    # Убираем падежные окончания
                    region_name = self._normalize_region_name(region_name)
                    if region_name:
                        return region_name
            
            # Стратегия 2: Извлечение из H1
            h1 = soup.find('h1')
            if h1:
                h1_text = h1.get_text().strip()
                if ' в ' in h1_text:
                    region_name = h1_text.split(' в ')[-1].strip()
                    region_name = self._normalize_region_name(region_name)
                    if region_name:
                        return region_name
            
            # Стратегия 3: Поиск в мета-описании
            try:
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    content = meta_desc.get('content', '')
                    if content and ' в ' in content:
                        region_name = content.split(' в ')[-1].split('.')[0].strip()
                        region_name = self._normalize_region_name(region_name)
                        if region_name:
                            return region_name
            except (AttributeError, TypeError):
                pass
            
            # Если не удалось извлечь, возвращаем базовое название
            return f"Регион {region_id}"
            
        except Exception as e:
            self.logger.warning(f"Ошибка извлечения названия региона {region_id}: {e}")
            return f"Регион {region_id}"
    
    def _normalize_region_name(self, region_name: str) -> str:
        """
        Нормализует название региона (убирает падежные окончания)
        
        Args:
            region_name: Исходное название региона
            
        Returns:
            str: Нормализованное название
        """
        if not region_name:
            return ""
        
        # Убираем лишние пробелы
        region_name = region_name.strip()
        
        # Словарь для замены падежных форм на именительный падеж
        replacements = {
            # Области в родительном падеже -> именительный падеж
            'Тверской области': 'Тверская область',
            'Калининградской области': 'Калининградская область',
            'Псковской области': 'Псковская область',
            'Ленинградской области': 'Ленинградская область',
            'Курской области': 'Курская область',
            'Тюменской области': 'Тюменская область',
            'Оренбургской области': 'Оренбургская область',
            'Тульской области': 'Тульская область',
            'Тамбовской области': 'Тамбовская область',
            'Московской области': 'Московская область',
            'Нижегородской области': 'Нижегородская область',
            'Саратовской области': 'Саратовская область',
            'Самарской области': 'Самарская область',
            'Волгоградской области': 'Волгоградская область',
            'Ростовской области': 'Ростовская область',
            'Свердловской области': 'Свердловская область',
            'Челябинской области': 'Челябинская область',
            'Новосибирской области': 'Новосибирская область',
            'Кемеровской области': 'Кемеровская область',
            'Иркутской области': 'Иркутская область',
            'Амурской области': 'Амурская область',
            'Магаданской области': 'Магаданская область',
            'Сахалинской области': 'Сахалинская область',
            
            # Республики
            'Карелии': 'Республика Карелия',
            'Удмуртии': 'Удмуртская Республика',
            'Мордовии': 'Республика Мордовия',
            'Башкортостане': 'Республика Башкортостан',
            'Татарстане': 'Республика Татарстан',
            'Чувашии': 'Чувашская Республика',
            'Марий Эл': 'Республика Марий Эл',
            'Коми': 'Республика Коми',
            'Дагестане': 'Республика Дагестан',
            'Ингушетии': 'Республика Ингушетия',
            'Северной Осетии': 'Республика Северная Осетия',
            'Кабардино-Балкарии': 'Кабардино-Балкарская Республика',
            'Карачаево-Черкесии': 'Карачаево-Черкесская Республика',
            'Адыгее': 'Республика Адыгея',
            'Калмыкии': 'Республика Калмыкия',
            'Крыму': 'Республика Крым',
            'Алтае': 'Республика Алтай',
            'Тыве': 'Республика Тыва',
            'Хакасии': 'Республика Хакасия',
            'Бурятии': 'Республика Бурятия',
            'Саха (Якутии)': 'Республика Саха (Якутия)',
            'Якутии': 'Республика Саха (Якутия)',
            
            # Края
            'Краснодарском крае': 'Краснодарский край',
            'Ставропольском крае': 'Ставропольский край',
            'Алтайском крае': 'Алтайский край',
            'Красноярском крае': 'Красноярский край',
            'Приморском крае': 'Приморский край',
            'Хабаровском крае': 'Хабаровский край',
            'Камчатском крае': 'Камчатский край',
            'Пермском крае': 'Пермский край',
            'Забайкальском крае': 'Забайкальский край',
            
            # Автономные округа
            'Ямало-Ненецком округе': 'Ямало-Ненецкий автономный округ',
            'Ханты-Мансийском округе': 'Ханты-Мансийский автономный округ',
            'Чукотском округе': 'Чукотский автономный округ',
            'Ненецком округе': 'Ненецкий автономный округ',
            'Чукотке': 'Чукотский автономный округ',
            'ХМАО': 'Ханты-Мансийский автономный округ',
            'ЯНАО': 'Ямало-Ненецкий автономный округ',
            
            # Города федерального значения
            'Москве': 'Москва',
            'Санкт-Петербурге': 'Санкт-Петербург',
            'Севастополе': 'Севастополь'
        }
        
        # Применяем замены
        for old_form, new_form in replacements.items():
            if region_name == old_form:
                return new_form
        
        # Если точного соответствия нет, пробуем паттерны
        import re
        
        # Паттерн для областей: "Название + области" -> "Название + область"
        oblast_pattern = r'^(.+?)ой области$'
        match = re.match(oblast_pattern, region_name)
        if match:
            return f"{match.group(1)}ая область"
        
        # Паттерн для краев: "Название + крае" -> "Название + край"
        krai_pattern = r'^(.+?)ском крае$'
        match = re.match(krai_pattern, region_name)
        if match:
            return f"{match.group(1)}ский край"
        
        # Возвращаем как есть, если не удалось нормализовать
        return region_name

    def get_region_data(self, region_id: int) -> Optional[PriceData]:
        """
        Получает данные по конкретному региону
        
        Args:
            region_id: ID региона
            
        Returns:
            Optional[PriceData]: Данные по региону или None при ошибке
        """
        url = f"{self.BASE_URL}?region={region_id}"
        self.logger.info(f"Получение данных для региона {region_id}: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            html_content = response.text
            
            # Извлекаем правильное название региона
            region_name = self._extract_region_name(html_content, region_id)
            
            # Извлекаем цены на топливо
            fuel_prices = self._extract_prices_from_html(html_content)
            
            if fuel_prices:
                self.logger.info(f"✅ Регион {region_id} ({region_name}): найдено {len(fuel_prices)} цен на топливо")
                for fuel_type, price in fuel_prices.items():
                    self.logger.info(f"   {fuel_type}: {price:.2f} ₽")
            else:
                self.logger.warning(f"⚠️ Регион {region_id} ({region_name}): цены на топливо не найдены")
            
            return PriceData(
                region_id=region_id,
                region_name=region_name,
                fuel_prices=fuel_prices,
                url=url,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                status="success" if fuel_prices else "no_data"
            )
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка получения данных для региона {region_id}: {e}")
            return PriceData(
                region_id=region_id,
                region_name=f"Регион {region_id}",
                fuel_prices={},
                url=url,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                status="error"
            )
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка получения данных для региона {region_id}: {e}")
            return PriceData(
                region_id=region_id,
                region_name=f"Регион {region_id}",
                fuel_prices={},
                url=url,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                status="error"
            )