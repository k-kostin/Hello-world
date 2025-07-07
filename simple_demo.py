#!/usr/bin/env python3
"""
Простая демонстрация работы регионального парсера russiabase.ru
Показывает сбор средних цен на топливо по регионам
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parsers.russiabase_parser import RussiaBaseRegionalParser
from datetime import datetime


def demo_regional_parser():
    """Демонстрация работы парсера региональных цен"""
    print("🚀 ДЕМОНСТРАЦИЯ РЕГИОНАЛЬНОГО ПАРСЕРА RUSSIABASE.RU")
    print("=" * 60)
    print("Собираем средние цены на топливо по регионам России")
    print("=" * 60)
    
    # Создаем парсер
    config = {
        "type": "russiabase_regional",
        "name": "RussiaBase Regional Demo"
    }
    
    parser = RussiaBaseRegionalParser("demo", config)
    
    # Демо-регионы для тестирования
    demo_regions = [
        {"id": 77, "name": "Москва"},
        {"id": 78, "name": "Санкт-Петербург"},  
        {"id": 40, "name": "Курская область"},
        {"id": 23, "name": "Краснодарский край"},
        {"id": 16, "name": "Республика Татарстан"}
    ]
    
    print(f"🎯 Тестируем {len(demo_regions)} регионов:")
    for region in demo_regions:
        print(f"   • {region['name']} (ID: {region['id']})")
    
    print("\n" + "=" * 60)
    print("🔄 НАЧИНАЕМ СБОР ДАННЫХ...")
    print("=" * 60)
    
    results = []
    
    for i, region in enumerate(demo_regions, 1):
        region_id = region["id"]
        region_name = region["name"]
        
        print(f"\n[{i}/{len(demo_regions)}] 🔍 Обрабатываем: {region_name}")
        print(f"    🌐 URL: https://russiabase.ru/prices?region={region_id}")
        
        try:
            # Получаем данные региона
            region_data = parser._fetch_region_data(region_id, region_name)
            results.append(region_data)
            
            # Показываем результат
            if region_data['status'] == 'success':
                fuel_prices = region_data.get('fuel_prices', {})
                if fuel_prices:
                    print(f"    ✅ Статус: Успешно")
                    print(f"    💰 Найдено цен: {len(fuel_prices)}")
                    for fuel_type, price in fuel_prices.items():
                        print(f"        {fuel_type}: {price} руб.")
                else:
                    print(f"    ⚠️ Статус: Цены не найдены")
            else:
                error = region_data.get('error', 'Неизвестная ошибка')
                print(f"    ❌ Статус: Ошибка - {error}")
            
            # Небольшая пауза между запросами
            parser.add_delay()
            
        except Exception as e:
            print(f"    💥 Исключение: {e}")
            results.append({
                'region_id': region_id,
                'region_name': region_name,
                'fuel_prices': {},
                'status': 'error',
                'error': str(e)
            })
    
    print("\n" + "=" * 60)
    print("📊 СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    # Создаем таблицу
    df = parser.create_fuel_prices_table(results)
    print(df.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("📈 СТАТИСТИКА")
    print("=" * 60)
    
    # Статистика
    stats = parser._create_statistics(results)
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ')}: {value}")
    
    print("\n" + "=" * 60)
    print("💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    # Сохраняем в файл
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"demo_regional_prices_{timestamp}.xlsx"
    
    try:
        saved_file = parser.save_to_excel(results, filename)
        print(f"✅ Результаты сохранены в файл: {saved_file}")
        print(f"📁 Файл содержит листы: Regional_Prices, Statistics, Errors")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)
    
    successful = len([r for r in results if r['status'] == 'success'])
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    print(f"📊 Обработано регионов: {total}")
    print(f"✅ Успешных: {successful}")
    print(f"📈 Процент успеха: {success_rate:.1f}%")
    
    if successful > 0:
        print("\n🎯 ПАРСЕР СРЕДНИХ ЦЕН НА ТОПЛИВО РАБОТАЕТ ПОЛНОЦЕННО!")
        print("   Может собирать данные по всем регионам России")
        print("   Для полного сбора используйте: python run_regional_parser.py --full")
    else:
        print("\n⚠️ Возможны проблемы с сетевым подключением или структурой сайта")
    
    return results


def show_usage_examples():
    """Показывает примеры использования парсера"""
    print("\n" + "=" * 60)
    print("📚 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ПАРСЕРА")
    print("=" * 60)
    
    examples = [
        ("Полный сбор по всем регионам", "python run_regional_parser.py --full"),
        ("Тестовый сбор (5 регионов)", "python run_regional_parser.py --test"),
        ("Сбор по конкретным регионам", "python run_regional_parser.py --test --regions 77 78 40"),
        ("Тест одного региона", "python run_regional_parser.py --region 77"),
        ("Список всех регионов", "python run_regional_parser.py --list-regions"),
        ("Подробный вывод", "python run_regional_parser.py --test --verbose")
    ]
    
    for i, (description, command) in enumerate(examples, 1):
        print(f"{i}. {description}:")
        print(f"   {command}")
        print()


def show_parser_features():
    """Показывает возможности парсера"""
    print("\n" + "=" * 60)
    print("⚡ ВОЗМОЖНОСТИ РЕГИОНАЛЬНОГО ПАРСЕРА")
    print("=" * 60)
    
    features = [
        "📍 Сбор данных по всем регионам России (85+ регионов)",
        "⛽ Поддержка всех видов топлива (АИ-92, АИ-95, АИ-98, АИ-100, Дизель, Газ)",
        "🔄 Множественные методы извлечения данных (JSON-LD, Next.js, regex, tables)",
        "📊 Создание сводных таблиц с региональными ценами",
        "💾 Экспорт в Excel с несколькими листами",
        "🛡️ Устойчивость к ошибкам и сетевым проблемам",
        "📝 Подробное логирование процесса",
        "⏱️ Контроль задержек для предотвращения блокировки",
        "📈 Статистика успешности сбора данных",
        "🎯 Возможность тестирования отдельных регионов"
    ]
    
    for feature in features:
        print(f"  {feature}")


if __name__ == "__main__":
    try:
        # Показываем возможности парсера
        show_parser_features()
        
        # Показываем примеры использования
        show_usage_examples()
        
        # Запускаем демонстрацию
        demo_regional_parser()
        
    except KeyboardInterrupt:
        print("\n🛑 Демонстрация прервана пользователем")
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        print("🔧 Проверьте настройки окружения и доступность сети")