"""
Конфигурация для парсинга цен сетей АЗС
"""
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

# Общие настройки
OUTPUT_DIR = "data"
LOGS_DIR = "logs"
REQUEST_DELAY = (1, 3)  # Минимальная и максимальная задержка между запросами
RETRY_COUNT = 3
TIMEOUT = 30

# Настройки для Selenium
SELENIUM_CONFIG = {
    "headless": True,
    "window_size": (1920, 1080),
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Конфигурация сетей АЗС
GAS_STATION_NETWORKS = {
    "lukoil": {
        "name": "Лукойл",
        "type": "russiabase",
        "brand_id": 119,
        "base_url": "https://russiabase.ru/prices?brand=119",
        "supports_regions": True
    },
    "bashneft": {
        "name": "Башнефть", 
        "type": "russiabase",
        "brand_id": 292,
        "base_url": "https://russiabase.ru/prices?brand=292",
        "supports_regions": True
    },
    "gazprom": {
        "name": "Газпром",
        "type": "api",
        "api_base": "https://gpnbonus.ru/api",
        "stations_endpoint": "/stations/list",
        "station_detail_endpoint": "/stations/{station_id}"
    },
    "yandex_maps": {
        "name": "Яндекс Карты",
        "type": "selenium",
        "search_url": "https://yandex.ru/maps/213/moscow/search/%D0%B7%D0%B0%D0%BF%D1%80%D0%B0%D0%B2%D0%BA%D0%B8/",
        "scroll_count": 3
    },
    "tatneft": {
        "name": "Татнефть",
        "type": "tatneft_api",
        "api_base": "https://api.gs.tatneft.ru/api/v2",
        "stations_endpoint": "/azs/",
        "station_detail_endpoint": "/azs/{station_id}",
        "fuel_types_endpoint": "/azs/fuel_types/"
    },
    "neftmagistral": {
        "name": "Нефтьмагистраль",
        "type": "russiabase",
        "brand_id": 402,
        "base_url": "https://russiabase.ru/prices?brand=402",
        "supports_regions": True
    },
    "regional_prices": {
        "name": "Региональные цены",
        "type": "russiabase_regional",
        "base_url": "https://russiabase.ru/prices",
        "delay": 1.5,
        "max_regions": None,
        "description": "Средние цены на топливо по регионам России"
    }
}

# Headers для запросов
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Схема выходных данных
OUTPUT_SCHEMA = {
    "station_id": str,
    "network_name": str,
    "station_name": str,
    "address": str,
    "city": str,
    "region": str,  # Добавлено поле региона
    "region_id": int,  # Добавлено поле ID региона
    "latitude": float,
    "longitude": float,
    "fuel_type": str,
    "price": float,
    "currency": str,
    "last_updated": str,
    "source": str
}

# Настройки для работы с регионами
REGIONS_CONFIG = {
    "regions_file": "regions.md",
    "default_regions": [77, 78, 50, 40, 23, 66, 96],  # Москва, СПб, Московская, Курская, Краснодар, Свердловская, Севастополь
    "enable_region_filtering": True,
    "enable_multi_region_parsing": True,
    "max_regions_per_network": 10  # Максимум регионов для парсинга одновременно
}