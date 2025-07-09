#!/usr/bin/env python3
"""
Региональный парсер цен на топливо
Использует интегрированную архитектуру проекта парсеров АЗС
Поддерживает историю региональных цен с организацией по датам
"""
import argparse
import sys
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

from src.orchestrator import GasStationOrchestrator
from src.parsers.russiabase_parser import RussiaBaseRegionalParser
from src.regional_history_manager import RegionalHistoryManager
from config import GAS_STATION_NETWORKS, REGIONS_CONFIG


def setup_logging():
    """Настройка логирования"""
    logger.remove()  # Удаляем стандартный обработчик
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}",
        level="INFO"
    )


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Региональный парсер цен на топливо",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python regional_parser.py --all-regions           # Парсить все регионы
  python regional_parser.py --popular-regions       # Парсить популярные регионы
  python regional_parser.py --regions 77 78 50      # Парсить конкретные регионы (Москва, СПб, МО)
  python regional_parser.py --max-regions 10        # Ограничить до 10 регионов
  python regional_parser.py --list-regions          # Показать доступные регионы
  python regional_parser.py --all-regions --disable-history  # Без сохранения в историю
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all-regions",
        action="store_true",
        help="Парсить все доступные регионы"
    )
    group.add_argument(
        "--popular-regions",
        action="store_true",
        help="Парсить популярные регионы (крупные города)"
    )
    group.add_argument(
        "--regions",
        nargs="+",
        type=int,
        help="Список ID регионов для парсинга"
    )
    group.add_argument(
        "--list-regions",
        action="store_true",
        help="Показать список доступных регионов"
    )
    
    parser.add_argument(
        "--max-regions",
        type=int,
        help="Максимальное количество регионов для парсинга"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Задержка между запросами в секундах (по умолчанию 1.5)"
    )
    
    parser.add_argument(
        "--use-orchestrator",
        action="store_true",
        help="Использовать общий оркестратор (интегрированный режим)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробное логирование"
    )
    
    parser.add_argument(
        "--enable-history",
        action="store_true",
        default=True,
        help="Сохранять данные в систему истории (по умолчанию включено)"
    )
    
    parser.add_argument(
        "--disable-history",
        action="store_true",
        help="Отключить сохранение в систему истории"
    )
    
    return parser.parse_args()


def list_available_regions():
    """Выводит список доступных регионов"""
    print("\n[INFO] Получение списка доступных регионов...")
    print("=" * 60)
    
    try:
        parser = RussiaBaseRegionalParser()
        regions = parser.get_all_regions()
        
        if regions:
            print(f"Всего доступно регионов: {len(regions)}")
            print("\nСписок регионов:")
            print("-" * 60)
            
            # Группируем регионы для лучшего отображения
            popular_ids = REGIONS_CONFIG.get('default_regions', [77, 78, 50, 40, 23, 66, 96])
            
            print("[POPULAR] Популярные регионы:")
            for region_id, region_name in sorted(regions.items()):
                if region_id in popular_ids:
                    print(f"  {region_id:3d}: {region_name} [*]")
            
            print("\n[ALL] Все остальные регионы:")
            for region_id, region_name in sorted(regions.items()):
                if region_id not in popular_ids:
                    logger.info(f"  {region_id:3d}: {region_name}")
            
        else:
            logger.error("Не удалось получить список регионов")
            
    except Exception as e:
        logger.error(f"Ошибка при получении списка регионов: {e}")


