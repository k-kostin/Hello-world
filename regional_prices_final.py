#!/usr/bin/env python3
"""
Финальная версия парсера региональных цен на топливо russiabase.ru
Доработанный парсер с поддержкой специфичных селекторов и улучшенной обработкой таблиц
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.russiabase_parser import RussiaBaseRegionalParser, PriceData
from src.regions import RegionManager

class RegionalPriceAnalyzer:
    """Анализатор региональных цен на топливо"""
    
    def __init__(self):
        self.parser = RussiaBaseRegionalParser(delay=1.5)
        self.region_manager = RegionManager()
        self.results: List[PriceData] = []
    
    def get_prices_for_region(self, region_id: int) -> Dict[str, Any]:
        """Получает цены для конкретного региона"""
        region = self.region_manager.get_region_by_id(region_id)
        if not region:
            return {"error": f"Регион с ID {region_id} не найден"}
        
        result = self.parser.get_region_prices(region_id, region['name'])
        if result and result.fuel_prices:
            return {
                "region_id": region_id,
                "region_name": region['name'],
                "prices": result.fuel_prices,
                "timestamp": result.timestamp,
                "status": "success"
            }
        else:
            return {
                "region_id": region_id,
                "region_name": region['name'],
                "error": "Не удалось получить цены",
                "status": "error"
            }
    
    def get_prices_for_multiple_regions(self, region_ids: List[int]) -> List[Dict[str, Any]]:
        """Получает цены для нескольких регионов"""
        results = []
        
        print(f"🔄 Получение цен для {len(region_ids)} регионов...")
        
        for i, region_id in enumerate(region_ids, 1):
            print(f"  [{i}/{len(region_ids)}] Обработка региона ID {region_id}")
            
            result = self.get_prices_for_region(region_id)
            results.append(result)
            
            # Небольшая пауза между запросами
            import time
            time.sleep(1.0)
        
        return results
    
    def get_popular_regions_prices(self) -> List[Dict[str, Any]]:
        """Получает цены для популярных регионов"""
        popular_regions = self.region_manager.get_popular_regions()
        region_ids = [region['id'] for region in popular_regions]
        return self.get_prices_for_multiple_regions(region_ids)
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str | None = None):
        """Сохраняет данные в JSON файл"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"regional_prices_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Данные сохранены в файл: {filename}")
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str | None = None):
        """Сохраняет данные в CSV файл"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"regional_prices_{timestamp}.csv"
        
        # Получаем все уникальные виды топлива
        all_fuel_types = set()
        for item in data:
            if 'prices' in item:
                all_fuel_types.update(item['prices'].keys())
        
        all_fuel_types = sorted(list(all_fuel_types))
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['region_id', 'region_name', 'timestamp', 'status'] + all_fuel_types
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for item in data:
                row = {
                    'region_id': item.get('region_id', ''),
                    'region_name': item.get('region_name', ''),
                    'timestamp': item.get('timestamp', ''),
                    'status': item.get('status', '')
                }
                
                if 'prices' in item:
                    for fuel_type in all_fuel_types:
                        row[fuel_type] = item['prices'].get(fuel_type, '')
                
                writer.writerow(row)
        
        print(f"📊 Данные сохранены в CSV файл: {filename}")
    
    def print_summary_table(self, data: List[Dict[str, Any]]):
        """Выводит сводную таблицу с ценами"""
        print("\n" + "=" * 100)
        print("📋 СВОДНАЯ ТАБЛИЦА ЦЕН НА ТОПЛИВО ПО РЕГИОНАМ")
        print("=" * 100)
        
        # Заголовок таблицы
        print(f"{'Регион':<30} {'АИ-92':<8} {'АИ-95':<8} {'АИ-98':<8} {'АИ-100':<8} {'ДТ':<8} {'Пропан':<8} {'Статус':<10}")
        print("-" * 100)
        
        # Данные по регионам
        successful_regions = 0
        fuel_stats = {}
        
        for item in data:
            region_name = item.get('region_name', 'Неизвестно')[:29]
            status = item.get('status', 'unknown')
            
            if status == 'success' and 'prices' in item:
                successful_regions += 1
                prices = item['prices']
                
                # Собираем статистику по топливу
                for fuel_type, price in prices.items():
                    if fuel_type not in fuel_stats:
                        fuel_stats[fuel_type] = []
                    fuel_stats[fuel_type].append(price)
                
                # Форматируем цены для вывода
                ai92 = f"{prices.get('АИ-92', 0):.1f}" if prices.get('АИ-92') else "-"
                ai95 = f"{prices.get('АИ-95', 0):.1f}" if prices.get('АИ-95') else "-"
                ai98 = f"{prices.get('АИ-98', 0):.1f}" if prices.get('АИ-98') else "-"
                ai100 = f"{prices.get('АИ-100', 0):.1f}" if prices.get('АИ-100') else "-"
                dt = f"{prices.get('ДТ', 0):.1f}" if prices.get('ДТ') else "-"
                propan = f"{prices.get('Пропан', 0):.1f}" if prices.get('Пропан') else "-"
                
                print(f"{region_name:<30} {ai92:<8} {ai95:<8} {ai98:<8} {ai100:<8} {dt:<8} {propan:<8} {'✅':<10}")
            else:
                print(f"{region_name:<30} {'-':<8} {'-':<8} {'-':<8} {'-':<8} {'-':<8} {'-':<8} {'❌':<10}")
        
        print("-" * 100)
        
        # Статистика
        print(f"\n📊 СТАТИСТИКА:")
        print(f"Всего регионов: {len(data)}")
        print(f"Успешно обработано: {successful_regions}")
        print(f"С ошибками: {len(data) - successful_regions}")
        
        if fuel_stats:
            print(f"\n💰 СРЕДНИЕ ЦЕНЫ (руб/л):")
            for fuel_type, prices in fuel_stats.items():
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                print(f"  {fuel_type:<10}: ср. {avg_price:.2f}, мин. {min_price:.2f}, макс. {max_price:.2f}")

def main():
    """Главная функция"""
    print("🏁 Финальная версия парсера региональных цен russiabase.ru")
    print("=" * 60)
    
    analyzer = RegionalPriceAnalyzer()
    
    # Пример 1: Получение цен для конкретного региона (Краснодарский край - ID 56)
    print("\n1️⃣ Получение цен для Краснодарского края (ID: 56)")
    print("-" * 50)
    
    krasnodar_prices = analyzer.get_prices_for_region(56)
    
    if krasnodar_prices.get('status') == 'success':
        print(f"✅ Регион: {krasnodar_prices['region_name']}")
        print(f"📅 Время: {krasnodar_prices['timestamp']}")
        print("💰 Цены:")
        for fuel_type, price in krasnodar_prices['prices'].items():
            print(f"    {fuel_type}: {price:.2f} руб/л")
    else:
        print(f"❌ Ошибка: {krasnodar_prices.get('error', 'Неизвестная ошибка')}")
    
    # Пример 2: Получение цен для нескольких важных регионов
    print("\n2️⃣ Получение цен для ключевых регионов")
    print("-" * 50)
    
    key_regions = [77, 78, 50, 23, 66, 52, 16]  # Москва, СПб, МО, Краснодарский, Свердловская, Нижегородская, Татарстан
    
    multiple_prices = analyzer.get_prices_for_multiple_regions(key_regions)
    
    # Выводим сводную таблицу
    analyzer.print_summary_table(multiple_prices)
    
    # Сохраняем результаты
    print("\n3️⃣ Сохранение результатов")
    print("-" * 50)
    
    analyzer.save_to_json(multiple_prices)
    analyzer.save_to_csv(multiple_prices)
    
    print(f"\n✅ Работа завершена: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Работа прервана пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()