"""
Парсер для сайта russiabase.ru - региональные цены на топливо
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import pandas as pd
from typing import List, Dict, Any, Optional
from loguru import logger

from .base import BaseParser
from config import DEFAULT_HEADERS, TIMEOUT
from src.regions import region_manager


class RussiaBaseRegionalParser(BaseParser):
    """Парсер для получения региональных цен с russiabase.ru"""
    
    def __init__(self, network_name: str, config: Dict[str, Any]):
        super().__init__(network_name, config)
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.base_url = "https://russiabase.ru/prices"
        
    def _fetch_region_data(self, region_id: int, region_name: str) -> Dict[str, Any]:
        """Получает данные о ценах на топливо для конкретного региона"""
        url = f"{self.base_url}?region={region_id}"
        logger.debug(f"Fetching region data: {url}")
        
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем данные в JSON-LD или других script тегах
            fuel_prices = self._extract_fuel_prices(soup, region_id, region_name)
            
            return {
                'region_id': region_id,
                'region_name': region_name,
                'url': url,
                'fuel_prices': fuel_prices,
                'status': 'success'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при загрузке данных для региона {region_id} ({region_name}): {e}")
            return {
                'region_id': region_id,
                'region_name': region_name,
                'url': url,
                'fuel_prices': {},
                'status': 'error',
                'error': str(e)
            }
    
    def _extract_fuel_prices(self, soup: BeautifulSoup, region_id: int, region_name: str) -> Dict[str, float]:
        """Извлекает цены на топливо из HTML страницы"""
        fuel_prices = {}
        
        # Метод 1: Поиск в JSON-LD структурах
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                if script.string:
                    data = json.loads(script.string)
                    prices = self._parse_json_ld_fuel_data(data)
                    fuel_prices.update(prices)
            except (json.JSONDecodeError, AttributeError) as e:
                logger.debug(f"Не удалось распарсить JSON-LD: {e}")
                continue
        
        # Метод 2: Поиск в обычных script тегах с данными
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'window.__NEXT_DATA__' in script.string:
                try:
                    # Извлекаем данные Next.js
                    prices = self._parse_nextjs_data(script.string)
                    fuel_prices.update(prices)
                except Exception as e:
                    logger.debug(f"Не удалось распарсить Next.js данные: {e}")
                    continue
        
        # Метод 3: Поиск цен в тексте страницы
        if not fuel_prices:
            fuel_prices = self._extract_prices_from_text(soup)
        
        # Метод 4: Поиск в таблицах или списках
        if not fuel_prices:
            fuel_prices = self._extract_prices_from_tables(soup)
        
        return fuel_prices
    
    def _parse_json_ld_fuel_data(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Парсит данные о топливе из JSON-LD"""
        prices = {}
        
        if isinstance(data, list):
            for item in data:
                prices.update(self._parse_json_ld_fuel_data(item))
        elif isinstance(data, dict):
            # Ищем поля с ценами на топливо
            for key, value in data.items():
                if isinstance(value, dict):
                    prices.update(self._parse_json_ld_fuel_data(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            prices.update(self._parse_json_ld_fuel_data(item))
                elif key.lower() in ['price', 'cost'] and isinstance(value, (int, float, str)):
                    # Пытаемся определить тип топлива по контексту
                    fuel_type = self._detect_fuel_type_from_context(data)
                    if fuel_type:
                        try:
                            price = float(str(value).replace(',', '.'))
                            prices[fuel_type] = price
                        except ValueError:
                            pass
        
        return prices
    
    def _parse_nextjs_data(self, script_content: str) -> Dict[str, float]:
        """Парсит данные из Next.js __NEXT_DATA__"""
        prices = {}
        
        try:
            # Ищем JSON данные в script
            json_start = script_content.find('{')
            json_end = script_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = script_content[json_start:json_end]
                data = json.loads(json_str)
                
                # Рекурсивно ищем цены в данных
                prices = self._extract_prices_from_nested_data(data)
        
        except json.JSONDecodeError as e:
            logger.debug(f"Ошибка парсинга Next.js данных: {e}")
        
        return prices
    
    def _extract_prices_from_text(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Извлекает цены из текста страницы используя регулярные выражения"""
        prices = {}
        text = soup.get_text()
        
        # Паттерны для поиска цен на топливо
        patterns = [
            r'АИ-92[^\d]*(\d+[.,]\d+)',
            r'АИ-95[^\d]*(\d+[.,]\d+)',
            r'АИ-98[^\d]*(\d+[.,]\d+)',
            r'АИ-100[^\d]*(\d+[.,]\d+)',
            r'[Дд]изель[^\d]*(\d+[.,]\d+)',
            r'ДТ[^\d]*(\d+[.,]\d+)',
            r'[Гг]аз[^\d]*(\d+[.,]\d+)',
        ]
        
        fuel_types = ['АИ-92', 'АИ-95', 'АИ-98', 'АИ-100', 'Дизель', 'ДТ', 'Газ']
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    price = float(matches[0].replace(',', '.'))
                    fuel_type = fuel_types[i]
                    if fuel_type == 'ДТ':
                        fuel_type = 'Дизель'
                    prices[fuel_type] = price
                except ValueError:
                    continue
        
        return prices
    
    def _extract_prices_from_tables(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Извлекает цены из таблиц на странице"""
        prices = {}
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    fuel_type = cells[0].get_text(strip=True)
                    price_text = cells[1].get_text(strip=True)
                    
                    # Пытаемся извлечь цену
                    price_match = re.search(r'(\d+[.,]\d+)', price_text)
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', '.'))
                            prices[fuel_type] = price
                        except ValueError:
                            continue
        
        return prices
    
    def _extract_prices_from_nested_data(self, data: Any) -> Dict[str, float]:
        """Рекурсивно извлекает цены из вложенных данных"""
        prices = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ['prices', 'fuel', 'gas', 'petrol', 'diesel']:
                    if isinstance(value, dict):
                        for fuel_type, price in value.items():
                            try:
                                prices[fuel_type] = float(price)
                            except (ValueError, TypeError):
                                pass
                elif isinstance(value, (dict, list)):
                    prices.update(self._extract_prices_from_nested_data(value))
        elif isinstance(data, list):
            for item in data:
                prices.update(self._extract_prices_from_nested_data(item))
        
        return prices
    
    def _detect_fuel_type_from_context(self, data: Dict[str, Any]) -> Optional[str]:
        """Определяет тип топлива по контексту данных"""
        text = json.dumps(data, ensure_ascii=False).lower()
        
        if 'аи-92' in text or 'ai-92' in text:
            return 'АИ-92'
        elif 'аи-95' in text or 'ai-95' in text:
            return 'АИ-95'
        elif 'аи-98' in text or 'ai-98' in text:
            return 'АИ-98'
        elif 'аи-100' in text or 'ai-100' in text:
            return 'АИ-100'
        elif 'дизель' in text or 'diesel' in text or 'дт' in text:
            return 'Дизель'
        elif 'газ' in text or 'gas' in text or 'пропан' in text:
            return 'Газ'
        
        return None
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Получает данные по всем регионам"""
        logger.info("Начинаем сбор данных по регионам с russiabase.ru")
        
        regions = region_manager.get_all_regions()
        all_data = []
        
        for region in regions:
            region_id = region['id']
            region_name = region['name']
            
            logger.info(f"Обрабатываем регион {region_id}: {region_name}")
            
            try:
                region_data = self.retry_on_failure(
                    self._fetch_region_data, 
                    region_id, 
                    region_name
                )
                all_data.append(region_data)
                
                # Добавляем задержку между запросами
                self.add_delay()
                
            except Exception as e:
                logger.error(f"Ошибка при обработке региона {region_id} ({region_name}): {e}")
                self.errors.append(f"Region {region_id} error: {e}")
                
                # Добавляем запись об ошибке
                all_data.append({
                    'region_id': region_id,
                    'region_name': region_name,
                    'url': f"{self.base_url}?region={region_id}",
                    'fuel_prices': {},
                    'status': 'error',
                    'error': str(e)
                })
        
        logger.info(f"Сбор данных завершен. Обработано {len(all_data)} регионов")
        return all_data
    
    def create_fuel_prices_table(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Создает таблицу с ценами на топливо по регионам"""
        rows = []
        
        for region_data in data:
            row = {
                'region_id': region_data['region_id'],
                'region_name': region_data['region_name'],
                'status': region_data['status']
            }
            
            # Добавляем цены на топливо как отдельные колонки
            fuel_prices = region_data.get('fuel_prices', {})
            for fuel_type, price in fuel_prices.items():
                row[fuel_type] = price
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Сортируем колонки: сначала служебные, потом топливо
        service_cols = ['region_id', 'region_name', 'status']
        fuel_cols = [col for col in df.columns if col not in service_cols]
        fuel_cols.sort()  # Сортируем названия топлива
        
        df = df[service_cols + fuel_cols]
        
        return df
    
    def save_to_excel(self, data: List[Dict[str, Any]], filename: str = 'russiabase_regional_prices.xlsx'):
        """Сохраняет данные в Excel файл"""
        df = self.create_fuel_prices_table(data)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Основная таблица
            df.to_excel(writer, sheet_name='Regional_Prices', index=False)
            
            # Сводная статистика
            stats = self._create_statistics(data)
            stats_df = pd.DataFrame(list(stats.items()), columns=['Metric', 'Value'])
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            # Ошибки
            if self.errors:
                errors_df = pd.DataFrame(self.errors, columns=['Error'])
                errors_df.to_excel(writer, sheet_name='Errors', index=False)
        
        logger.info(f"Данные сохранены в файл: {filename}")
        return filename
    
    def _create_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Создает статистику по собранным данным"""
        total_regions = len(data)
        successful_regions = len([d for d in data if d['status'] == 'success'])
        error_regions = total_regions - successful_regions
        
        # Собираем все уникальные типы топлива
        fuel_types = set()
        for region_data in data:
            fuel_types.update(region_data.get('fuel_prices', {}).keys())
        
        return {
            'Total_Regions': total_regions,
            'Successful_Regions': successful_regions,
            'Error_Regions': error_regions,
            'Success_Rate_%': round((successful_regions / total_regions) * 100, 2) if total_regions > 0 else 0,
            'Unique_Fuel_Types': len(fuel_types),
            'Fuel_Types_Found': ', '.join(sorted(fuel_types))
        }
    
    def parse_station_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Парсит данные станций из региональных данных
        
        Примечание: Этот метод не используется в региональном парсере,
        так как мы работаем с агрегированными данными по регионам
        """
        # Для регионального парсера этот метод не актуален
        # так как мы собираем средние цены по регионам, а не по отдельным станциям
        return []