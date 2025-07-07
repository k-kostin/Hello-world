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

def test_single_region():
    """Тест парсинга одного региона"""
    logger.info("Тестирование парсинга одного региона...")
    
    parser = RussiaBaseRegionalParser(delay=0.5)
    
    # Тестируем Курскую область (ID: 40)
    result = parser.get_region_prices(40, "Курская область")
    
    if result:
        print("\n" + "="*60)
        print("ТЕСТ ОДНОГО РЕГИОНА: КУРСКАЯ ОБЛАСТЬ")
        print("="*60)
        print(f"Статус: {result.status}")
        print(f"URL: {result.url}")
        print("Найденные цены на топливо:")
        
        if result.fuel_prices:
            for fuel_type, price in result.fuel_prices.items():
                print(f"  {fuel_type}: {price} руб.")
        else:
            print("  Цены не найдены")
        
        print("="*60)
        print()
        
        return result
    else:
        print("Ошибка: не удалось получить данные для региона")
        return None

def test_multiple_regions():
    """Тест парсинга нескольких регионов"""
    logger.info("Запуск тестирования регионального парсера russiabase.ru")
    
    # Тестовые регионы
    test_regions = [
        {'id': 77, 'name': 'Москва'},
        {'id': 78, 'name': 'Санкт-Петербург'},
        {'id': 40, 'name': 'Курская область'},
        {'id': 23, 'name': 'Краснодарский край'},
        {'id': 16, 'name': 'Республика Татарстан'},
    ]
    
    # Создаем парсер
    parser = RussiaBaseRegionalParser(delay=2.0)  # 2 секунды между запросами
    
    logger.info("Начинаем сбор данных...")
    
    # Парсим регионы
    results = parser.parse_multiple_regions(test_regions)
    
    logger.info("Создаем таблицу с результатами...")
    
    # Создаем DataFrame для результатов
    rows = []
    all_fuel_types = set()
    
    for result in results:
        row = {
            'region_id': result.region_id,
            'region_name': result.region_name,
            'status': result.status
        }
        
        # Добавляем цены на топливо
        for fuel_type, price in result.fuel_prices.items():
            row[fuel_type] = price
            all_fuel_types.add(fuel_type)
        
        rows.append(row)
    
    # Создаем DataFrame
    df = pd.DataFrame(rows)
    
    # Убеждаемся, что все типы топлива представлены как колонки
    service_cols = ['region_id', 'region_name', 'status']
    fuel_cols = sorted(list(all_fuel_types))
    
    # Переупорядочиваем колонки
    for col in fuel_cols:
        if col not in df.columns:
            df[col] = None
    
    df = df[service_cols + fuel_cols]
    
    # Выводим результаты
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ РЕГИОНАЛЬНОГО ПАРСЕРА")
    print("="*80)
    print(df.to_string(index=False))
    print("="*80)
    
    # Сохраняем результаты в Excel
    filename = 'test_regional_prices.xlsx'
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Основная таблица
        df.to_excel(writer, sheet_name='Regional_Prices', index=False)
        
        # Статистика
        stats = create_statistics(results, all_fuel_types)
        stats_df = pd.DataFrame(list(stats.items()), columns=['Metric', 'Value'])
        stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        # Детальная информация
        details = []
        for result in results:
            details.append({
                'Region_ID': result.region_id,
                'Region_Name': result.region_name,
                'URL': result.url,
                'Timestamp': result.timestamp,
                'Status': result.status,
                'Fuel_Count': len(result.fuel_prices)
            })
        
        details_df = pd.DataFrame(details)
        details_df.to_excel(writer, sheet_name='Details', index=False)
    
    logger.info(f"Данные сохранены в файл: {filename}")
    logger.info(f"Результаты сохранены в файл: {filename}")
    
    # Выводим статистику
    print("\nСТАТИСТИКА:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    logger.info("Тестирование завершено успешно!")
    
    return results, df

def create_statistics(results, fuel_types):
    """Создает статистику по результатам"""
    total_regions = len(results)
    successful_regions = len([r for r in results if r.status == 'success'])
    error_regions = total_regions - successful_regions
    
    # Подсчитываем найденные типы топлива
    found_fuel_types = set()
    for result in results:
        found_fuel_types.update(result.fuel_prices.keys())
    
    return {
        'Total_Regions': total_regions,
        'Successful_Regions': successful_regions,
        'Error_Regions': error_regions,
        'Success_Rate_%': round((successful_regions / total_regions) * 100, 2) if total_regions > 0 else 0,
        'Unique_Fuel_Types': len(found_fuel_types),
        'Fuel_Types_Found': ', '.join(sorted(found_fuel_types)) if found_fuel_types else 'None'
    }

def test_parser_methods():
    """Тест отдельных методов парсера"""
    logger.info("Тестирование методов парсера...")
    
    parser = RussiaBaseRegionalParser()
    
    # Тест нормализации названий топлива
    test_fuel_names = [
        'АИ-92', 'аи-95', 'AI-98', 'дизель', 'ГАЗ', 'пропан',
        'ai92', 'Дизельное топливо', '95', 'Бензин АИ-95'
    ]
    
    print("\nТест нормализации названий топлива:")
    for name in test_fuel_names:
        normalized = parser._normalize_fuel_name(name)
        print(f"  '{name}' -> '{normalized}'")
    
    # Тест извлечения цены из текста
    test_prices = [
        '55.5', '61,23', '72.45 руб.', '55.5754', 'цена: 68.90', 'нет цены'
    ]
    
    print("\nТест извлечения цен из текста:")
    for text in test_prices:
        price = parser._extract_price_from_text(text)
        print(f"  '{text}' -> {price}")
    
    # Показываем доступные типы топлива
    print(f"\nДоступные типы топлива: {parser.get_available_fuel_types()}")

def main():
    """Главная функция для запуска всех тестов"""
    print("="*80)
    print("ТЕСТИРОВАНИЕ УЛУЧШЕННОГО РЕГИОНАЛЬНОГО ПАРСЕРА RUSSIABASE.RU")
    print("="*80)
    
    try:
        # Тест отдельных методов
        test_parser_methods()
        
        # Тест одного региона
        test_single_region()
        
        # Тест нескольких регионов
        test_multiple_regions()
        
    except KeyboardInterrupt:
        logger.info("Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"Ошибка во время тестирования: {e}")
        raise

if __name__ == "__main__":
    main()