def run_regional_parsing_standalone(args):
    """Запуск парсинга в standalone режиме"""
    logger.info("[RUN] Запуск регионального парсинга (standalone режим)")
    
    # Создаем конфигурацию
    config = {
        'type': 'russiabase_regional',
        'base_url': 'https://russiabase.ru/prices',
        'delay': args.delay,
        'max_regions': args.max_regions
    }
    
    parser = RussiaBaseRegionalParser("regional_prices", config)
    
    # Определяем регионы для парсинга
    regions_to_parse = []
    
    if args.all_regions:
        all_regions = parser.get_all_regions()
        regions_to_parse = [
            {'id': region_id, 'name': region_name}
            for region_id, region_name in all_regions.items()
        ]
        logger.info(f"Режим: все регионы ({len(regions_to_parse)} регионов)")
        
    elif args.popular_regions:
        all_regions = parser.get_all_regions()
        popular_ids = REGIONS_CONFIG.get('default_regions', [77, 78, 50, 40, 23, 66, 96])
        regions_to_parse = [
            {'id': region_id, 'name': all_regions[region_id]}
            for region_id in popular_ids
            if region_id in all_regions
        ]
        logger.info(f"Режим: популярные регионы ({len(regions_to_parse)} регионов)")
        
    elif args.regions:
        all_regions = parser.get_all_regions()
        regions_to_parse = [
            {'id': region_id, 'name': all_regions.get(region_id, f'Регион {region_id}')}
            for region_id in args.regions
            if region_id in all_regions
        ]
        logger.info(f"Режим: выбранные регионы ({len(regions_to_parse)} регионов)")
    
    if not regions_to_parse:
        logger.error("Нет регионов для парсинга")
        return False
    
    # Ограничиваем количество регионов если задано
    if args.max_regions and len(regions_to_parse) > args.max_regions:
        regions_to_parse = regions_to_parse[:args.max_regions]
        logger.info(f"Ограничиваем до {args.max_regions} регионов")
    
    # Запускаем парсинг
    start_time = datetime.now()
    results = parser.parse_multiple_regions(regions_to_parse)
    end_time = datetime.now()
    
    # Выводим результаты
    log_regional_results(results, end_time - start_time)
    
    # Сохраняем в файлы
    save_regional_data(results, enable_history=not args.disable_history)
    
    return len(results) > 0


def run_regional_parsing_orchestrated(args):
    """Запуск парсинга через оркестратор"""
    logger.info("[RUN] Запуск регионального парсинга (интегрированный режим)")
    
    # Обновляем конфигурацию регионального парсера
    regional_config = GAS_STATION_NETWORKS["regional_prices"].copy()
    regional_config['delay'] = args.delay
    regional_config['max_regions'] = args.max_regions
    
    # Создаем оркестратор только для регионального парсера
    orchestrator = GasStationOrchestrator(
        networks=["regional_prices"],
        parallel=False,
        max_workers=1
    )
    
    start_time = datetime.now()
    results = orchestrator.run()
    end_time = datetime.now()
    
    if results:
        summary = orchestrator.get_summary()
        log_orchestrator_summary(summary, end_time - start_time)
        return True
    else:
        logger.error("Парсинг не дал результатов")
        return False


def log_regional_results(results, duration):
    """Логирует результаты регионального парсинга"""
    logger.info("=" * 80)
    logger.info("РЕЗУЛЬТАТЫ РЕГИОНАЛЬНОГО ПАРСИНГА")
    logger.info("=" * 80)
    
    if not results:
        logger.error("Нет результатов")
        return
    
    logger.info(f"Время выполнения: {duration}")
    logger.info(f"Успешно обработано регионов: {len(results)}")
    
    # Группируем цены по типам топлива
    fuel_stats = {}
    successful_regions = []
    
    for result in results:
        if result.status == 'success' and result.fuel_prices:
            successful_regions.append(result)
            for fuel_type, price in result.fuel_prices.items():
                if fuel_type != 'АИ-80':
                    if fuel_type not in fuel_stats:
                        fuel_stats[fuel_type] = []
                    fuel_stats[fuel_type].append(price)
    
    if fuel_stats:
        logger.info("Средние цены по России:")
        for fuel_type, prices in fuel_stats.items():
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            unit = "руб/м³" if fuel_type == "Газ" else "руб/кг" if fuel_type == "Пропан" else "руб/л"
            logger.info(f"  {fuel_type:10}: ср. {avg_price:.2f}, мин. {min_price:.2f}, макс. {max_price:.2f} {unit}")
    
    logger.info(f"Топ-10 регионов по ценам:")
    for i, result in enumerate(successful_regions[:10], 1):
        ai95 = result.fuel_prices.get("АИ-95", 0)
        dt = result.fuel_prices.get("ДТ", 0)
        price_info = f"{result.region_name}"
        if ai95 > 0:
            price_info += f" | АИ-95: {ai95:.2f}"
        if dt > 0:
            price_info += f" | ДТ: {dt:.2f}"
        logger.info(f"  {i}. {price_info}")
    
    if len(successful_regions) > 10:
        logger.info(f"... и еще {len(successful_regions) - 10} регионов")


