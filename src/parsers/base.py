"""
Базовый класс для всех парсеров цен АЗС
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import random
from datetime import datetime
import polars as pl
from loguru import logger

from config import REQUEST_DELAY, RETRY_COUNT


class BaseParser(ABC):
    """Базовый абстрактный класс для парсеров цен АЗС"""
    
    def __init__(self, network_name: str, config: Dict[str, Any]):
        self.network_name = network_name
        self.config = config
        self.session_data = []
        self.errors = []
        
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Основной метод для получения данных с источника"""
        pass
    
    @abstractmethod
    def parse_station_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Метод для парсинга данных отдельной станции"""
        pass
    
    def normalize_data(self, parsed_data: List[Dict[str, Any]]) -> pl.DataFrame:
        """Нормализация данных в единую схему"""
        normalized_rows = []
        
        for item in parsed_data:
            try:
                normalized_item = {
                    "station_id": str(item.get("station_id", "")),
                    "network_name": self.network_name,
                    "station_name": str(item.get("station_name", "")),
                    "address": str(item.get("address", "")),
                    "city": str(item.get("city", "")),
                    "latitude": float(item.get("latitude", 0.0)) if item.get("latitude") else None,
                    "longitude": float(item.get("longitude", 0.0)) if item.get("longitude") else None,
                    "fuel_type": str(item.get("fuel_type", "")),
                    "price": float(item.get("price", 0.0)) if item.get("price") else None,
                    "currency": str(item.get("currency", "RUB")),
                    "last_updated": datetime.now().isoformat(),
                    "source": str(item.get("source", self.config.get("base_url", "")))
                }
                normalized_rows.append(normalized_item)
            except Exception as e:
                logger.error(f"Ошибка нормализации данных: {e}, item: {item}")
                self.errors.append(f"Normalization error: {e}")
                
        return pl.DataFrame(normalized_rows)
    
    def add_delay(self):
        """Добавляет случайную задержку между запросами"""
        delay = random.uniform(*REQUEST_DELAY)
        time.sleep(delay)
    
    def retry_on_failure(self, func, *args, **kwargs):
        """Повторяет выполнение функции при ошибке"""
        for attempt in range(RETRY_COUNT):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
                if attempt == RETRY_COUNT - 1:
                    raise
                self.add_delay()
    
    def run(self) -> pl.DataFrame:
        """Основной метод запуска парсинга"""
        logger.info(f"Начинаем парсинг сети {self.network_name}")
        
        try:
            # Получение сырых данных
            raw_data = self.fetch_data()
            logger.info(f"Получено {len(raw_data)} сырых записей")
            
            # Парсинг данных
            parsed_data = []
            for raw_item in raw_data:
                try:
                    station_data = self.parse_station_data(raw_item)
                    parsed_data.extend(station_data)
                except Exception as e:
                    logger.error(f"Ошибка парсинга станции: {e}")
                    self.errors.append(f"Station parse error: {e}")
            
            logger.info(f"Обработано {len(parsed_data)} записей")
            
            # Нормализация данных
            df = self.normalize_data(parsed_data)
            
            logger.info(f"Парсинг сети {self.network_name} завершен. Итого записей: {len(df)}")
            
            if self.errors:
                logger.warning(f"Обнаружены ошибки ({len(self.errors)}): {self.errors[:5]}")
            
            return df
            
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге {self.network_name}: {e}")
            raise
    
    def clean_price(self, price_str: str) -> Optional[float]:
        """Очистка и нормализация цены"""
        if not price_str or price_str in ['–', '-', '', 'N/A']:
            return None
        
        try:
            # Удаляем все символы кроме цифр, точки и запятой
            cleaned = ''.join(c for c in str(price_str) if c.isdigit() or c in '.,')
            if ',' in cleaned:
                cleaned = cleaned.replace(',', '.')
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
    
    def clean_address(self, address: str) -> str:
        """Очистка адреса"""
        if not address:
            return ""
        return str(address).strip().replace('\n', ' ').replace('\t', ' ')
    
    def extract_city_from_address(self, address: str) -> str:
        """Извлечение города из адреса"""
        if not address:
            return ""
        
        # Простая логика извлечения города
        for city_prefix in ['г. ', 'город ', 'гор. ']:
            if city_prefix in address:
                start = address.find(city_prefix) + len(city_prefix)
                end = address.find(',', start)
                if end == -1:
                    end = address.find(' ', start + 5)  # Берем следующий пробел после 5 символов
                if end != -1:
                    return address[start:end].strip()
                else:
                    return address[start:].strip()
        
        # Если префикс не найден, пытаемся извлечь из начала адреса
        parts = address.split(',')
        if len(parts) > 1:
            return parts[-1].strip()  # Последняя часть обычно город
        
        return ""