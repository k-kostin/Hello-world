#!/usr/bin/env python3
"""
Скрипт для тестирования обновленного парсера региональных цен на топливо
с сайта russiabase.ru с новыми селекторами
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.russiabase_parser import RussiaBaseRegionalParser
from src.regions import RegionManager

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'test_parser_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def test_region_parsing():
    """Тестирует парсинг цен для нескольких регионов"""
    
    print("🚀 Запуск тестирования обновленного парсера russiabase.ru")
    print("=" * 60)
    
    # Создаем парсер
    parser = RussiaBaseRegionalParser(delay=2.0)
    region_manager = RegionManager()
    
    # Получаем список тестовых регионов
    test_regions = [
        {"id": 56, "name": "Краснодарский край"},  # Регион из примера пользователя
        {"id": 77, "name": "Москва"},
        {"id": 78, "name": "Санкт-Петербург"},
        {"id": 23, "name": "Краснодарский край"},
        {"id": 16, "name": "Республика Татарстан"}
    ]
    
    print(f"📍 Тестируем парсинг для {len(test_regions)} регионов:")
    for region in test_regions:
        print(f"  - {region['name']} (ID: {region['id']})")
    print()
    
    # Парсим данные для каждого региона
    results = []
    for i, region in enumerate(test_regions, 1):
        print(f"🔄 [{i}/{len(test_regions)}] Парсинг: {region['name']} (ID: {region['id']})")
        
        try:
            result = parser.get_region_prices(region['id'], region['name'])
            
            if result and result.fuel_prices:
                results.append(result)
                print(f"✅ Успешно извлечены цены:")
                for fuel_type, price in result.fuel_prices.items():
                    print(f"    {fuel_type}: {price:.2f} руб/л")
            else:
                print(f"❌ Не удалось извлечь цены для региона {region['name']}")
            
        except Exception as e:
            print(f"💥 Ошибка при парсинге региона {region['name']}: {e}")
        
        print()
    
    # Итоговая статистика
    print("=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    
    if results:
        print(f"Успешно обработано регионов: {len(results)}")
        print(f"Регионов с ошибками: {len(test_regions) - len(results)}")
        
        # Сводная таблица по видам топлива
        fuel_data = {}
        for result in results:
            for fuel_type, price in result.fuel_prices.items():
                if fuel_type not in fuel_data:
                    fuel_data[fuel_type] = []
                fuel_data[fuel_type].append(price)
        
        print("\n📈 Средние цены по видам топлива:")
        for fuel_type, prices in fuel_data.items():
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            print(f"  {fuel_type:10}: ср. {avg_price:.2f}, мин. {min_price:.2f}, макс. {max_price:.2f} руб/л")
        
        # Детальная таблица по регионам
        print("\n🗺️  Детальная таблица по регионам:")
        print("-" * 80)
        print(f"{'Регион':<25} {'АИ-92':<8} {'АИ-95':<8} {'АИ-98':<8} {'ДТ':<8} {'Пропан':<8}")
        print("-" * 80)
        
        for result in results:
            fuel_prices = result.fuel_prices
            region_name = result.region_name[:24]  # Обрезаем длинные названия
            
            ai92 = f"{fuel_prices.get('АИ-92', 0):.1f}" if fuel_prices.get('АИ-92') else "-"
            ai95 = f"{fuel_prices.get('АИ-95', 0):.1f}" if fuel_prices.get('АИ-95') else "-" 
            ai98 = f"{fuel_prices.get('АИ-98', 0):.1f}" if fuel_prices.get('АИ-98') else "-"
            dt = f"{fuel_prices.get('ДТ', 0):.1f}" if fuel_prices.get('ДТ') else "-"
            propan = f"{fuel_prices.get('Пропан', 0):.1f}" if fuel_prices.get('Пропан') else "-"
            
            print(f"{region_name:<25} {ai92:<8} {ai95:<8} {ai98:<8} {dt:<8} {propan:<8}")
        
        print("-" * 80)
        
    else:
        print("❌ Не удалось получить данные ни для одного региона")
    
    print(f"\n✅ Тестирование завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def test_fuel_normalization():
    """Тестирует нормализацию названий топлива"""
    print("\n🧪 Тестирование нормализации названий топлива")
    print("-" * 50)
    
    parser = RussiaBaseRegionalParser()
    
    test_names = [
        "АИ-92", "аи-92", "AI-92", "92", "Аи-92+",
        "АИ-95", "аи-95", "AI-95", "95", "Аи-95+", 
        "АИ-98", "аи-98", "98",
        "АИ-100", "100",
        "Дизель", "ДТ", "дт", "Diesel",
        "Газ", "Пропан", "LPG", "СУГ"
    ]
    
    for name in test_names:
        normalized = parser._normalize_fuel_name(name)
        print(f"  '{name}' -> '{normalized}'")

def main():
    """Главная функция"""
    setup_logging()
    
    try:
        # Тестируем нормализацию названий
        test_fuel_normalization()
        
        # Тестируем парсинг регионов
        test_region_parsing()
        
    except KeyboardInterrupt:
        print("\n⚠️  Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()