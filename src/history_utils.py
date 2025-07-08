#!/usr/bin/env python3
"""
Утилиты для работы с историей региональных цен
Анализ, сравнение и поиск по историческим данным
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import argparse
import sys


class RegionalHistoryAnalyzer:
    """Анализатор истории региональных цен"""
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = Path(base_data_dir)
        self.history_dir = self.base_data_dir / "regional_history"
        self.metadata_file = self.history_dir / "history_index.json"
    
    def compare_dates(self, date1: date, date2: date, fuel_type: Optional[str] = None) -> Dict[str, Any]:
        """Сравнивает цены между двумя датами"""
        try:
            # Получаем данные за обе даты
            data1 = self._load_latest_data_for_date(date1)
            data2 = self._load_latest_data_for_date(date2)
            
            if not data1 or not data2:
                return {
                    'error': f'Нет данных за одну из дат: {date1} или {date2}',
                    'date1_available': bool(data1),
                    'date2_available': bool(data2)
                }
            
            # Создаем словари регион_id -> цены для быстрого поиска
            prices1 = {item['region_id']: item['fuel_prices'] for item in data1}
            prices2 = {item['region_id']: item['fuel_prices'] for item in data2}
            
            # Находим общие регионы
            common_regions = set(prices1.keys()) & set(prices2.keys())
            
            if not common_regions:
                return {
                    'error': 'Нет общих регионов между датами',
                    'regions_date1': len(prices1),
                    'regions_date2': len(prices2)
                }
            
            comparison = {
                'date1': date1.strftime("%Y-%m-%d"),
                'date2': date2.strftime("%Y-%m-%d"),
                'common_regions_count': len(common_regions),
                'regions_only_date1': len(prices1) - len(common_regions),
                'regions_only_date2': len(prices2) - len(common_regions),
                'fuel_changes': {},
                'region_changes': []
            }
            
            # Анализируем изменения по типам топлива
            fuel_types = set()
            for region_prices in list(prices1.values()) + list(prices2.values()):
                if region_prices:
                    fuel_types.update(region_prices.keys())
            
            # Фильтруем по конкретному типу топлива если указан
            if fuel_type:
                fuel_types = {fuel_type} if fuel_type in fuel_types else set()
            
            for fuel in fuel_types:
                changes = []
                for region_id in common_regions:
                    price1 = prices1[region_id].get(fuel)
                    price2 = prices2[region_id].get(fuel)
                    
                    if price1 is not None and price2 is not None:
                        change = round(price2 - price1, 2)
                        if abs(change) > 0.01:  # Минимальное изменение 1 копейка
                            changes.append({
                                'region_id': region_id,
                                'price1': price1,
                                'price2': price2,
                                'change': change,
                                'change_percent': round((change / price1) * 100, 2) if price1 > 0 else 0
                            })
                
                if changes:
                    # Сортируем по размеру изменения
                    changes.sort(key=lambda x: abs(x['change']), reverse=True)
                    
                    comparison['fuel_changes'][fuel] = {
                        'regions_with_changes': len(changes),
                        'avg_change': round(sum(c['change'] for c in changes) / len(changes), 2),
                        'max_increase': max(changes, key=lambda x: x['change']) if changes else None,
                        'max_decrease': min(changes, key=lambda x: x['change']) if changes else None,
                        'all_changes': changes[:20]  # Топ-20 изменений
                    }
            
            return comparison
            
        except Exception as e:
            return {'error': f'Ошибка сравнения: {str(e)}'}
    
    def _load_latest_data_for_date(self, target_date: date) -> Optional[List[Dict]]:
        """Загружает последние данные за указанную дату"""
        try:
            # Ищем в индексе
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                date_str = target_date.strftime("%Y%m%d")
                matching_entries = [
                    entry for entry in index_data['entries']
                    if entry['date'] == date_str
                ]
                
                if matching_entries:
                    # Берем последнюю запись за день
                    latest_entry = max(matching_entries, key=lambda x: x['timestamp'])
                    json_path = self.history_dir / latest_entry['files']['json']
                    
                    if json_path.exists():
                        with open(json_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"Ошибка загрузки данных за {target_date}: {e}")
            return None
    
    def find_price_trends(self, days: int = 7, fuel_type: str = "АИ-95") -> Dict[str, Any]:
        """Анализирует тренды цен за последние N дней"""
        try:
            # Получаем данные за последние дни
            trends = {
                'fuel_type': fuel_type,
                'period_days': days,
                'daily_averages': [],
                'regional_trends': {},
                'overall_trend': 'stable'
            }
            
            daily_data = {}
            end_date = date.today()
            
            for i in range(days):
                check_date = end_date - timedelta(days=i)
                data = self._load_latest_data_for_date(check_date)
                if data:
                    daily_data[check_date] = data
            
            if len(daily_data) < 2:
                return {'error': f'Недостаточно данных для анализа тренда (найдено {len(daily_data)} дней)'}
            
            # Вычисляем средние цены по дням
            for check_date in sorted(daily_data.keys()):
                data = daily_data[check_date]
                fuel_prices = [
                    item['fuel_prices'].get(fuel_type) 
                    for item in data 
                    if item.get('fuel_prices', {}).get(fuel_type) is not None
                ]
                
                if fuel_prices:
                    avg_price = round(sum(fuel_prices) / len(fuel_prices), 2)
                    trends['daily_averages'].append({
                        'date': check_date.strftime("%Y-%m-%d"),
                        'avg_price': avg_price,
                        'regions_count': len(fuel_prices)
                    })
            
            # Определяем общий тренд
            if len(trends['daily_averages']) >= 2:
                first_avg = trends['daily_averages'][0]['avg_price']
                last_avg = trends['daily_averages'][-1]['avg_price']
                change = last_avg - first_avg
                
                if abs(change) < 0.5:
                    trends['overall_trend'] = 'stable'
                elif change > 0:
                    trends['overall_trend'] = 'rising'
                else:
                    trends['overall_trend'] = 'falling'
                
                trends['total_change'] = round(change, 2)
                trends['total_change_percent'] = round((change / first_avg) * 100, 2) if first_avg > 0 else 0
            
            return trends
            
        except Exception as e:
            return {'error': f'Ошибка анализа трендов: {str(e)}'}
    
    def get_statistics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Получает сводную статистику за период"""
        try:
            if not self.metadata_file.exists():
                return {'error': 'Файл индекса истории не найден'}
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Фильтруем записи за последние N дней
            cutoff_date = (datetime.now() - timedelta(days=days)).date()
            recent_entries = [
                entry for entry in index_data['entries']
                if datetime.fromisoformat(entry['timestamp']).date() >= cutoff_date
            ]
            
            if not recent_entries:
                return {'error': f'Нет данных за последние {days} дней'}
            
            summary = {
                'period_days': days,
                'total_downloads': len(recent_entries),
                'unique_dates': len(set(entry['date'] for entry in recent_entries)),
                'completeness_distribution': {},
                'fuel_types_frequency': {},
                'average_regions_per_download': 0,
                'latest_entry': None
            }
            
            # Анализируем распределение полноты выгрузок
            for entry in recent_entries:
                completeness = entry.get('completeness', 'UNKNOWN')
                summary['completeness_distribution'][completeness] = \
                    summary['completeness_distribution'].get(completeness, 0) + 1
            
            # Анализируем частоту типов топлива
            all_fuel_types = set()
            total_regions = 0
            
            for entry in recent_entries:
                fuel_types = entry.get('fuel_types', [])
                for fuel in fuel_types:
                    summary['fuel_types_frequency'][fuel] = \
                        summary['fuel_types_frequency'].get(fuel, 0) + 1
                    all_fuel_types.add(fuel)
                
                total_regions += entry.get('successful_regions', 0)
            
            summary['average_regions_per_download'] = round(total_regions / len(recent_entries), 1)
            summary['unique_fuel_types'] = len(all_fuel_types)
            
            # Последняя запись
            if recent_entries:
                latest = max(recent_entries, key=lambda x: x['timestamp'])
                summary['latest_entry'] = {
                    'timestamp': latest['timestamp'],
                    'completeness': latest.get('completeness'),
                    'regions': latest.get('successful_regions'),
                    'fuel_types_count': len(latest.get('fuel_types', []))
                }
            
            return summary
            
        except Exception as e:
            return {'error': f'Ошибка получения статистики: {str(e)}'}


