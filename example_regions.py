#!/usr/bin/env python3
"""
Пример использования функциональности регионов для парсинга russiabase.ru
"""
import sys
from pathlib import Path

# Добавляем src в путь для импорта
sys.path.append(str(Path(__file__).parent / "src"))

from regions import region_manager, get_region_id_by_name, is_valid_region_id


def demo_region_functionality():
    """Демонстрация функциональности работы с регионами"""
    print("🗺️  Демонстрация функциональности регионов")
    print("=" * 50)
    
    # Общая информация
    summary = region_manager.get_regions_summary()
    print(f"📊 Общая статистика:")
    print(f"   Всего регионов: {summary['total_regions']}")
    print(f"   Диапазон ID: {summary['id_range']['min']}-{summary['id_range']['max']}")
    print(f"   Популярных регионов: {summary['popular_regions']}")
    
    print(f"\n📋 По типам:")
    for region_type, count in summary['by_type'].items():
        print(f"   {region_type.capitalize()}: {count}")
    
    # Поиск региона по ID
    print(f"\n🔍 Поиск региона по ID:")
    region_id = 40  # Курская область
    region = region_manager.get_region_by_id(region_id)
    if region:
        print(f"   ID {region_id}: {region['name']}")
        print(f"   URL: {region['url']}")
    
    # Поиск по названию
    print(f"\n🔍 Поиск региона по названию:")
    region_name = "Москва"
    region = region_manager.get_region_by_name(region_name)
    if region:
        print(f"   '{region_name}' найдена: ID {region['id']}")
        print(f"   Полное название: {region['name']}")
    
    # Популярные регионы
    print(f"\n⭐ Популярные регионы:")
    popular = region_manager.get_popular_regions()
    for region in popular[:5]:  # Показываем первые 5
        print(f"   {region['id']:2d}: {region['name']}")
    
    # Поиск по типу
    print(f"\n🏛️  Республики (первые 5):")
    republics = region_manager.get_regions_by_type('республика')
    for region in republics[:5]:
        print(f"   {region['id']:2d}: {region['name']}")
    
    # Поиск по части названия
    print(f"\n🔎 Поиск 'область' (первые 5):")
    regions = region_manager.search_regions('область')
    for region in regions[:5]:
        print(f"   {region['id']:2d}: {region['name']}")
    
    # Утилитарные функции
    print(f"\n🛠️  Утилитарные функции:")
    moscow_id = get_region_id_by_name("Москва")
    print(f"   ID Москвы: {moscow_id}")
    
    spb_valid = is_valid_region_id(78)
    print(f"   ID 78 валиден: {spb_valid}")
    
    invalid_check = is_valid_region_id(999)
    print(f"   ID 999 валиден: {invalid_check}")


def demo_parsing_with_regions():
    """Демонстрация парсинга с использованием регионов"""
    print(f"\n🚀 Примеры URL для парсинга:")
    print("=" * 50)
    
    # Популярные регионы для парсинга
    popular_regions = region_manager.get_popular_regions()[:3]
    
    brand_id = 119  # Лукойл
    
    for region in popular_regions:
        # Формируем URL для парсинга конкретной сети в конкретном регионе
        base_url = f"https://russiabase.ru/prices?brand={brand_id}&region={region['id']}"
        print(f"   {region['name']}:")
        print(f"     URL: {base_url}")
        print(f"     Команда: python main.py --networks lukoil --region {region['id']}")
        print()


def demo_region_validation():
    """Демонстрация валидации регионов"""
    print(f"\n✅ Валидация регионов:")
    print("=" * 50)
    
    test_regions = [
        ("Курская область", 40),
        ("Москва", 77),
        ("Неизвестный регион", 999),
        ("Санкт-Петербург", 78)
    ]
    
    for name, region_id in test_regions:
        is_valid = is_valid_region_id(region_id)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {name} (ID: {region_id}) - {'Валиден' if is_valid else 'Не найден'}")


if __name__ == "__main__":
    print("🗺️  Система управления регионами для RussiaBase.ru")
    print("=" * 60)
    print()
    
    try:
        demo_region_functionality()
        demo_parsing_with_regions()
        demo_region_validation()
        
        print(f"\n🎯 Готово!")
        print(f"📝 Для использования в парсерах импортируйте:")
        print(f"   from src.regions import region_manager, get_region_id_by_name")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)