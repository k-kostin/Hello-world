#!/usr/bin/env python3
"""
Тестовый скрипт для нового регионального парсера russiabase.ru
"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parsers.russiabase_parser import RussiaBaseRegionalParser
from loguru import logger

def test_regional_parser():
    """Тестирует региональный парсер"""
    logger.info("Запуск тестирования регионального парсера russiabase.ru")
    
    # Конфигурация для парсера
    config = {
        "type": "russiabase_regional",
        "name": "RussiaBase Regional Prices",
        "description": "Парсер региональных цен на топливо с russiabase.ru"
    }
    
    # Создаем экземпляр парсера
    parser = RussiaBaseRegionalParser("russiabase_regional", config)
    
    try:
        # Тестируем загрузку данных только для нескольких регионов
        logger.info("Начинаем сбор данных...")
        
        # Для тестирования используем только несколько регионов
        test_regions = [
            {'id': 77, 'name': 'Москва'},
            {'id': 78, 'name': 'Санкт-Петербург'},
            {'id': 40, 'name': 'Курская область'},
            {'id': 23, 'name': 'Краснодарский край'},
            {'id': 16, 'name': 'Республика Татарстан'}
        ]
        
        # Собираем данные для тестовых регионов
        test_data = []
        for region in test_regions:
            logger.info(f"Тестируем регион: {region['name']} (ID: {region['id']})")
            region_data = parser._fetch_region_data(region['id'], region['name'])
            test_data.append(region_data)
            
            # Показываем результат
            if region_data['status'] == 'success':
                fuel_prices = region_data.get('fuel_prices', {})
                if fuel_prices:
                    logger.info(f"Найдены цены на топливо: {fuel_prices}")
                else:
                    logger.warning(f"Цены на топливо не найдены для региона {region['name']}")
            else:
                logger.error(f"Ошибка для региона {region['name']}: {region_data.get('error', 'Unknown error')}")
            
            # Небольшая пауза между запросами
            parser.add_delay()
        
        # Создаем таблицу с результатами
        logger.info("Создаем таблицу с результатами...")
        df = parser.create_fuel_prices_table(test_data)
        
        # Выводим таблицу в консоль
        print("\n" + "="*80)
        print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ РЕГИОНАЛЬНОГО ПАРСЕРА")
        print("="*80)
        print(df.to_string(index=False))
        print("="*80)
        
        # Сохраняем в Excel файл
        filename = parser.save_to_excel(test_data, 'test_regional_prices.xlsx')
        logger.info(f"Результаты сохранены в файл: {filename}")
        
        # Статистика
        stats = parser._create_statistics(test_data)
        print("\nСТАТИСТИКА:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        logger.info("Тестирование завершено успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}")
        raise


def test_single_region():
    """Тестирует парсинг одного региона (Курская область)"""
    logger.info("Тестирование парсинга одного региона...")
    
    config = {"type": "russiabase_regional"}
    parser = RussiaBaseRegionalParser("test", config)
    
    # Тестируем Курскую область (ID: 40)
    region_data = parser._fetch_region_data(40, "Курская область")
    
    print("\n" + "="*60)
    print("ТЕСТ ОДНОГО РЕГИОНА: КУРСКАЯ ОБЛАСТЬ")
    print("="*60)
    print(f"Статус: {region_data['status']}")
    print(f"URL: {region_data['url']}")
    
    if region_data['status'] == 'success':
        fuel_prices = region_data.get('fuel_prices', {})
        if fuel_prices:
            print("Найденные цены на топливо:")
            for fuel_type, price in fuel_prices.items():
                print(f"  {fuel_type}: {price} руб.")
        else:
            print("Цены на топливо не найдены")
    else:
        print(f"Ошибка: {region_data.get('error', 'Unknown error')}")
    
    print("="*60)


if __name__ == "__main__":
    # Настройка логирования
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    # Запускаем тесты
    logger.info("Начинаем тестирование нового регионального парсера...")
    
    try:
        # Тест одного региона
        test_single_region()
        
        print("\n")
        
        # Тест нескольких регионов
        test_regional_parser()
        
    except KeyboardInterrupt:
        logger.info("Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)