#!/usr/bin/env python3
"""
Пример использования парсера цен АЗС
"""
import sys
from datetime import datetime
from loguru import logger

from src.orchestrator import GasStationOrchestrator
from src.utils import DataProcessor, DataValidator
from config import GAS_STATION_NETWORKS


def setup_logging():
    """Настройка логирования для примера"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}",
        level="INFO"
    )


def example_basic_parsing():
    """Пример базового парсинга"""
    logger.info("=== Пример 1: Базовый парсинг ===")
    
    # Создаем оркестратор для парсинга только Лукойл
    orchestrator = GasStationOrchestrator(
        networks=['lukoil'],
        parallel=False
    )
    
    # Запускаем парсинг
    results = orchestrator.run()
    
    if results:
        logger.info("Парсинг завершен успешно!")
        summary = orchestrator.get_summary()
        logger.info(f"Получено {summary['total_records']} записей")
    else:
        logger.error("Парсинг не дал результатов")


def example_parallel_parsing():
    """Пример параллельного парсинга"""
    logger.info("=== Пример 2: Параллельный парсинг ===")
    
    # Парсим несколько сетей параллельно
    orchestrator = GasStationOrchestrator(
        networks=['lukoil', 'bashneft'],  # Исключаем медленные сети для примера
        parallel=True,
        max_workers=2
    )
    
    start_time = datetime.now()
    results = orchestrator.run()
    end_time = datetime.now()
    
    if results:
        logger.info(f"Параллельный парсинг завершен за {end_time - start_time}")
        for network, df in results.items():
            network_name = GAS_STATION_NETWORKS[network]['name']
            logger.info(f"  {network_name}: {len(df)} записей")


def example_data_analysis():
    """Пример анализа данных"""
    logger.info("=== Пример 3: Анализ данных ===")
    
    # Загружаем последние данные
    df = DataProcessor.load_latest_data()
    
    if df is None:
        logger.warning("Нет данных для анализа. Сначала запустите парсинг.")
        return
    
    # Очищаем данные
    df_clean = DataProcessor.clean_data(df)
    
    # Получаем статистику
    stats = DataProcessor.get_price_statistics(df_clean)
    
    logger.info("Общая статистика:")
    logger.info(f"  Всего записей: {stats['total_records']}")
    logger.info(f"  Всего станций: {stats['total_stations']}")
    logger.info(f"  Всего сетей: {stats['total_networks']}")
    logger.info(f"  Всего городов: {stats['total_cities']}")
    
    # Статистика по топливу
    logger.info("\nСтатистика по топливу:")
    for fuel in stats['fuel_types'][:5]:  # Топ-5
        logger.info(f"  {fuel['fuel_type']}: {fuel['count']} записей, средняя цена {fuel['avg_price']:.2f}")
    
    # Сравнение сетей
    comparison = DataProcessor.compare_networks(df_clean, "АИ-95")
    logger.info("\nСравнение сетей по АИ-95:")
    for row in comparison.head(3).iter_rows(named=True):
        logger.info(f"  {row['network_name']}: {row['avg_price']:.2f} руб/ед. "
                   f"({row['stations_count']} станций)")


def example_cheapest_stations():
    """Пример поиска дешевых заправок"""
    logger.info("=== Пример 4: Поиск дешевых заправок ===")
    
    df = DataProcessor.load_latest_data()
    if df is None:
        logger.warning("Нет данных для анализа.")
        return
    
    df_clean = DataProcessor.clean_data(df)
    
    # Ищем самые дешевые заправки с АИ-95
    cheapest = DataProcessor.find_cheapest_stations(df_clean, "АИ-95", limit=5)
    
    logger.info("Топ-5 самых дешевых заправок АИ-95:")
    for row in cheapest.iter_rows(named=True):
        logger.info(f"  {row['network_name']} - {row['station_name']}")
        logger.info(f"    Адрес: {row['address']}")
        logger.info(f"    Цена: {row['price']:.2f} руб/ед.")
        logger.info("")


def example_data_validation():
    """Пример валидации качества данных"""
    logger.info("=== Пример 5: Валидация данных ===")
    
    df = DataProcessor.load_latest_data()
    if df is None:
        logger.warning("Нет данных для валидации.")
        return
    
    # Проверяем качество данных
    quality_report = DataValidator.validate_data_quality(df)
    
    logger.info(f"Отчет о качестве данных:")
    logger.info(f"  Всего записей: {quality_report['total_records']}")
    logger.info(f"  Оценка качества: {quality_report['quality_score']:.1f}%")
    
    if quality_report['issues']:
        logger.info("  Обнаруженные проблемы:")
        for issue in quality_report['issues']:
            logger.info(f"    {issue['type']}: {issue['count']} ({issue['percentage']:.1f}%)")
    else:
        logger.info("  Проблем не обнаружено!")


def example_export_report():
    """Пример создания отчета"""
    logger.info("=== Пример 6: Создание отчета ===")
    
    df = DataProcessor.load_latest_data()
    if df is None:
        logger.warning("Нет данных для отчета.")
        return
    
    df_clean = DataProcessor.clean_data(df)
    
    # Создаем сводный отчет
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"price_analysis_report_{timestamp}.xlsx"
    
    DataProcessor.export_summary_report(df_clean, report_file)
    logger.info(f"Отчет сохранен: {report_file}")


def example_custom_network_selection():
    """Пример выбора конкретных сетей"""
    logger.info("=== Пример 7: Выбор конкретных сетей ===")
    
    # Показываем доступные сети
    logger.info("Доступные сети:")
    for key, config in GAS_STATION_NETWORKS.items():
        logger.info(f"  {key}: {config['name']} ({config['type']})")
    
    # Парсим только быстрые сети (API)
    api_networks = [key for key, config in GAS_STATION_NETWORKS.items() 
                   if config['type'] == 'api']
    
    if api_networks:
        logger.info(f"\nПарсим только API сети: {api_networks}")
        orchestrator = GasStationOrchestrator(networks=api_networks)
        results = orchestrator.run()
        
        if results:
            logger.info("API парсинг завершен успешно!")


def main():
    """Главная функция с примерами"""
    setup_logging()
    
    logger.info("🚗 Примеры использования парсера цен АЗС")
    logger.info("="*50)
    
    examples = [
        ("Базовый парсинг", example_basic_parsing),
        ("Параллельный парсинг", example_parallel_parsing),
        ("Анализ данных", example_data_analysis),
        ("Поиск дешевых заправок", example_cheapest_stations),
        ("Валидация данных", example_data_validation),
        ("Создание отчета", example_export_report),
        ("Выбор сетей", example_custom_network_selection)
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        
    try:
        choice = input("\nВыберите пример для запуска (1-7, или 'all' для всех): ").strip()
        
        if choice.lower() == 'all':
            for name, func in examples:
                logger.info(f"\n--- Выполняем: {name} ---")
                try:
                    func()
                except Exception as e:
                    logger.error(f"Ошибка в примере '{name}': {e}")
        
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            idx = int(choice) - 1
            name, func = examples[idx]
            logger.info(f"\n--- Выполняем: {name} ---")
            func()
            
        else:
            logger.error("Неверный выбор")
            
    except KeyboardInterrupt:
        logger.warning("\nВыполнение прервано пользователем")
    except Exception as e:
        logger.error(f"Ошибка: {e}")


if __name__ == "__main__":
    main()