def print_comparison_result(comparison: Dict[str, Any]):
    """Выводит результат сравнения в красивом формате"""
    if 'error' in comparison:
        print(f"❌ ОШИБКА: {comparison['error']}")
        return
    
    print(f"\n📊 СРАВНЕНИЕ ЦЕН: {comparison['date1']} → {comparison['date2']}")
    print("=" * 70)
    print(f"Общих регионов: {comparison['common_regions_count']}")
    
    if 'fuel_changes' in comparison:
        for fuel_type, changes in comparison['fuel_changes'].items():
            print(f"\n🛢️  {fuel_type}:")
            print(f"   Регионов с изменениями: {changes['regions_with_changes']}")
            print(f"   Среднее изменение: {changes['avg_change']:+.2f} руб.")
            
            if changes['max_increase']:
                inc = changes['max_increase']
                print(f"   Максимальный рост: +{inc['change']:.2f} руб. (регион {inc['region_id']})")
            
            if changes['max_decrease']:
                dec = changes['max_decrease']
                print(f"   Максимальное снижение: {dec['change']:.2f} руб. (регион {dec['region_id']})")


def print_trends_result(trends: Dict[str, Any]):
    """Выводит результат анализа трендов"""
    if 'error' in trends:
        print(f"❌ ОШИБКА: {trends['error']}")
        return
    
    print(f"\n📈 ТРЕНД ЦЕН НА {trends['fuel_type']} за {trends['period_days']} дней")
    print("=" * 70)
    
    if 'overall_trend' in trends:
        trend_icons = {
            'rising': '📈 РОСТ',
            'falling': '📉 СНИЖЕНИЕ', 
            'stable': '➡️  СТАБИЛЬНОСТЬ'
        }
        
        trend_text = trend_icons.get(trends['overall_trend'], '❓ НЕИЗВЕСТНО')
        print(f"Общий тренд: {trend_text}")
        
        if 'total_change' in trends:
            print(f"Изменение: {trends['total_change']:+.2f} руб. ({trends.get('total_change_percent', 0):+.1f}%)")
    
    if 'daily_averages' in trends and trends['daily_averages']:
        print(f"\nСредние цены по дням:")
        for day_data in trends['daily_averages'][-7:]:  # Последние 7 дней
            print(f"  {day_data['date']}: {day_data['avg_price']:.2f} руб. ({day_data['regions_count']} регионов)")