def print_regional_results(results, duration):
    """Выводит результаты регионального парсинга"""
    print("\n" + "=" * 80)
    print("[STATS] РЕЗУЛЬТАТЫ РЕГИОНАЛЬНОГО ПАРСИНГА")
    print("=" * 80)
    
    if not results:
        print("[ERROR] Нет результатов")
        return
    
    print(f"[TIME] Время выполнения: {duration}")
    print(f"[STATS] Успешно обработано регионов: {len(results)}")
    
    # Группируем цены по типам топлива
    fuel_stats = {}
    successful_regions = []
    
    for result in results:
        if result.status == 'success' and result.fuel_prices:
            successful_regions.append(result)
            for fuel_type, price in result.fuel_prices.items():
                # Исключаем АИ-80 из статистики
                if fuel_type != 'АИ-80':
                    if fuel_type not in fuel_stats:
                        fuel_stats[fuel_type] = []
                    fuel_stats[fuel_type].append(price)
    
    if fuel_stats:
        print(f"[PRICE] Средние цены по России:")
        for fuel_type, prices in fuel_stats.items():
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            # Определяем правильные единицы измерения
            if fuel_type == "Газ":
                unit = "руб/м³"
            elif fuel_type == "Пропан":
                unit = "руб/кг"
            else:
                unit = "руб/л"
            print(f"  {fuel_type:10}: ср. {avg_price:.2f}, мин. {min_price:.2f}, макс. {max_price:.2f} {unit}")
    
    print(f"\n[TABLE] Топ-10 регионов по ценам:")
    print("-" * 130)
    print(f"{'Регион':<25} {'АИ-92':<7} {'АИ-92+':<7} {'АИ-95':<7} {'АИ-95+':<7} {'АИ-98':<7} {'АИ-98+':<7} {'АИ-100':<8} {'ДТ':<7} {'ДТ+':<7} {'Газ':<7} {'Пропан':<7}")
    print("-" * 130)
    
    # Показываем первые 10 успешных регионов
    for i, result in enumerate(successful_regions[:10], 1):
        region_name = result.region_name[:24]
        prices = result.fuel_prices
        
        ai92 = f"{prices.get('АИ-92', 0):.1f}" if prices.get('АИ-92') else "-"
        ai92_plus = f"{prices.get('АИ-92+', 0):.1f}" if prices.get('АИ-92+') else "-"
        ai95 = f"{prices.get('АИ-95', 0):.1f}" if prices.get('АИ-95') else "-"
        ai95_plus = f"{prices.get('АИ-95+', 0):.1f}" if prices.get('АИ-95+') else "-"
        ai98 = f"{prices.get('АИ-98', 0):.1f}" if prices.get('АИ-98') else "-"
        ai98_plus = f"{prices.get('АИ-98+', 0):.1f}" if prices.get('АИ-98+') else "-"
        ai100 = f"{prices.get('АИ-100', 0):.1f}" if prices.get('АИ-100') else "-"
        dt = f"{prices.get('ДТ', 0):.1f}" if prices.get('ДТ') else "-"
        dt_plus = f"{prices.get('ДТ+', 0):.1f}" if prices.get('ДТ+') else "-"
        gas = f"{prices.get('Газ', 0):.1f}" if prices.get('Газ') else "-"
        propan = f"{prices.get('Пропан', 0):.1f}" if prices.get('Пропан') else "-"
        
        print(f"{region_name:<25} {ai92:<7} {ai92_plus:<7} {ai95:<7} {ai95_plus:<7} {ai98:<7} {ai98_plus:<7} {ai100:<8} {dt:<7} {dt_plus:<7} {gas:<7} {propan:<7}")
    
    if len(successful_regions) > 10:
        print(f"... и еще {len(successful_regions) - 10} регионов")
    
    print("-" * 130)


