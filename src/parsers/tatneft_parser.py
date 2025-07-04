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
        self.station_detail_endpoint: str = config.get("station_detail_endpoint", "/azs/{station_id}")
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
        """Получает список всех АЗС"""
        url = self.api_base + self.stations_endpoint
        logger.info(f"Запрашиваем список АЗС: {url}")
        data = self._get_json(url)
        # API возвращает словарь {"results":[...]} или список
        if isinstance(data, dict):
            stations = data.get("results") or data.get("data") or []
        else:
            stations = data
        logger.info(f"Получено {len(stations)} записей об АЗС")
        return stations

    def _fetch_station_details(self, station_id: str) -> Dict[str, Any]:
        url = self.api_base + self.station_detail_endpoint.format(station_id=station_id)
        return self._get_json(url)

    # ---------- BaseParser abstract implementations ----------
    def fetch_data(self) -> List[Dict[str, Any]]:
        stations = self._fetch_stations_list()
        detailed_data = []
        fuel_type_map = self._fetch_fuel_types()

        for idx, station in enumerate(stations):
            sid = station.get("id") or station.get("azs_id") or station.get("GPNAZSID")
            if not sid:
                continue
            try:
                logger.debug(f"[{idx+1}/{len(stations)}] station {sid}")
                details = self.retry_on_failure(self._fetch_station_details, sid)
                combined = {
                    "station_info": station,
                    "detail": details,
                    "fuel_type_map": fuel_type_map,
                }
                detailed_data.append(combined)
            except Exception as e:
                logger.warning(f"Ошибка получения деталей станции {sid}: {e}")
                self.errors.append(f"station {sid}: {e}")
            if idx < len(stations) - 1:
                self.add_delay()
        return detailed_data

    def parse_station_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        station = raw_data.get("station_info", {})
        detail = raw_data.get("detail", {})
        fuel_type_map: Dict[int, str] = raw_data.get("fuel_type_map", {})

        # базовые поля станции
        station_id = str(station.get("id"))
        name = station.get("name") or station.get("title", "")
        city = station.get("city") or station.get("settlement", "")
        address = station.get("address", "")
        latitude = station.get("latitude") or station.get("lat")
        longitude = station.get("longitude") or station.get("lng")

        fuel_entries = []
        fuels = detail.get("fuel") or detail.get("fuels") or detail.get("prices") or []

        for fuel in fuels:
            try:
                fuel_type_id = fuel.get("fuel_type_id") or fuel.get("id")
                fuel_type = fuel_type_map.get(int(fuel_type_id), str(fuel_type_id))
                price_val = fuel.get("price") or fuel.get("price_value")
                currency = fuel.get("currency_code") or fuel.get("currency") or "RUB"

                price = self.clean_price(price_val)
                if price is None:
                    continue

                entry = {
                    "station_id": station_id,
                    "station_name": name,
                    "address": self.clean_address(address),
                    "city": city,
                    "latitude": float(latitude) if latitude else None,
                    "longitude": float(longitude) if longitude else None,
                    "fuel_type": fuel_type,
                    "price": price,
                    "currency": currency,
                    "source": f"{self.api_base}/azs/{station_id}"
                }
                fuel_entries.append(entry)
            except Exception as e:
                logger.warning(f"Ошибка обработки топлива станции {station_id}: {e}")
                continue

        return fuel_entries