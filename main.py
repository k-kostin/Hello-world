#!/usr/bin/env python3
"""
Главный модуль для запуска парсинга цен АЗС
"""
import argparse
import sys
from datetime import datetime
from loguru import logger

from src.orchestrator import GasStationOrchestrator
from config import GAS_STATION_NETWORKS


def setup_logging():
    """Настройка базового логирования"""
    logger.remove()  # Удаляем стандартный обработчик
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}",
        level="INFO"
    )


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Парсер цен сетей АЗС",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py --all                    # Парсить все сети
  python main.py --networks lukoil gazprom    # Парсить только Лукойл и Газпром
  python main.py --networks bashneft --parallel   # Параллельный парсинг Башнефти
  python main.py --list                   # Показать доступные сети
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Парсить все доступные сети АЗС"
    )
    group.add_argument(
        "--networks",
        nargs="+",
        choices=list(GAS_STATION_NETWORKS.keys()),
        help="Список сетей для парсинга"
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="Показать список доступных сетей"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Запустить парсеры параллельно (по умолчанию последовательно)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Количество параллельных воркеров (по умолчанию 3)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробное логирование"
    )
    
    return parser.parse_args()


def list_networks():
    """Выводит список доступных сетей"""
    print("\nДоступные сети АЗС:")
    print("=" * 70)
    
    for key, config in GAS_STATION_NETWORKS.items():
        network_type = config['type']
        type_info = ""
        
        if network_type == 'russiabase':
            type_info = f"Страниц: {config.get('max_pages', 1)}"
        elif network_type == 'russiabase_regional':
            type_info = f"Региональный парсер (все регионы России)"
        elif network_type == 'api':
            type_info = f"API: {config.get('api_base', 'N/A')}"
        elif network_type == 'selenium':
            type_info = f"Selenium WebDriver"
        elif network_type == 'tatneft_api':
            type_info = f"Татнефть API"
        
        print(f"  {key:18} - {config['name']:25} ({network_type})")
        if type_info:
            print(f"{'':22}   {type_info}")
    
    print(f"\nВсего доступно сетей: {len(GAS_STATION_NETWORKS)}")
    print("\n💡 Для региональных цен используйте: python main.py --networks regional_prices")
    print("💡 Или используйте специальный скрипт: python regional_parser_final.py --help")


def main():
    """Главная функция"""
    args = parse_arguments()
    
    # Настройка логирования
    setup_logging()
    if args.verbose:
        logger.remove()
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}",
            level="DEBUG"
        )
    
    # Показать список сетей
    if args.list:
        list_networks()
        return
    
    # Определяем сети для парсинга
    if args.all:
        networks = list(GAS_STATION_NETWORKS.keys())
        logger.info("Запуск парсинга всех доступных сетей")
    else:
        networks = args.networks
        logger.info(f"Запуск парсинга выбранных сетей: {', '.join(networks)}")
    
    # Информация о режиме работы
    mode = "параллельном" if args.parallel else "последовательном"
    logger.info(f"Режим выполнения: {mode}")
    if args.parallel:
        logger.info(f"Количество воркеров: {args.workers}")
    
    try:
        # Создаем и запускаем оркестратор
        orchestrator = GasStationOrchestrator(
            networks=networks,
            parallel=args.parallel,
            max_workers=args.workers
        )
        
        start_time = datetime.now()
        results = orchestrator.run()
        end_time = datetime.now()
        
        # Выводим итоговую статистику
        if results:
            summary = orchestrator.get_summary()
            
            print("\n" + "=" * 60)
            print("СВОДКА ПО РЕЗУЛЬТАТАМ ПАРСИНГА")
            print("=" * 60)
            print(f"Время выполнения: {end_time - start_time}")
            print(f"Общее количество записей: {summary['total_records']}")
            print(f"Успешно обработано сетей: {summary['networks_parsed']}")
            print(f"Сетей с ошибками: {summary['networks_failed']}")
            
            print("\nПо сетям:")
            for network, stats in summary['networks_summary'].items():
                network_name = GAS_STATION_NETWORKS[network]['name']
                print(f"  {network_name:20}: {stats['records']:4} записей, "
                      f"{stats['stations']:3} станций, "
                      f"{stats['cities']:2} городов, "
                      f"ср. цена: {stats['avg_price']:.2f}")
            
            if summary['errors']:
                print(f"\nОшибки:")
                for network, error in summary['errors'].items():
                    print(f"  {network}: {error}")
            
            print(f"\nРезультаты сохранены в директории: data/")
            
        else:
            logger.error("Парсинг не дал результатов")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Парсинг прерван пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()