def log_orchestrator_summary(summary, duration):
    """Логирует сводку оркестратора"""
    logger.info("=" * 80)
    logger.info("СВОДКА РЕГИОНАЛЬНОГО ПАРСИНГА (ОРКЕСТРАТОР)")
    logger.info("=" * 80)
    logger.info(f"Время выполнения: {duration}")
    logger.info(f"Общее количество записей: {summary['total_records']}")
    logger.info(f"Успешно обработано: {summary['networks_parsed']}")
    logger.info(f"Ошибок: {summary['networks_failed']}")
    
    if 'regional_prices' in summary['networks_summary']:
        net_summary = summary['networks_summary']['regional_prices']
        logger.info(f"Регионов: {net_summary['cities']}")
        logger.info(f"Типов топлива: {net_summary['fuel_types']}")
        logger.info(f"Средняя цена: {net_summary['avg_price']:.2f} руб/ед.")
    
    if summary['errors']:
        logger.warning("Ошибки:")
        for network, error in summary['errors'].items():
            logger.warning(f"  {network}: {error}")


def print_orchestrator_summary(summary, duration):
    """Выводит сводку от оркестратора"""
    print("\n" + "=" * 80)
    print("[STATS] СВОДКА РЕГИОНАЛЬНОГО ПАРСИНГА (ОРКЕСТРАТОР)")
    print("=" * 80)
    print(f"[TIME] Время выполнения: {duration}")
    print(f"[LOG] Общее количество записей: {summary['total_records']}")
    print(f"[OK] Успешно обработано: {summary['networks_parsed']}")
    print(f"[ERROR] Ошибок: {summary['networks_failed']}")
    
    if 'regional_prices' in summary['networks_summary']:
        net_summary = summary['networks_summary']['regional_prices']
        print(f"[LOC] Регионов: {net_summary['cities']}")
        print(f"[FUEL] Типов топлива: {net_summary['fuel_types']}")
        print(f"[PRICE] Средняя цена: {net_summary['avg_price']:.2f} руб/ед.")
    
    if summary['errors']:
        print(f"\n[WARNING] Ошибки:")
        for network, error in summary['errors'].items():
            print(f"  {network}: {error}")


