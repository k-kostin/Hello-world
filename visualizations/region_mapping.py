#!/usr/bin/env python3
"""
Скрипт для создания маппинга между названиями регионов в geojson файле и данными с ценами.
"""

import json
from typing import Dict, List, Tuple
from pathlib import Path
import re

def load_geojson_regions(geojson_path: str) -> List[Dict]:
    """Загружает названия регионов из geojson файла."""
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    regions = []
    for feature in data['features']:
        props = feature['properties']
        regions.append({
            'name_ru': props.get('name', ''),
            'name_latin': props.get('name_latin', ''),
            'cartodb_id': props.get('cartodb_id', None)
        })
    
    return regions

def load_fuel_price_regions(prices_path: str) -> List[Dict]:
    """Загружает названия регионов из файла с ценами на топливо."""
    with open(prices_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    regions = []
    for item in data:
        regions.append({
            'region_id': item.get('region_id', None),
            'region_name': item.get('region_name', ''),
            'fuel_prices': item.get('fuel_prices', {})
        })
    
    return regions

def normalize_region_name(name: str) -> str:
    """Нормализует название региона для лучшего сопоставления."""
    # Убираем лишние пробелы
    name = name.strip()
    
    # Приводим к нижнему регистру для сравнения
    name_lower = name.lower()
    
    # Убираем типичные окончания
    patterns = [
        r'\s+область$',
        r'\s+край$',
        r'\s+республика$',
        r'республика\s+',
        r'\s+автономный\s+округ$',
        r'\s+автономная\s+область$',
        r'\s+округ$',
        r'\s+федерального\s+значения$'
    ]
    
    for pattern in patterns:
        name_lower = re.sub(pattern, '', name_lower)
    
    return name_lower.strip()

def create_region_mapping(geojson_regions: List[Dict], fuel_regions: List[Dict]) -> Dict:
    """Создает маппинг между регионами из geojson и данными с ценами."""
    mapping = {}
    unmatched_geojson = []
    unmatched_fuel = []
    
    # Создаем словарь нормализованных названий из fuel_regions
    fuel_normalized = {}
    for fuel_region in fuel_regions:
        normalized = normalize_region_name(fuel_region['region_name'])
        fuel_normalized[normalized] = fuel_region
    
    # Пытаемся сопоставить
    for geo_region in geojson_regions:
        geo_normalized = normalize_region_name(geo_region['name_ru'])
        
        if geo_normalized in fuel_normalized:
            mapping[geo_region['name_ru']] = fuel_normalized[geo_normalized]
        else:
            unmatched_geojson.append(geo_region)
    
    # Находим несопоставленные регионы из fuel_regions
    matched_fuel_names = {v['region_name'] for v in mapping.values()}
    unmatched_fuel = [r for r in fuel_regions if r['region_name'] not in matched_fuel_names]
    
    return {
        'mapping': mapping,
        'unmatched_geojson': unmatched_geojson,
        'unmatched_fuel': unmatched_fuel,
        'stats': {
            'total_geojson': len(geojson_regions),
            'total_fuel': len(fuel_regions),
            'matched': len(mapping),
            'unmatched_geojson': len(unmatched_geojson),
            'unmatched_fuel': len(unmatched_fuel)
        }
    }

def save_mapping(mapping_data: Dict, output_path: str):
    """Сохраняет маппинг в JSON файл."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, ensure_ascii=False, indent=2)

def main():
    # Пути к файлам
    geojson_path = "data/geojson/russia_reg v2.geojson"
    prices_path = "regional_prices_20250707_145425.json"  # Последний файл с ценами
    output_path = "data/region_mapping.json"
    
    print("Загрузка данных...")
    
    # Загружаем данные
    geojson_regions = load_geojson_regions(geojson_path)
    fuel_regions = load_fuel_price_regions(prices_path)
    
    print(f"Загружено {len(geojson_regions)} регионов из geojson")
    print(f"Загружено {len(fuel_regions)} регионов из данных с ценами")
    
    # Создаем маппинг
    mapping_result = create_region_mapping(geojson_regions, fuel_regions)
    
    # Сохраняем результат
    save_mapping(mapping_result, output_path)
    
    print(f"\nРезультаты сопоставления:")
    print(f"Всего регионов в geojson: {mapping_result['stats']['total_geojson']}")
    print(f"Всего регионов в данных с ценами: {mapping_result['stats']['total_fuel']}")
    print(f"Успешно сопоставлено: {mapping_result['stats']['matched']}")
    print(f"Не сопоставлено из geojson: {mapping_result['stats']['unmatched_geojson']}")
    print(f"Не сопоставлено из данных с ценами: {mapping_result['stats']['unmatched_fuel']}")
    
    if mapping_result['unmatched_geojson']:
        print(f"\nНе сопоставленные регионы из geojson:")
        for region in mapping_result['unmatched_geojson'][:5]:  # показываем первые 5
            print(f"  - {region['name_ru']}")
    
    if mapping_result['unmatched_fuel']:
        print(f"\nНе сопоставленные регионы из данных с ценами:")
        for region in mapping_result['unmatched_fuel'][:5]:  # показываем первые 5
            print(f"  - {region['region_name']}")
    
    print(f"\nМаппинг сохранен в: {output_path}")

if __name__ == "__main__":
    main()