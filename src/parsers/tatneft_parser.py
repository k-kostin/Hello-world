from typing import List, Dict, Any, Optional
import requests
from loguru import logger
import time

import polars as pl

from .base import BaseParser
from config import DEFAULT_HEADERS, TIMEOUT, REQUEST_DELAY


class TatneftParser(BaseParser):
    """Парсер API Татнефть (https://api.gs.tatneft.ru)"""

    def __init__(self, network_name: str, config: Dict[str, Any]):
        super().__init__(network_name, config)
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.api_base: str = config["api_base"].rstrip("/")  # https://api.gs.tatneft.ru/api/v2
        self.stations_endpoint: str = config.get("stations_endpoint", "/azs/")
        # Removed individual station detail endpoint as it's not working and not needed
        self.fuel_types_endpoint: str = config.get("fuel_types_endpoint", "/azs/fuel_types/")
        self._fuel_type_map: Optional[Dict[int, str]] = None

    # ---------- Low-level API helpers ----------
    def _get_json(self, url: str) -> Any:
        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def _fetch_fuel_types(self) -> Dict[int, str]:
        """Возвращает отображение id -> название топлива"""
        if self._fuel_type_map is not None:
            return self._fuel_type_map
        url = self.api_base + self.fuel_types_endpoint
        logger.debug(f"Fetching fuel types: {url}")
        try:
            data = self._get_json(url)
            # ожидаемый формат: [{"id":30, "short_name":"АИ-92", ...}, ...]
            mapping = {}
            for item in data:
                fid = item.get("id") or item.get("fuel_type_id")
                name = item.get("short_name") or item.get("name") or item.get("title")
                if fid is not None and name:
                    mapping[int(fid)] = name
            self._fuel_type_map = mapping
        except Exception as e:
            logger.error(f"Не удалось загрузить справочник типов топлива: {e}")
            self._fuel_type_map = {}
        return self._fuel_type_map

    def _fetch_stations_list(self) -> List[Dict[str, Any]]:
        """Получает список всех АЗС с полной информацией"""
        url = self.api_base + self.stations_endpoint
        logger.info(f"Запрашиваем список АЗС: {url}")
        data = self._get_json(url)
        
        # API возвращает словарь с полем "data" содержащим массив станций
        stations = []
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                stations = data["data"]
            elif "results" in data and isinstance(data["results"], list):
                stations = data["results"]
            elif isinstance(data, list):
                stations = data
        elif isinstance(data, list):
            stations = data
            
        logger.info(f"Получено {len(stations)} записей об АЗС")
        return stations

    # ---------- BaseParser abstract implementations ----------
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Получает данные АЗС, используя только основной endpoint /azs/"""
        stations = self._fetch_stations_list()
        
        # Пытаемся получить справочник типов топлива, но если не получается - не критично
        try:
            fuel_type_map = self._fetch_fuel_types()
        except Exception as e:
            logger.warning(f"Не удалось загрузить справочник типов топлива: {e}")
            fuel_type_map = {}

        # Теперь просто возвращаем станции с добавленным справочником топлива
        # Не делаем дополнительных запросов к /azs/{id}, так как они возвращают 404
        detailed_data = []
        for idx, station in enumerate(stations):
            try:
                combined = {
                    "station_info": station,
                    "fuel_type_map": fuel_type_map,
                }
                detailed_data.append(combined)
                logger.debug(f"[{idx+1}/{len(stations)}] Обработана станция {station.get('id', 'N/A')}")
            except Exception as e:
                logger.warning(f"Ошибка обработки станции {station.get('id', 'N/A')}: {e}")
                self.errors.append(f"station {station.get('id', 'N/A')}: {e}")
        
        return detailed_data

    def parse_station_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Парсит данные станции из ответа /azs/ endpoint"""
        station = raw_data.get("station_info", {})
        fuel_type_map: Dict[int, str] = raw_data.get("fuel_type_map", {})

        # Извлекаем основную информацию о станции
        station_id = str(station.get("id", ""))
        name = station.get("name") or station.get("title", "")
        region = station.get("region", "")
        address = station.get("address", "")
        latitude = station.get("lat") or station.get("latitude")
        longitude = station.get("lon") or station.get("longitude")
        number = station.get("number")

        # Формируем адрес если он пустой
        if not address and region:
            address = region

        fuel_entries = []
        # В ответе /azs/ топливо находится в поле "fuel"
        fuels = station.get("fuel", [])

        for fuel in fuels:
            try:
                # Пытаемся извлечь информацию о топливе из разных возможных полей
                fuel_type_id = fuel.get("fuel_type_id") or fuel.get("id") or fuel.get("type_id")
                
                # Определяем тип топлива
                if fuel_type_id and fuel_type_map:
                    fuel_type = fuel_type_map.get(int(fuel_type_id), f"Тип_{fuel_type_id}")
                else:
                    # Пытаемся получить название из самого объекта топлива
                    fuel_type = (fuel.get("name") or fuel.get("title") or 
                                fuel.get("short_name") or f"Тип_{fuel_type_id}")

                # Извлекаем цену
                price_val = fuel.get("price") or fuel.get("price_value") or fuel.get("cost")
                currency = station.get("currency_code", "RUB")

                price = self.clean_price(price_val)
                if price is None:
                    continue

                entry = {
                    "station_id": station_id,
                    "station_name": name,
                    "address": self.clean_address(address),
                    "city": region,
                    "latitude": float(latitude) if latitude else None,
                    "longitude": float(longitude) if longitude else None,
                    "fuel_type": fuel_type,
                    "price": price,
                    "currency": currency,
                    "source": f"{self.api_base}/azs/"
                }
                
                # Добавляем дополнительную информацию если доступна
                if number:
                    entry["station_number"] = number
                    
                fuel_entries.append(entry)
                
            except Exception as e:
                logger.warning(f"Ошибка обработки топлива станции {station_id}: {e}")
                continue

        return fuel_entries