def save_regional_excel_report(results, filename):
    """Создает детальный Excel отчет с региональными ценами"""
    import pandas as pd
    
    try:
        # Подготавливаем данные для разных листов
        
        # 1. Основная таблица с ценами по регионам
        main_data = []
        for result in results:
            if result.status == 'success' and result.fuel_prices:
                base_row = {
                    'region_id': result.region_id,
                    'region_name': result.region_name,
                    'timestamp': result.timestamp,
                    'url': result.url,
                    'status': result.status
                }
                
                # Добавляем цены по типам топлива как отдельные колонки (исключая АИ-80)
                for fuel_type, price in result.fuel_prices.items():
                    if fuel_type != 'АИ-80':
                        base_row[f'{fuel_type}'] = price
                
                main_data.append(base_row)
        
        # 2. Сводная статистика по типам топлива
        fuel_stats = {}
        for result in results:
            if result.status == 'success' and result.fuel_prices:
                for fuel_type, price in result.fuel_prices.items():
                    # Исключаем АИ-80 из статистики Excel
                    if fuel_type != 'АИ-80':
                        if fuel_type not in fuel_stats:
                            fuel_stats[fuel_type] = []
                        fuel_stats[fuel_type].append(price)
        
        # Статистика по топливу
        fuel_summary = []
        for fuel_type, prices in fuel_stats.items():
            if prices:
                fuel_summary.append({
                    'Тип топлива': fuel_type,
                    'Регионов с данными': len(prices),
                    'Средняя цена': round(sum(prices) / len(prices), 2),
                    'Минимальная цена': round(min(prices), 2),
                    'Максимальная цена': round(max(prices), 2),
                    'Разброс цен': round(max(prices) - min(prices), 2)
                })
        
        # 3. Топ самых дорогих и дешевых регионов
        successful_results = [r for r in results if r.status == 'success' and r.fuel_prices]
        
        # Создаем Excel файл с несколькими листами
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            
            # Лист 1: Основные данные
            if main_data:
                main_df = pd.DataFrame(main_data)
                main_df.to_excel(writer, sheet_name='Цены по регионам', index=False)
            
            # Лист 2: Сводная статистика
            if fuel_summary:
                summary_df = pd.DataFrame(fuel_summary)
                summary_df.to_excel(writer, sheet_name='Статистика по топливу', index=False)
            
            # Лист 3: Общая информация
            info_data = [
                ['Дата и время парсинга', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Всего регионов обработано', len(results)],
                ['Успешно получены данные', len(successful_results)],
                ['Регионов с ошибками', len(results) - len(successful_results)],
                ['Типов топлива найдено', len(fuel_stats)]
            ]
            
            info_df = pd.DataFrame(info_data, columns=['Параметр', 'Значение'])
            info_df.to_excel(writer, sheet_name='Общая информация', index=False)
            
            # Настройка ширины колонок для всех листов
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                # Устанавливаем ширину колонок
                for i, col in enumerate(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']):
                    if sheet_name == 'Цены по регионам':
                        if i == 1:  # Колонка с названием региона
                            worksheet.set_column(f'{col}:{col}', 30)
                        elif i > 4:  # Колонки с ценами
                            worksheet.set_column(f'{col}:{col}', 12)
                        else:
                            worksheet.set_column(f'{col}:{col}', 15)
                    else:
                        worksheet.set_column(f'{col}:{col}', 20)
    
    except Exception as e:
        logger.error(f"Ошибка создания Excel отчета: {e}")
        # Если не удалось создать Excel, создаем простую версию
        try:
            simple_data = []
            for result in results:
                if result.status == 'success':
                    row = {
                        'Регион ID': result.region_id,
                        'Название региона': result.region_name,
                        'Статус': result.status,
                        'Дата': result.timestamp
                    }
                    if result.fuel_prices:
                        for fuel_type, price in result.fuel_prices.items():
                            # Исключаем АИ-80 из простого Excel
                            if fuel_type != 'АИ-80':
                                row[fuel_type] = price
                    simple_data.append(row)
            
            if simple_data:
                simple_df = pd.DataFrame(simple_data)
                simple_df.to_excel(filename, index=False)
        except Exception as e2:
            logger.error(f"Не удалось создать даже простой Excel файл: {e2}")


def save_regional_csv_report(results, filename):
    """Создает CSV отчет с региональными ценами"""
    import pandas as pd
    
    try:
        # Подготавливаем данные для CSV
        csv_data = []
        for result in results:
            if result.status == 'success' and result.fuel_prices:
                base_row = {
                    'region_id': result.region_id,
                    'region_name': result.region_name,
                    'timestamp': result.timestamp,
                    'url': result.url,
                    'status': result.status
                }
                
                # Добавляем цены по типам топлива как отдельные колонки (исключая АИ-80)
                for fuel_type, price in result.fuel_prices.items():
                    if fuel_type != 'АИ-80':
                        base_row[f'{fuel_type}'] = price
                
                csv_data.append(base_row)
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            # Сортируем колонки для лучшего отображения
            cols = ['region_id', 'region_name', 'timestamp', 'url', 'status']
            fuel_cols = [col for col in df.columns if col not in cols]
            fuel_cols.sort()  # Сортируем типы топлива по алфавиту
            df = df[cols + fuel_cols]
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"[FILE] Данные сохранены в CSV: {filename}")
        else:
            logger.warning("Нет данных для сохранения в CSV")
            
    except Exception as e:
        logger.error(f"Ошибка создания CSV отчета: {e}")


def save_regional_data(results, enable_history: bool = True):
    """Сохраняет данные в файлы (JSON, Excel и CSV) с правильным неймингом по полноте выгрузки.
    Использует систему именования по аналогии с АЗС.
    
    Args:
        results: Результаты парсинга региональных цен
        enable_history: Если True, сохраняет данные в систему истории
    """
    if not results:
        return
    
    # Сохранение в систему истории (новый способ)
    if enable_history:
        try:
            history_manager = RegionalHistoryManager()
            history_result = history_manager.save_regional_data_with_history(results)
            
            logger.info(f"[HISTORY] ✅ Данные сохранены в систему истории")
            logger.info(f"[HISTORY] 📁 Папка: {history_result.get('history_json', 'N/A')}")
            if 'metadata' in history_result:
                completeness = history_result['metadata'].get('completeness', 'UNKNOWN')
                regions_count = history_result['metadata'].get('successful_regions', 0)
                logger.info(f"[HISTORY] 📊 Полнота: {completeness} ({regions_count} регионов)")
            
        except Exception as e:
            logger.error(f"[HISTORY] ❌ Ошибка сохранения в историю: {e}")
            logger.info(f"[HISTORY] 📝 Продолжаем с обычным сохранением...")
    
    # Сохранение в корневую папку (старый способ для совместимости)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Определяем полноту выгрузки
    successful_count = len([r for r in results if r.status == 'success'])
    total_expected_regions = 85  # Примерное количество всех регионов России
    
    # Система нейминга по аналогии с АЗС (полная выгрузка vs частичная)
    if successful_count >= 80:  # 95%+ регионов - это полная выгрузка
        # Полная выгрузка всех регионов (по аналогии с all_gas_stations_)
        prefix = f"all_regions"
        file_type = "ПОЛНАЯ"
    elif successful_count >= 60:  # 70%+ регионов - большая выгрузка
        # Крупная выгрузка с указанием количества регионов
        prefix = f"regions_{successful_count}of{total_expected_regions}"
        file_type = "КРУПНАЯ"
    else:  # Частичная выгрузка
        # Частичная выгрузка с указанием количества регионов
        prefix = f"regions_partial_{successful_count}reg"
        file_type = "ЧАСТИЧНАЯ"
    
    # Сохраняем в JSON (корневая папка для совместимости)
    json_filename = f"{prefix}_{timestamp}.json"
    
    json_data = []
    for result in results:
        json_data.append({
            'region_id': result.region_id,
            'region_name': result.region_name,
            'fuel_prices': result.fuel_prices,
            'url': result.url,
            'timestamp': result.timestamp,
            'status': result.status
        })
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[SAVE] Данные сохранены в JSON: {json_filename}")
    logger.info(f"[NAMING] Тип выгрузки: {file_type} ({successful_count} из ~{total_expected_regions} регионов)")
    
    # Важная информация для пользователя
    if successful_count >= 80:
        logger.info(f"[VISUALIZATION] ✅ Файл подходит для создания карт (полная выгрузка)")
    else:
        logger.warning(f"[VISUALIZATION] ⚠️  Файл НЕ подходит для карт - нужна полная выгрузка (>=80 регионов)")
        logger.warning(f"[RECOMMEND] Запустите: python regional_parser.py --all-regions")
    
    # Сохраняем в Excel с тем же префиксом
    excel_filename = f"{prefix}_{timestamp}.xlsx"
    save_regional_excel_report(results, excel_filename)
    logger.info(f"[SAVE] Данные сохранены в Excel: {excel_filename}")
    
    # Сохраняем в CSV с тем же префиксом  
    csv_filename = f"{prefix}_{timestamp}.csv"
    save_regional_csv_report(results, csv_filename)
    logger.info(f"[SAVE] Данные сохранены в CSV: {csv_filename}")
    



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
    
    logger.info("=== Региональный парсер цен на топливо ===")
    logger.info("=" * 60)
    
    # Показать список регионов
    if args.list_regions:
        list_available_regions()
        return
    
    try:
        # Выбираем режим работы
        if args.use_orchestrator:
            success = run_regional_parsing_orchestrated(args)
        else:
            success = run_regional_parsing_standalone(args)
        
        if success:
            logger.success(f"Парсинг завершен успешно: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("Результаты сохранены в текущей директории")
            if not args.disable_history:
                logger.info("Данные также сохранены в систему истории: data/regional_history/")
                logger.info("Для анализа истории используйте: python src/history_utils.py --help")
        else:
            logger.error("Парсинг завершился с ошибками")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\n[WARNING] Парсинг прерван пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n[CRASH] Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()