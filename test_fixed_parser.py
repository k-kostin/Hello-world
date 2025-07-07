#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправленного регионального парсера
"""
import sys
from pathlib import Path
import logging

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.russiabase_parser import RussiaBaseRegionalParser

def setup_logging():
    """Настройка детального логирования"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('parser_debug.log', encoding='utf-8')
        ]
    )

def test_single_region():
    """Тестирует парсинг одного региона с детальной отладкой"""
    print("🔍 Тестирование исправленного парсера")
    print("=" * 60)
    
    parser = RussiaBaseRegionalParser()
    
    # Тестируем Москву (ID: 77)
    region_id = 77
    region_name = "Москва"
    
    print(f"🗺️ Тестируем регион: {region_name} (ID: {region_id})")
    print("=" * 60)
    
    result = parser.get_region_prices(region_id, region_name)
    
    if result:
        print(f"\n📊 РЕЗУЛЬТАТ ДЛЯ РЕГИОНА: {result.region_name}")
        print(f"🆔 ID региона: {result.region_id}")
        print(f"🔗 URL: {result.url}")
        print(f"⏰ Время: {result.timestamp}")
        print(f"📊 Статус: {result.status}")
        
        if result.fuel_prices:
            print(f"\n💰 НАЙДЕННЫЕ ЦЕНЫ:")
            for fuel_type, price in result.fuel_prices.items():
                print(f"  {fuel_type:10}: {price:.2f} руб/л")
            
            # Проверяем на подозрительные цены
            suspicious_prices = [92.0, 95.0, 98.0, 100.0]
            if any(price in suspicious_prices for price in result.fuel_prices.values()):
                print(f"\n⚠️ ВНИМАНИЕ: Обнаружены подозрительные цены!")
                print(f"Возможно, парсер извлекает номера топлива вместо цен")
            else:
                print(f"\n✅ Цены выглядят реалистично")
        else:
            print(f"\n❌ Цены не найдены")
    else:
        print(f"\n❌ Ошибка при парсинге региона")

def test_multiple_regions():
    """Тестирует парсинг нескольких регионов"""
    print("\n" + "=" * 60)
    print("🔍 Тестирование нескольких регионов")
    print("=" * 60)
    
    parser = RussiaBaseRegionalParser()
    
    # Тестируем несколько ключевых регионов
    test_regions = [
        {'id': 77, 'name': 'Москва'},
        {'id': 78, 'name': 'Санкт-Петербург'},
        {'id': 23, 'name': 'Краснодарский край'},
    ]
    
    results = []
    
    for region in test_regions:
        print(f"\n🔄 Парсинг: {region['name']} (ID: {region['id']})")
        
        result = parser.get_region_prices(region['id'], region['name'])
        if result:
            results.append(result)
        
        # Задержка между запросами
        import time
        time.sleep(2)
    
    # Выводим сводку
    print(f"\n📊 СВОДКА ПО РЕЗУЛЬТАТАМ")
    print("=" * 60)
    
    successful_count = 0
    suspicious_count = 0
    
    for result in results:
        if result.fuel_prices:
            successful_count += 1
            
            # Проверяем на подозрительные цены
            suspicious_prices = [92.0, 95.0, 98.0, 100.0]
            if any(price in suspicious_prices for price in result.fuel_prices.values()):
                suspicious_count += 1
                status = "⚠️ ПОДОЗРИТЕЛЬНО"
            else:
                status = "✅ ОК"
            
            print(f"{result.region_name:20} | {len(result.fuel_prices)} видов топлива | {status}")
        else:
            print(f"{result.region_name:20} | Нет данных | ❌ ОШИБКА")
    
    print(f"\nСтатистика:")
    print(f"  Успешно обработано: {successful_count}/{len(test_regions)}")
    print(f"  Подозрительных результатов: {suspicious_count}")
    
    if suspicious_count > 0:
        print(f"\n⚠️ РЕКОМЕНДАЦИЯ: Требуется дальнейшая доработка парсера")
        print(f"Подозрительные цены указывают на проблемы с извлечением данных")
    else:
        print(f"\n✅ УСПЕХ: Парсер работает корректно!")

def main():
    """Главная функция"""
    setup_logging()
    
    try:
        test_single_region()
        test_multiple_regions()
        
        print(f"\n📝 Детальные логи сохранены в файл: parser_debug.log")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()