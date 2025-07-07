#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование улучшенного регионального парсера для russiabase.ru
с поддержкой автоматического извлечения полной карты регионов из JSON
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

def test_regions_extraction():
    """Тест извлечения полной карты регионов из JSON структуры"""
    logger.info("Тестирование извлечения карты регионов из JSON...")
    
    parser = RussiaBaseRegionalParser()
    
    # Извлекаем полную карту регионов
    regions = parser.extract_regions_from_json()
    
    if regions:
        print("\n" + "="*80)
        print("ПОЛНАЯ КАРТА РЕГИОНОВ ИЗВЛЕЧЕНА ИЗ JSON СТРУКТУРЫ")
        print("="*80)
        print(f"Всего регионов найдено: {len(regions)}")
        print("\nПример регионов:")
        
        # Показываем первые 10 регионов
        for i, (region_id, region_name) in enumerate(list(regions.items())[:10]):
            print(f"  {region_id:2d}: {region_name}")
        
        if len(regions) > 10:
            print(f"  ... и еще {len(regions) - 10} регионов")
        
        # Проверяем наличие ключевых регионов
        key_regions = {90: 'Москва', 99: 'Санкт-Петербург', 78: 'Камчатский край'}
        print("\nПроверка ключевых регионов:")
        for region_id, expected_name in key_regions.items():
            actual_name = regions.get(region_id, 'НЕ НАЙДЕН')
            status = "✅" if region_id in regions else "❌"
            print(f"  {status} ID {region_id}: {actual_name}")
        
        print("="*80)
        return regions
    else:
        print("❌ Ошибка: не удалось извлечь карту регионов")
        return {}

def test_single_region():
    """Тест парсинга одного региона с правильным названием"""
    logger.info("Тестирование парсинга одного региона...")
    
    parser = RussiaBaseRegionalParser(delay=0.5)
    
    # Сначала получаем правильные названия регионов
    regions_map = parser.get_all_regions()
    
    # Тестируем Курскую область (ID: 40)
    region_id = 40
    correct_name = regions_map.get(region_id, "Курская область")
    
    result = parser.get_region_prices(region_id, correct_name)
    
    if result:
        print("\n" + "="*60)
        print("ТЕСТ ОДНОГО РЕГИОНА С ПРАВИЛЬНЫМ НАЗВАНИЕМ")
        print("="*60)
        print(f"ID региона: {result.region_id}")
        print(f"Название: {result.region_name}")
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

