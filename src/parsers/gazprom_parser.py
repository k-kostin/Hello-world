"""
Парсер для API Газпром Нефть
"""
import requests
from typing import List, Dict, Any, Optional
from loguru import logger

from .base import BaseParser
from config import DEFAULT_HEADERS, TIMEOUT


class GazpromParser(BaseParser):
    """Парсер для API Газпром Нефть"""
    
    def __init__(self, network_name: str, config: Dict[str, Any]):
        super().__init__(network_name, config)
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.api_base = config["api_base"]
        
    def _fetch_stations_list(self) -> List[Dict[str, Any]]:
        """Получает список всех станций"""
        url = self.api_base + self.config["stations_endpoint"]
        logger.info(f"Fetching stations list from: {url}")
        
        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        stations = data.get('stations', [])
        
        logger.info(f"Получено {len(stations)} станций")
        return stations
    
    def _fetch_station_details(self, station_id: str) -> Dict[str, Any]:
        """Получает детальную информацию о станции включая цены"""
        url = self.api_base + self.config["station_detail_endpoint"].format(station_id=station_id)
        logger.info(f"Fetching station details: {url}")
        
        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        
        return response.json()
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Получает данные о всех станциях с ценами"""
        # Сначала получаем список станций
        stations = self._fetch_stations_list()
        
        # Затем получаем детальную информацию по каждой станции
        detailed_data = []
        for i, station in enumerate(stations):
            try:
                station_id = station.get('GPNAZSID')
                if not station_id:
                    continue
                
                logger.info(f"Обработка станции {i+1}/{len(stations)}: {station_id}")
                
                # Получаем детальную информацию
                details = self.retry_on_failure(self._fetch_station_details, station_id)
                
                # Объединяем базовую информацию с деталями
                combined_data = {
                    'station_info': station,
                    'fuel_details': details.get('data', [])
                }
                detailed_data.append(combined_data)
                
                if i < len(stations) - 1:  # Добавляем задержку между запросами
                    self.add_delay()
                    
            except Exception as e:
                logger.error(f"Ошибка при загрузке данных станции {station_id}: {e}")
                self.errors.append(f"Station details error for {station_id}: {e}")
                continue
        
        return detailed_data
    
    def parse_station_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Парсит данные одной станции"""
        try:
            station_info = raw_data.get('station_info', {})
            fuel_details = raw_data.get('fuel_details', [])
            
            # Базовая информация о станции
            station_id = str(station_info.get('GPNAZSID', ''))
            station_name = station_info.get('name', '')
            city = station_info.get('city', '')
            address = station_info.get('address', '')
            latitude = station_info.get('latitude')
            longitude = station_info.get('longitude')
            
            fuel_entries = []
            
            # Обрабатываем каждый вид топлива
            for fuel_item in fuel_details:
                try:
                    # Извлекаем информацию о продукте
                    product = fuel_item.get('product', {})
                    price_info = fuel_item.get('price', {})
                    
                    # Проверяем наличие данных
                    if not product or not price_info:
                        continue
                    
                    fuel_type = product.get('title', product.get('shortTitle', ''))
                    price_value = price_info.get('price')
                    currency = price_info.get('currency', 'RUB')
                    
                    # Пропускаем если нет цены
                    if price_value is None or price_value == 0:
                        continue
                    
                    fuel_entry = {
                        'station_id': station_id,
                        'station_name': station_name,
                        'address': self.clean_address(address),
                        'city': city,
                        'latitude': float(latitude) if latitude else None,
                        'longitude': float(longitude) if longitude else None,
                        'fuel_type': fuel_type,
                        'price': float(price_value),
                        'currency': currency,
                        'source': f"{self.api_base}/stations/{station_id}"
                    }
                    fuel_entries.append(fuel_entry)
                    
                except Exception as e:
                    logger.warning(f"Ошибка обработки топлива: {e}, fuel_item: {fuel_item}")
                    continue
            
            return fuel_entries
            
        except Exception as e:
            logger.error(f"Ошибка парсинга данных станции: {e}, data: {raw_data}")
            return []