def print_statistics_summary(stats: Dict[str, Any]):
    """Выводит сводную статистику"""
    if 'error' in stats:
        print(f"❌ ОШИБКА: {stats['error']}")
        return
    
    print(f"\n📋 СТАТИСТИКА ЗА {stats['period_days']} ДНЕЙ")
    print("=" * 70)
    print(f"Всего выгрузок: {stats['total_downloads']}")
    print(f"Уникальных дат: {stats['unique_dates']}")
    print(f"Среднее регионов на выгрузку: {stats['average_regions_per_download']}")
    print(f"Уникальных типов топлива: {stats['unique_fuel_types']}")
    
    if 'completeness_distribution' in stats:
        print(f"\nРаспределение по полноте:")
        for completeness, count in stats['completeness_distribution'].items():
            print(f"  {completeness}: {count} выгрузок")
    
    if 'latest_entry' in stats and stats['latest_entry']:
        latest = stats['latest_entry']
        print(f"\nПоследняя выгрузка:")
        print(f"  Время: {latest['timestamp']}")
        print(f"  Полнота: {latest['completeness']}")
        print(f"  Регионов: {latest['regions']}")


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        description="Утилиты для анализа истории региональных цен",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python history_utils.py compare --date1 2025-01-15 --date2 2025-01-16
  python history_utils.py trends --days 7 --fuel АИ-95
  python history_utils.py stats --days 30
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда сравнения
    compare_parser = subparsers.add_parser('compare', help='Сравнить цены между датами')
    compare_parser.add_argument('--date1', required=True, help='Первая дата (YYYY-MM-DD)')
    compare_parser.add_argument('--date2', required=True, help='Вторая дата (YYYY-MM-DD)')
    compare_parser.add_argument('--fuel', help='Тип топлива для анализа')
    
    # Команда анализа трендов
    trends_parser = subparsers.add_parser('trends', help='Анализ трендов цен')
    trends_parser.add_argument('--days', type=int, default=7, help='Количество дней для анализа')
    trends_parser.add_argument('--fuel', default='АИ-95', help='Тип топлива')
    
    # Команда статистики
    stats_parser = subparsers.add_parser('stats', help='Сводная статистика')
    stats_parser.add_argument('--days', type=int, default=30, help='Период в днях')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    analyzer = RegionalHistoryAnalyzer()
    
    try:
        if args.command == 'compare':
            date1 = datetime.strptime(args.date1, '%Y-%m-%d').date()
            date2 = datetime.strptime(args.date2, '%Y-%m-%d').date()
            result = analyzer.compare_dates(date1, date2, args.fuel)
            print_comparison_result(result)
            
        elif args.command == 'trends':
            result = analyzer.find_price_trends(args.days, args.fuel)
            print_trends_result(result)
            
        elif args.command == 'stats':
            result = analyzer.get_statistics_summary(args.days)
            print_statistics_summary(result)
            
    except ValueError as e:
        print(f"❌ ОШИБКА: Неверный формат даты. Используйте YYYY-MM-DD")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ОШИБКА: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()