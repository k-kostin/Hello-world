#!/usr/bin/env python3
"""
Финальный региональный парсер цен на топливо
Использует интегрированную архитектуру проекта парсеров АЗС
"""
import argparse
import sys
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

from src.orchestrator import GasStationOrchestrator
from src.parsers.russiabase_parser import RussiaBaseRegionalParser
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
        description="Финальный региональный парсер цен на топливо",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python regional_parser_final.py --all-regions           # Парсить все регионы
  python regional_parser_final.py --popular-regions       # Парсить популярные регионы
  python regional_parser_final.py --regions 77 78 50      # Парсить конкретные регионы (Москва, СПб, МО)
  python regional_parser_final.py --max-regions 10        # Ограничить до 10 регионов
  python regional_parser_final.py --list-regions          # Показать доступные регионы
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
    
    return parser.parse_args()


def list_available_regions():
    """Выводит список доступных регионов"""
    print("\n🗺️  Получение списка доступных регионов...")
    print("=" * 60)
    
    try:
        parser = RussiaBaseRegionalParser()
        regions = parser.get_all_regions()
        
        if regions:
            print(f"Всего доступно регионов: {len(regions)}")
            print("\nСписок регионов:")
            print("-" * 60)
            
            # Группируем регионы для лучшего отображения
            popular_ids = REGIONS_CONFIG.get('default_regions', [77, 78, 50, 40, 23, 66])
            
            print("📍 Популярные регионы:")
            for region_id, region_name in sorted(regions.items()):
                if region_id in popular_ids:
                    print(f"  {region_id:3d}: {region_name} ⭐")
            
            print("\n📍 Все остальные регионы:")
            for region_id, region_name in sorted(regions.items()):
                if region_id not in popular_ids:
                    print(f"  {region_id:3d}: {region_name}")
            
        else:
            print("❌ Не удалось получить список регионов")
            
    except Exception as e:
        logger.error(f"Ошибка при получении списка регионов: {e}")


def run_regional_parsing_standalone(args):
    """Запуск парсинга в standalone режиме"""
    logger.info("🚀 Запуск регионального парсинга (standalone режим)")
    
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
        popular_ids = REGIONS_CONFIG.get('default_regions', [77, 78, 50, 40, 23, 66])
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
    print_regional_results(results, end_time - start_time)
    
    # Сохраняем в файлы
    save_regional_data(results)
    
    return len(results) > 0


def run_regional_parsing_orchestrated(args):
    """Запуск парсинга через оркестратор"""
    logger.info("🚀 Запуск регионального парсинга (интегрированный режим)")
    
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
        print_orchestrator_summary(summary, end_time - start_time)
        return True
    else:
        logger.error("Парсинг не дал результатов")
        return False


def print_regional_results(results, duration):
    """Выводит результаты регионального парсинга"""
    print("\n" + "=" * 80)
    print("📊 РЕЗУЛЬТАТЫ РЕГИОНАЛЬНОГО ПАРСИНГА")
    print("=" * 80)
    
    if not results:
        print("❌ Нет результатов")
        return
    
    print(f"⏱️  Время выполнения: {duration}")
    print(f"🗺️  Успешно обработано регионов: {len(results)}")
    
    # Группируем цены по типам топлива
    fuel_stats = {}
    successful_regions = []
    
    for result in results:
        if result.status == 'success' and result.fuel_prices:
            successful_regions.append(result)
            for fuel_type, price in result.fuel_prices.items():
                if fuel_type not in fuel_stats:
                    fuel_stats[fuel_type] = []
                fuel_stats[fuel_type].append(price)
    
    if fuel_stats:
        print(f"💰 Средние цены по России:")
        for fuel_type, prices in fuel_stats.items():
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            print(f"  {fuel_type:10}: ср. {avg_price:.2f}, мин. {min_price:.2f}, макс. {max_price:.2f} руб/л")
    
    print(f"\n📋 Топ-10 регионов по ценам:")
    print("-" * 80)
    print(f"{'Регион':<30} {'АИ-92':<8} {'АИ-95':<8} {'АИ-98':<8} {'ДТ':<8} {'Пропан':<8}")
    print("-" * 80)
    
    # Показываем первые 10 успешных регионов
    for i, result in enumerate(successful_regions[:10], 1):
        region_name = result.region_name[:29]
        prices = result.fuel_prices
        
        ai92 = f"{prices.get('АИ-92', 0):.1f}" if prices.get('АИ-92') else "-"
        ai95 = f"{prices.get('АИ-95', 0):.1f}" if prices.get('АИ-95') else "-"
        ai98 = f"{prices.get('АИ-98', 0):.1f}" if prices.get('АИ-98') else "-"
        dt = f"{prices.get('ДТ', 0):.1f}" if prices.get('ДТ') else "-"
        propan = f"{prices.get('Пропан', 0):.1f}" if prices.get('Пропан') else "-"
        
        print(f"{region_name:<30} {ai92:<8} {ai95:<8} {ai98:<8} {dt:<8} {propan:<8}")
    
    if len(successful_regions) > 10:
        print(f"... и еще {len(successful_regions) - 10} регионов")
    
    print("-" * 80)