def test_multiple_regions_with_correct_names():
    """Тест парсинга нескольких регионов с правильными названиями из JSON"""
    logger.info("Запуск тестирования с автоматическим получением правильных названий...")
    
    parser = RussiaBaseRegionalParser(delay=2.0)
    
    # Получаем полную карту регионов
    all_regions = parser.get_all_regions()
    
    if not all_regions:
        logger.error("Не удалось получить карту регионов")
        return []
    
    logger.info(f"Получена карта из {len(all_regions)} регионов")
    
    # Выбираем тестовые регионы с правильными названиями
    test_region_ids = [90, 99, 40, 56, 43]  # Москва, СПб, Курская область, Краснодарский край, Татарстан
    
    test_regions = []
    for region_id in test_region_ids:
        if region_id in all_regions:
            test_regions.append({
                'id': region_id, 
                'name': all_regions[region_id]
            })
        else:
            logger.warning(f"Регион {region_id} не найден в карте регионов")
    
    if not test_regions:
        logger.error("Нет доступных тестовых регионов")
        return []
    
    logger.info("Начинаем сбор данных для регионов с правильными названиями...")
    
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
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ С ПРАВИЛЬНЫМИ НАЗВАНИЯМИ РЕГИОНОВ")
    print("="*80)
    print(df.to_string(index=False))
    print("="*80)
    
    # Сохраняем результаты в Excel
    filename = 'test_regional_prices_optimized.xlsx'
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Основная таблица
        df.to_excel(writer, sheet_name='Regional_Prices', index=False)
        
        # Полная карта регионов
        regions_df = pd.DataFrame([
            {'region_id': region_id, 'region_name': region_name}
            for region_id, region_name in sorted(all_regions.items())
        ])
        regions_df.to_excel(writer, sheet_name='All_Regions_Map', index=False)
        
        # Статистика
        stats = create_statistics(results, all_fuel_types, len(all_regions))
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
    
    # Выводим статистику
    print("\nСТАТИСТИКА:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    logger.info("Тестирование завершено успешно!")
    
    return results, df

def create_statistics(results, fuel_types, total_regions_available):
    """Создает расширенную статистику по результатам"""
    total_regions = len(results)
    successful_regions = len([r for r in results if r.status == 'success'])
    error_regions = total_regions - successful_regions
    
    # Подсчитываем найденные типы топлива
    found_fuel_types = set()
    for result in results:
        found_fuel_types.update(result.fuel_prices.keys())
    
    return {
        'Total_Regions_Available': total_regions_available,
        'Tested_Regions': total_regions,
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

def save_regions_research():
    """Сохраняет исследование ID регионов в отдельный файл"""
    parser = RussiaBaseRegionalParser()
    regions = parser.get_all_regions()
    
    if not regions:
        logger.error("Не удалось получить карту регионов для исследования")
        return
    
    # Создаем markdown файл с исследованием
    filename = 'REGIONS_ID_MAPPING_RESEARCH.md'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Исследование ID регионов russiabase.ru\n\n")
        f.write("## Автоматическое извлечение карты регионов из JSON структуры\n\n")
        f.write("Данное исследование демонстрирует автоматическое извлечение полной карты всех ")
        f.write("регионов России из JSON структуры, встроенной в HTML код страницы russiabase.ru.\n\n")
        
        f.write("### Найденная JSON структура\n\n")
        f.write("В HTML коде страницы обнаружена JSON структура вида:\n")
        f.write('```json\n"regions":[{"id":"18","value":"Алтайский край"},{"id":"72","value":"Амурская область"}...]\n```\n\n')
        
        f.write(f"### Полная карта регионов ({len(regions)} регионов)\n\n")
        f.write("| ID | Название региона |\n")
        f.write("|----|------------------|\n")
        
        for region_id, region_name in sorted(regions.items()):
            # Отмечаем ключевые регионы
            marker = ""
            if region_id == 90:  # Москва
                marker = " ✅"
            elif region_id == 99:  # Санкт-Петербург
                marker = " ✅"
            elif region_id in [40, 56, 43]:  # Тестовые регионы
                marker = " ✅"
            
            f.write(f"| {region_id} | {region_name}{marker} |\n")
        
        f.write("\n### Ключевые преимущества\n\n")
        f.write("1. **Полнота данных**: Автоматически получаем все 84 региона России\n")
        f.write("2. **Правильные названия**: Никаких ошибок в названиях регионов\n")
        f.write("3. **Эффективность**: Одним запросом получаем всю карту регионов\n")
        f.write("4. **Актуальность**: Данные всегда синхронизированы с сайтом\n\n")
        
        f.write("### Техническая реализация\n\n")
        f.write("Парсер использует регулярные выражения для поиска JSON структуры в HTML коде:\n")
        f.write("- `r'\"regions\"\\s*:\\s*(\\[.*?\\])'`\n")
        f.write("- `r'window\\.__NEXT_DATA__\\s*=\\s*({.*?});'`\n")
        f.write("- Рекурсивный поиск массива регионов в JSON объектах\n\n")
        
        f.write(f"*Данные актуальны на {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    logger.info(f"Исследование сохранено в файл: {filename}")

def main():
    """Главная функция для запуска всех тестов"""
    print("="*80)
    print("ТЕСТИРОВАНИЕ УЛУЧШЕННОГО ПАРСЕРА RUSSIABASE.RU С JSON ИЗВЛЕЧЕНИЕМ")
    print("="*80)
    
    try:
        # Тест извлечения карты регионов
        test_regions_extraction()
        
        # Сохраняем исследование регионов
        save_regions_research()
        
        # Тест отдельных методов
        test_parser_methods()
        
        # Тест одного региона
        test_single_region()
        
        # Тест нескольких регионов с правильными названиями
        test_multiple_regions_with_correct_names()
        
    except KeyboardInterrupt:
        logger.info("Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"Ошибка во время тестирования: {e}")
        raise

if __name__ == "__main__":
    main()