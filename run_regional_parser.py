#!/usr/bin/env python3
"""
Продукционный скрипт для сбора региональных цен на топливо с russiabase.ru
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from typing import Optional, List
from src.parsers.russiabase_parser import RussiaBaseRegionalParser
from src.regions import region_manager
from loguru import logger


def setup_logging(verbose: bool = False):
    """Настройка логирования"""
    logger.remove()
    
    # Консольный вывод
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stdout, 
        level=level, 
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"
    )
    
    # Логирование в файл
    log_file = f"logs/regional_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    os.makedirs("logs", exist_ok=True)
    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="10 MB"
    )
    
    logger.info(f"Логи сохраняются в файл: {log_file}")


def run_full_collection():
    """Запуск полного сбора данных по всем регионам"""
    logger.info("🚀 Начинаем полный сбор региональных цен на топливо")
    
    # Конфигурация парсера
    config = {
        "type": "russiabase_regional",
        "name": "RussiaBase Regional Fuel Prices",
        "description": "Сбор средних цен на топливо по регионам России"
    }
    
    # Создаем парсер
    parser = RussiaBaseRegionalParser("regional_fuel_prices", config)
    
    try:
        # Показываем информацию о регионах
        regions = region_manager.get_all_regions()
        logger.info(f"📊 Будет обработано регионов: {len(regions)}")
        
        # Сбор данных
        start_time = datetime.now()
        logger.info(f"⏰ Начало сбора: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        data = parser.fetch_data()
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"⏱️ Сбор завершен за: {duration}")
        
        # Создание таблицы
        logger.info("📋 Создание сводной таблицы...")
        df = parser.create_fuel_prices_table(data)
        
        # Показываем предварительные результаты
        successful_regions = len([d for d in data if d['status'] == 'success'])
        logger.info(f"✅ Успешно обработано регионов: {successful_regions}/{len(data)}")
        
        # Показываем несколько примеров
        logger.info("📝 Примеры собранных данных:")
        for i, region_data in enumerate(data[:5]):  # Показываем первые 5
            if region_data['status'] == 'success' and region_data['fuel_prices']:
                prices = region_data['fuel_prices']
                prices_str = ", ".join([f"{fuel}: {price} руб." for fuel, price in prices.items()])
                logger.info(f"   {region_data['region_name']}: {prices_str}")
        
        # Сохранение результатов
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"regional_fuel_prices_{timestamp}.xlsx"
        
        logger.info(f"💾 Сохранение результатов в {filename}...")
        saved_file = parser.save_to_excel(data, filename)
        
        # Статистика
        stats = parser._create_statistics(data)
        logger.info("📈 ИТОГОВАЯ СТАТИСТИКА:")
        for key, value in stats.items():
            logger.info(f"   {key}: {value}")
        
        # Финальный отчет
        logger.success(f"🎉 Сбор данных завершен успешно!")
        logger.info(f"📁 Файл с результатами: {saved_file}")
        logger.info(f"🕐 Общее время работы: {duration}")
        
        return saved_file, stats
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при сборе данных: {e}")
        raise


def run_test_collection(region_ids: Optional[List[int]] = None):
    """Запуск тестового сбора для нескольких регионов"""
    logger.info("🧪 Запуск тестового сбора данных")
    
    # Регионы для тестирования
    if not region_ids:
        test_regions_ids = [77, 78, 40, 23, 16]  # Москва, СПб, Курск, Краснодар, Татарстан
    else:
        test_regions_ids = region_ids
    
    config = {"type": "russiabase_regional"}
    parser = RussiaBaseRegionalParser("test_regional", config)
    
    test_data = []
    
    for region_id in test_regions_ids:
        region = region_manager.get_region_by_id(region_id)
        if not region:
            logger.warning(f"⚠️ Регион с ID {region_id} не найден")
            continue
            
        region_name = region['name']
        logger.info(f"🔍 Тестируем регион: {region_name} (ID: {region_id})")
        
        try:
            region_data = parser._fetch_region_data(region_id, region_name)
            test_data.append(region_data)
            
            # Показываем результат сразу
            if region_data['status'] == 'success':
                fuel_prices = region_data.get('fuel_prices', {})
                if fuel_prices:
                    prices_str = ", ".join([f"{fuel}: {price}" for fuel, price in fuel_prices.items()])
                    logger.success(f"✅ {region_name}: {prices_str}")
                else:
                    logger.warning(f"⚠️ {region_name}: цены не найдены")
            else:
                error_msg = region_data.get('error', 'Unknown error')
                logger.error(f"❌ {region_name}: {error_msg}")
                
            # Пауза между запросами
            parser.add_delay()
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке {region_name}: {e}")
    
    # Создаем таблицу с результатами
    if test_data:
        df = parser.create_fuel_prices_table(test_data)
        
        print("\n" + "="*80)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТОВОГО СБОРА")
        print("="*80)
        print(df.to_string(index=False))
        print("="*80)
        
        # Сохраняем тестовые результаты
        test_filename = f"test_regional_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        parser.save_to_excel(test_data, test_filename)
        logger.info(f"💾 Тестовые результаты сохранены в: {test_filename}")
        
        return test_filename
    
    return None


def run_single_region(region_id: int):
    """Тестирование одного региона"""
    region = region_manager.get_region_by_id(region_id)
    if not region:
        logger.error(f"❌ Регион с ID {region_id} не найден")
        return None
        
    region_name = region['name']
    logger.info(f"🎯 Тестирование региона: {region_name} (ID: {region_id})")
    
    config = {"type": "russiabase_regional"}
    parser = RussiaBaseRegionalParser("single_test", config)
    
    try:
        region_data = parser._fetch_region_data(region_id, region_name)
        
        print(f"\n{'='*60}")
        print(f"🎯 ТЕСТ РЕГИОНА: {region_name.upper()}")
        print(f"{'='*60}")
        print(f"URL: {region_data['url']}")
        print(f"Статус: {region_data['status']}")
        
        if region_data['status'] == 'success':
            fuel_prices = region_data.get('fuel_prices', {})
            if fuel_prices:
                print("💰 Найденные цены на топливо:")
                for fuel_type, price in fuel_prices.items():
                    print(f"   {fuel_type}: {price} руб.")
            else:
                print("⚠️ Цены на топливо не найдены")
        else:
            print(f"❌ Ошибка: {region_data.get('error', 'Unknown error')}")
        
        print(f"{'='*60}")
        
        return region_data
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании региона {region_name}: {e}")
        return None


def main():
    """Главная функция с обработкой аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Сбор региональных цен на топливо с russiabase.ru",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python run_regional_parser.py --full                    # Полный сбор по всем регионам
  python run_regional_parser.py --test                    # Тестовый сбор (5 регионов)
  python run_regional_parser.py --region 77               # Тест одного региона (Москва)
  python run_regional_parser.py --test --regions 77 78 40 # Тест конкретных регионов
  python run_regional_parser.py --list-regions            # Показать список регионов
        """
    )
    
    parser.add_argument('--full', action='store_true', 
                       help='Полный сбор данных по всем регионам')
    parser.add_argument('--test', action='store_true', 
                       help='Тестовый сбор данных (несколько регионов)')
    parser.add_argument('--region', type=int, 
                       help='Тестирование одного региона по ID')
    parser.add_argument('--regions', type=int, nargs='+', 
                       help='Список ID регионов для тестирования')
    parser.add_argument('--list-regions', action='store_true', 
                       help='Показать список всех регионов')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Подробный вывод (DEBUG уровень)')
    
    args = parser.parse_args()
    
    # Настройка логирования
    setup_logging(args.verbose)
    
    try:
        if args.list_regions:
            # Показать список регионов
            regions = region_manager.get_all_regions()
            print(f"\n📋 СПИСОК РЕГИОНОВ ({len(regions)} шт.):")
            print("-" * 60)
            for region in regions:
                print(f"ID {region['id']:2d}: {region['name']}")
            print("-" * 60)
            
        elif args.region:
            # Тестирование одного региона
            run_single_region(args.region)
            
        elif args.test:
            # Тестовый сбор
            region_ids: Optional[List[int]] = args.regions if args.regions else None
            run_test_collection(region_ids)
            
        elif args.full:
            # Полный сбор
            logger.warning("⚠️ Запускается полный сбор данных по всем регионам!")
            logger.warning("⚠️ Это может занять 15-30 минут!")
            
            import time
            for i in range(5, 0, -1):
                print(f"Начинаем через {i}...", end="\r")
                time.sleep(1)
            print("Запуск!           ")
            
            run_full_collection()
            
        else:
            # Показать помощь, если не указаны аргументы
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("🛑 Работа прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()