def print_orchestrator_summary(summary, duration):
    """Выводит сводку от оркестратора"""
    print("\n" + "=" * 80)
    print("📊 СВОДКА РЕГИОНАЛЬНОГО ПАРСИНГА (ОРКЕСТРАТОР)")
    print("=" * 80)
    print(f"⏱️  Время выполнения: {duration}")
    print(f"📝 Общее количество записей: {summary['total_records']}")
    print(f"✅ Успешно обработано: {summary['networks_parsed']}")
    print(f"❌ Ошибок: {summary['networks_failed']}")
    
    if 'regional_prices' in summary['networks_summary']:
        net_summary = summary['networks_summary']['regional_prices']
        print(f"🗺️  Регионов: {net_summary['cities']}")
        print(f"⛽ Типов топлива: {net_summary['fuel_types']}")
        print(f"💰 Средняя цена: {net_summary['avg_price']:.2f} руб/л")
    
    if summary['errors']:
        print(f"\n⚠️  Ошибки:")
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
                
                # Добавляем цены по типам топлива как отдельные колонки
                for fuel_type, price in result.fuel_prices.items():
                    base_row[f'{fuel_type}'] = price
                
                main_data.append(base_row)
        
        # 2. Сводная статистика по типам топлива
        fuel_stats = {}
        for result in results:
            if result.status == 'success' and result.fuel_prices:
                for fuel_type, price in result.fuel_prices.items():
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
            
            # Лист 3: Самые дорогие регионы (по АИ-95 если есть)
            if successful_results:
                ai95_regions = [(r.region_name, r.fuel_prices.get('АИ-95', 0)) 
                               for r in successful_results 
                               if r.fuel_prices.get('АИ-95', 0) > 0]
                
                if ai95_regions:
                    ai95_sorted = sorted(ai95_regions, key=lambda x: x[1], reverse=True)
                    expensive_df = pd.DataFrame(ai95_sorted[:10], columns=['Регион', 'Цена АИ-95'])
                    expensive_df.to_excel(writer, sheet_name='Дорогие регионы АИ-95', index=False)
                    
                    # Лист 4: Самые дешевые регионы
                    cheap_df = pd.DataFrame(ai95_sorted[-10:], columns=['Регион', 'Цена АИ-95'])
                    cheap_df.to_excel(writer, sheet_name='Дешевые регионы АИ-95', index=False)
            
            # Лист 5: Общая информация
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
                            row[fuel_type] = price
                    simple_data.append(row)
            
            if simple_data:
                simple_df = pd.DataFrame(simple_data)
                simple_df.to_excel(filename, index=False)
        except Exception as e2:
            logger.error(f"Не удалось создать даже простой Excel файл: {e2}")


def save_regional_data(results):
    """Сохраняет данные в файлы (JSON и Excel)"""
    if not results:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Сохраняем в JSON
    json_filename = f"regional_prices_{timestamp}.json"
    
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
    
    logger.info(f"💾 Данные сохранены в JSON: {json_filename}")
    
    # Сохраняем в Excel
    excel_filename = f"regional_prices_{timestamp}.xlsx"
    save_regional_excel_report(results, excel_filename)
    
    logger.info(f"📊 Данные сохранены в Excel: {excel_filename}")


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
    
    print("🏁 Финальный региональный парсер цен на топливо")
    print("=" * 60)
    
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
            print(f"\n✅ Парсинг завершен успешно: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("📂 Результаты сохранены в текущей директории")
        else:
            print("\n❌ Парсинг завершился с ошибками")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Парсинг прерван пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()