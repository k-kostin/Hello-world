#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование улучшенного регионального парсера для russiabase.ru
"""
import sys
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / 'src'))

from parsers.russiabase_parser import RussiaBaseRegionalParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_regions_map():
    """Тест получения полной карты регионов"""
    logger.info("Тестирование получения карты регионов...")
    
    parser = RussiaBaseRegionalParser(delay=0.5)
    regions_map = parser.get_all_regions_map()
    
    if regions_map:
        print(f"\n{'='*60}")
        print(f"ПОЛНАЯ КАРТА РЕГИОНОВ RUSSIABASE.RU")
        print(f"{'='*60}")
        print(f"Всего регионов: {len(regions_map)}")
        print(f"{'='*60}")
        
        # Сортируем по ID для удобного просмотра
        sorted_regions = sorted(regions_map.items(), key=lambda x: x[0])
        
        print("ID | Название региона")
        print("-" * 60)
        for region_id, region_name in sorted_regions:
            print(f"{region_id:2d} | {region_name}")
        
        print(f"{'='*60}")
        
        # Проверим конкретные регионы, которые тестировали ранее
        test_ids = [40, 77, 78, 90, 99]
        print(f"\nПроверка известных ID:")
        for test_id in test_ids:
            if test_id in regions_map:
                print(f"  ID {test_id}: {regions_map[test_id]} ✅")
            else:
                print(f"  ID {test_id}: не найден ❌")
        
        return regions_map
    else:
        print("❌ Не удалось получить карту регионов")
        return {}

def test_single_region_with_map():
    """Тест парсинга одного региона с использованием карты"""
    logger.info("Тестирование парсинга одного региона с картой...")
    
    parser = RussiaBaseRegionalParser(delay=0.5)
    
    # Сначала получаем карту регионов
    regions_map = parser.get_all_regions_map()
    
    # Тестируем Курскую область (ID: 40)
    result = parser.get_region_data(40, regions_map)
    
    if result:
        print(f"\n{'='*60}")
        print(f"ТЕСТ ОДНОГО РЕГИОНА С КАРТОЙ: {result.region_name.upper()}")
        print(f"{'='*60}")
        print(f"ID: {result.region_id}")
        print(f"Название: {result.region_name}")
        print(f"Статус: {result.status}")
        print(f"URL: {result.url}")
        print(f"Время: {result.timestamp}")
        print(f"Найденные цены на топливо:")
        
        if result.fuel_prices:
            for fuel_type, price in result.fuel_prices.items():
                print(f"  {fuel_type}: {price} руб.")
        else:
            print("  Цены не найдены")
        
        print(f"{'='*60}")
        return result
    else:
        print("❌ Не удалось получить данные по региону")
        return None

def test_multiple_regions_optimized():
    """Тест оптимизированного парсинга нескольких регионов"""
    logger.info("Запуск тестирования оптимизированного регионального парсера russiabase.ru")
    
    parser = RussiaBaseRegionalParser(delay=0.5)
    
    # Тестовые регионы (включая правильные ID для Москвы и СПб)
    test_regions = [90, 99, 40, 56, 43]  # Москва, СПб, Курская область, Краснодарский край, Татарстан
    
    logger.info("Начинаем сбор данных...")
    results = parser.get_multiple_regions_data(test_regions)
    
    if results:
        # Создаем DataFrame для отображения результатов
        data_rows = []
        
        for result in results:
            row = {
                'region_id': result.region_id,
                'region_name': result.region_name,
                'status': result.status,
                'timestamp': result.timestamp
            }
            
            # Добавляем цены на топливо как отдельные колонки
            for fuel_type, price in result.fuel_prices.items():
                row[fuel_type] = price
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Заполняем NaN значения прочерками для лучшего отображения
        df = df.fillna('-')
        
        print(f"\n{'='*80}")
        print(f"РЕЗУЛЬТАТЫ ОПТИМИЗИРОВАННОГО ТЕСТИРОВАНИЯ РЕГИОНАЛЬНОГО ПАРСЕРА")
        print(f"{'='*80}")
        print(df.to_string(index=False))
        print(f"{'='*80}")
        
        # Статистика
        total_regions = len(results)
        successful_regions = len([r for r in results if r.status == "success"])
        error_regions = total_regions - successful_regions
        
        # Собираем все найденные типы топлива
        all_fuel_types = set()
        for result in results:
            all_fuel_types.update(result.fuel_prices.keys())
        
        print(f"СТАТИСТИКА:")
        print(f"  Total_Regions: {total_regions}")
        print(f"  Successful_Regions: {successful_regions}")
        print(f"  Error_Regions: {error_regions}")
        print(f"  Success_Rate_%: {(successful_regions/total_regions*100):.1f}")
        print(f"  Unique_Fuel_Types: {len(all_fuel_types)}")
        print(f"  Fuel_Types_Found: {', '.join(sorted(all_fuel_types))}")
        
        # Сохраняем в Excel
        save_to_excel_optimized(results)
        
        return results
    else:
        print("❌ Не удалось получить данные")
        return []

def save_to_excel_optimized(results):
    """Сохранение результатов в Excel файл"""
    logger.info("Создаем таблицу с результатами...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_regional_prices_optimized.xlsx"
    
    # Основная таблица с данными
    data_rows = []
    for result in results:
        row = {
            'region_id': result.region_id,
            'region_name': result.region_name,
            'status': result.status,
            'url': result.url,
            'timestamp': result.timestamp
        }
        
        # Добавляем цены на топливо
        for fuel_type, price in result.fuel_prices.items():
            row[fuel_type] = price
        
        data_rows.append(row)
    
    df = pd.DataFrame(data_rows)
    
    # Статистика
    stats_data = {
        'Метрика': [
            'Всего регионов',
            'Успешно обработано',
            'Ошибок',
            'Процент успешности',
            'Типы топлива найдены'
        ],
        'Значение': [
            len(results),
            len([r for r in results if r.status == "success"]),
            len([r for r in results if r.status != "success"]),
            f"{len([r for r in results if r.status == 'success'])/len(results)*100:.1f}%",
            len(set().union(*[r.fuel_prices.keys() for r in results]))
        ]
    }
    stats_df = pd.DataFrame(stats_data)
    
    # Сохраняем в Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Regional_Prices', index=False)
        stats_df.to_excel(writer, sheet_name='Statistics', index=False)
    
    logger.info(f"Данные сохранены в файл: {filename}")
    logger.info(f"Результаты сохранены в файл: {filename}")

def main():
    """Основная функция тестирования"""
    print("="*80)
    print("ТЕСТИРОВАНИЕ ОПТИМИЗИРОВАННОГО РЕГИОНАЛЬНОГО ПАРСЕРА RUSSIABASE.RU")
    print("="*80)
    
    # Тест 1: Получение полной карты регионов
    print("\n1. Получение полной карты регионов:")
    regions_map = test_regions_map()
    
    # Тест 2: Парсинг одного региона с картой
    print("\n\n2. Тестирование одного региона с картой:")
    test_single_region_with_map()
    
    # Тест 3: Оптимизированный парсинг нескольких регионов
    print("\n\n3. Оптимизированный парсинг нескольких регионов:")
    test_multiple_regions_optimized()
    
    logger.info("Тестирование завершено успешно!")

if __name__ == "__main__":
    main()