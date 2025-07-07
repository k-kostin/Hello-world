# 🌍 Полное руководство по парсингу средних цен топлива по регионам России

## 📖 Содержание

1. [Что такое региональный парсинг?](#что-такое-региональный-парсинг)
2. [Быстрый старт](#быстрый-старт)
3. [Детальные команды](#детальные-команды)
4. [Программный интерфейс](#программный-интерфейс)
5. [Конфигурация](#конфигурация)
6. [Анализ данных](#анализ-данных)
7. [Форматы выходных данных](#форматы-выходных-данных)
8. [Примеры использования](#примеры-использования)
9. [Устранение неполадок](#устранение-неполадок)

---

## 🌟 Что такое региональный парсинг?

**Региональный парсер цен топлива** — это специализированный модуль, который извлекает **средние цены на топливо по всем регионам Российской Федерации**. 

### 🎯 Ключевые особенности

| Особенность | Описание |
|-------------|----------|
| **📊 Средние данные** | Не конкретные АЗС, а усредненные цены по региону |
| **🗺️ Полное покрытие** | Все 84 субъекта Российской Федерации |
| **⚡ Высокая скорость** | Один HTTP-запрос = все данные по региону |
| **🔄 Автоматическое извлечение** | Динамическое получение списка всех регионов |
| **📈 Аналитический формат** | Идеально для исследований и статистики |

### 💡 Отличия от обычного парсинга

| Критерий | Обычный парсинг | Региональный парсинг |
|----------|-----------------|---------------------|
| **Данные** | Конкретные АЗС | Средние цены по региону |
| **Объем данных** | Большой (тысячи записей) | Компактный (84 региона) |
| **Скорость** | Медленно | Быстро |
| **Назначение** | Поиск конкретных заправок | Аналитика и статистика |
| **Покрытие** | Частичное | 100% территории РФ |

---

## 🚀 Быстрый старт

### 🌍 Парсинг всех регионов России (84 региона)

```bash
python regional_parser.py --all-regions
```

**Результат:**
- Извлекает средние цены по всем 84 регионам РФ
- Создает файл `regional_prices_YYYYMMDD_HHMMSS.json`
- Показывает статистику по топливу
- Время выполнения: ~3-5 минут

### ⭐ Парсинг популярных регионов

```bash
python regional_parser.py --popular-regions
```

**Популярные регионы (по умолчанию):**
- 77 - Москва
- 78 - Санкт-Петербург  
- 50 - Московская область
- 40 - Калужская область
- 23 - Краснодарский край
- 66 - Свердловская область

### 🎯 Парсинг конкретных регионов

```bash
# Москва, СПб и Московская область
python regional_parser.py --regions 77 78 50

# Только Москва
python regional_parser.py --regions 77
```

### 🔗 Через основной интерфейс

```bash
python main.py --networks regional_prices
```

---

## 📋 Детальные команды

### 🗺️ Просмотр всех доступных регионов

```bash
python regional_parser.py --list-regions
```

**Пример вывода:**
```
📍 Популярные регионы:
   77: Москва ⭐
   78: Санкт-Петербург ⭐
   50: Московская область ⭐

📍 Все остальные регионы:
    1: Республика Адыгея
    2: Республика Башкортостан
    3: Республика Бурятия
   ...
```

### ⚙️ Настройка параметров

#### Ограничение количества регионов
```bash
# Парсить только первые 10 регионов
python regional_parser.py --all-regions --max-regions 10

# Ограничить популярные регионы до 3
python regional_parser.py --popular-regions --max-regions 3
```

#### Настройка задержки между запросами
```bash
# Задержка 2 секунды (бережнее к серверу)
python regional_parser.py --popular-regions --delay 2.0

# Быстрый режим (1 секунда)
python regional_parser.py --popular-regions --delay 1.0
```

#### Подробное логирование
```bash
python regional_parser.py --all-regions --verbose
```

#### Интегрированный режим (через оркестратор)
```bash
python regional_parser.py --popular-regions --use-orchestrator
```

---

## 💻 Программный интерфейс

### 🔧 Базовое использование

```python
from src.parsers.russiabase_parser import RussiaBaseRegionalParser

# Создаем парсер
parser = RussiaBaseRegionalParser()

# 1. Получаем список всех доступных регионов
all_regions = parser.get_all_regions()
print(f"Всего регионов: {len(all_regions)}")

# 2. Парсим один регион
moscow_result = parser.get_region_prices(77, "Москва")
if moscow_result and moscow_result.status == 'success':
    print("Цены в Москве:")
    for fuel_type, price in moscow_result.fuel_prices.items():
        print(f"  {fuel_type}: {price:.2f} руб/л")
```

### 🌍 Парсинг множественных регионов

```python
# Подготавливаем список регионов
regions_to_parse = [
    {'id': 77, 'name': 'Москва'},
    {'id': 78, 'name': 'Санкт-Петербург'},
    {'id': 50, 'name': 'Московская область'}
]

# Парсим все регионы сразу
results = parser.parse_multiple_regions(regions_to_parse)

# Обрабатываем результаты
for result in results:
    print(f"\n--- {result.region_name} ---")
    if result.status == 'success':
        print(f"✅ Данные получены:")
        for fuel_type, price in result.fuel_prices.items():
            print(f"  {fuel_type}: {price:.2f} руб/л")
    else:
        print(f"❌ Ошибка: {result.error_message}")
```

### 🔄 Автоматический парсинг всех регионов

```python
# Получаем все регионы автоматически
all_regions = parser.get_all_regions()

# Конвертируем в формат для парсинга
regions_list = [
    {'id': region_id, 'name': region_name}
    for region_id, region_name in all_regions.items()
]

print(f"Парсим {len(regions_list)} регионов...")

# Парсим с ограничением (первые 20 регионов)
limited_regions = regions_list[:20]
results = parser.parse_multiple_regions(limited_regions)

print(f"Успешно получены данные для {len([r for r in results if r.status == 'success'])} регионов")
```

### 📊 Расширенная статистика

```python
def analyze_regional_prices(results):
    """Анализ региональных цен"""
    
    # Группируем данные по типам топлива
    fuel_data = {}
    successful_regions = []
    
    for result in results:
        if result.status == 'success' and result.fuel_prices:
            successful_regions.append(result)
            for fuel_type, price in result.fuel_prices.items():
                if fuel_type not in fuel_data:
                    fuel_data[fuel_type] = []
                fuel_data[fuel_type].append({
                    'region': result.region_name,
                    'price': price
                })
    
    # Статистика по топливу
    print("📊 Статистика по топливу:")
    for fuel_type, data in fuel_data.items():
        prices = [item['price'] for item in data]
        
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        min_region = next(item['region'] for item in data if item['price'] == min_price)
        max_region = next(item['region'] for item in data if item['price'] == max_price)
        
        print(f"\n{fuel_type}:")
        print(f"  📈 Средняя цена: {avg_price:.2f} руб/л")
        print(f"  📉 Минимум: {min_price:.2f} руб/л ({min_region})")
        print(f"  📈 Максимум: {max_price:.2f} руб/л ({max_region})")
        print(f"  🎯 Разброс: {max_price - min_price:.2f} руб/л")
    
    return fuel_data

# Использование
results = parser.parse_multiple_regions(regions_list)
fuel_stats = analyze_regional_prices(results)
```

---

## ⚙️ Конфигурация

### 📝 Основная конфигурация в `config.py`

```python
# Региональный парсер
GAS_STATION_NETWORKS["regional_prices"] = {
    "name": "Региональные цены",
    "type": "russiabase_regional",
    "base_url": "https://russiabase.ru/prices",
    "delay": 1.5,                      # Задержка между запросами (сек)
    "max_regions": None,               # Максимум регионов (None = все)
    "description": "Средние цены на топливо по регионам России"
}

# Настройки регионов
REGIONS_CONFIG = {
    "regions_file": "regions.md",
    "default_regions": [77, 78, 50, 40, 23, 66],  # Популярные регионы
    "enable_region_filtering": True,
    "enable_multi_region_parsing": True,
    "max_regions_per_network": 10
}
```

### 🔧 Программная конфигурация

```python
# Создание парсера с кастомной конфигурацией
custom_config = {
    'delay': 2.0,          # Увеличенная задержка
    'max_regions': 20,     # Ограничение регионов  
    'timeout': 45          # Увеличенный таймаут
}

parser = RussiaBaseRegionalParser("regional_prices", custom_config)
```

---

## 📊 Анализ данных

### 🎯 Топ самых дорогих/дешевых регионов

```python
def find_extreme_regions(results, fuel_type="АИ-95"):
    """Найти самые дорогие и дешевые регионы"""
    
    regions_data = []
    for result in results:
        if result.status == 'success' and fuel_type in result.fuel_prices:
            regions_data.append({
                'region': result.region_name,
                'price': result.fuel_prices[fuel_type]
            })
    
    # Сортируем по цене
    regions_data.sort(key=lambda x: x['price'])
    
    print(f"🏆 Топ-5 самых дешевых регионов по {fuel_type}:")
    for i, data in enumerate(regions_data[:5], 1):
        print(f"  {i}. {data['region']}: {data['price']:.2f} руб/л")
    
    print(f"\n💸 Топ-5 самых дорогих регионов по {fuel_type}:")
    for i, data in enumerate(regions_data[-5:], 1):
        print(f"  {i}. {data['region']}: {data['price']:.2f} руб/л")
    
    return regions_data

# Использование
results = parser.parse_multiple_regions(regions_list)
extreme_data = find_extreme_regions(results, "АИ-95")
```

### 📈 Сравнение регионов

```python
def compare_regions(results, regions_to_compare):
    """Сравнить конкретные регионы"""
    
    comparison_data = {}
    
    for result in results:
        if result.region_name in regions_to_compare and result.status == 'success':
            comparison_data[result.region_name] = result.fuel_prices
    
    print("🔍 Сравнение регионов:")
    print(f"{'Регион':<20} {'АИ-92':<8} {'АИ-95':<8} {'АИ-98':<8} {'ДТ':<8}")
    print("-" * 60)
    
    for region, prices in comparison_data.items():
        ai92 = f"{prices.get('АИ-92', 0):.2f}" if prices.get('АИ-92') else "-"
        ai95 = f"{prices.get('АИ-95', 0):.2f}" if prices.get('АИ-95') else "-"
        ai98 = f"{prices.get('АИ-98', 0):.2f}" if prices.get('АИ-98') else "-"
        dt = f"{prices.get('ДТ', 0):.2f}" if prices.get('ДТ') else "-"
        
        print(f"{region:<20} {ai92:<8} {ai95:<8} {ai98:<8} {dt:<8}")

# Использование
compare_regions(results, ["Москва", "Санкт-Петербург", "Московская область"])
```

### 💾 Экспорт в различные форматы

```python
import json
import csv
from datetime import datetime

def export_regional_data(results, format='json'):
    """Экспорт данных в различные форматы"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == 'json':
        # JSON формат
        json_data = []
        for result in results:
            json_data.append({
                'region_id': result.region_id,
                'region_name': result.region_name,
                'fuel_prices': result.fuel_prices,
                'timestamp': result.timestamp,
                'status': result.status
            })
        
        filename = f"regional_prices_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Данные сохранены в JSON: {filename}")
    
    elif format == 'csv':
        # CSV формат (развернутый)
        filename = f"regional_prices_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['region_id', 'region_name', 'fuel_type', 'price', 'timestamp'])
            
            for result in results:
                if result.status == 'success':
                    for fuel_type, price in result.fuel_prices.items():
                        writer.writerow([
                            result.region_id,
                            result.region_name,
                            fuel_type,
                            price,
                            result.timestamp
                        ])
        
        print(f"💾 Данные сохранены в CSV: {filename}")

# Использование
export_regional_data(results, 'json')
export_regional_data(results, 'csv')
```

---

## 📁 Форматы выходных данных

### 🏗️ Структура результата

```python
@dataclass
class RegionalPriceResult:
    region_id: int                    # ID региона (77 для Москвы)
    region_name: str                  # Название ("Москва")
    fuel_prices: Dict[str, float]     # {"АИ-92": 45.50, "АИ-95": 48.20}
    url: str                          # URL запроса
    timestamp: str                    # ISO формат времени
    status: str                       # 'success' или 'error'
    error_message: str = None         # Описание ошибки
```

### 📄 JSON файл

```json
[
  {
    "region_id": 77,
    "region_name": "Москва",
    "fuel_prices": {
      "АИ-92": 45.50,
      "АИ-95": 48.20,
      "АИ-98": 52.10,
      "ДТ": 49.80,
      "Пропан": 26.30
    },
    "timestamp": "2024-12-01T15:30:45",
    "status": "success"
  },
  {
    "region_id": 78,
    "region_name": "Санкт-Петербург",
    "fuel_prices": {
      "АИ-92": 44.90,
      "АИ-95": 47.80,
      "АИ-98": 51.60,
      "ДТ": 49.20
    },
    "timestamp": "2024-12-01T15:30:48",
    "status": "success"
  }
]
```

### 📊 Excel файл (через оркестратор)

При использовании `--use-orchestrator` создается Excel файл со структурой:

| region_id | region_name | fuel_type | avg_price | currency | timestamp |
|-----------|-------------|-----------|-----------|----------|-----------|
| 77 | Москва | АИ-92 | 45.50 | RUB | 2024-12-01T15:30:45 |
| 77 | Москва | АИ-95 | 48.20 | RUB | 2024-12-01T15:30:45 |
| 78 | Санкт-Петербург | АИ-92 | 44.90 | RUB | 2024-12-01T15:30:48 |

---

## 🎨 Примеры использования

### 🌍 Пример 1: Аналитический отчет по России

```python
#!/usr/bin/env python3
"""
Создание аналитического отчета по ценам топлива в России
"""

from src.parsers.russiabase_parser import RussiaBaseRegionalParser
from datetime import datetime
import json

def create_russia_fuel_report():
    """Создает полный отчет по ценам в России"""
    
    parser = RussiaBaseRegionalParser()
    
    # Получаем все регионы
    all_regions = parser.get_all_regions()
    regions_list = [
        {'id': region_id, 'name': region_name}
        for region_id, region_name in all_regions.items()
    ]
    
    print(f"🚀 Начинаем парсинг {len(regions_list)} регионов...")
    
    # Парсим все регионы
    results = parser.parse_multiple_regions(regions_list)
    
    # Анализируем результаты
    successful_results = [r for r in results if r.status == 'success']
    
    print(f"✅ Успешно получены данные для {len(successful_results)} регионов")
    
    # Создаем отчет
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_regions': len(regions_list),
        'successful_regions': len(successful_results),
        'failed_regions': len(results) - len(successful_results),
        'fuel_statistics': {},
        'regional_data': []
    }
    
    # Группируем по топливу для статистики
    fuel_stats = {}
    
    for result in successful_results:
        # Добавляем в региональные данные
        report['regional_data'].append({
            'region_id': result.region_id,
            'region_name': result.region_name,
            'fuel_prices': result.fuel_prices
        })
        
        # Собираем статистику по топливу
        for fuel_type, price in result.fuel_prices.items():
            if fuel_type not in fuel_stats:
                fuel_stats[fuel_type] = []
            fuel_stats[fuel_type].append(price)
    
    # Вычисляем статистику
    for fuel_type, prices in fuel_stats.items():
        report['fuel_statistics'][fuel_type] = {
            'average_price': round(sum(prices) / len(prices), 2),
            'min_price': min(prices),
            'max_price': max(prices),
            'regions_count': len(prices),
            'price_spread': round(max(prices) - min(prices), 2)
        }
    
    # Сохраняем отчет
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"russia_fuel_report_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 Отчет сохранен: {filename}")
    
    # Выводим краткую статистику
    print("\n📈 Средние цены по России:")
    for fuel_type, stats in report['fuel_statistics'].items():
        print(f"  {fuel_type}: {stats['average_price']:.2f} руб/л "
              f"(разброс: {stats['price_spread']:.2f} руб/л)")
    
    return report

if __name__ == "__main__":
    report = create_russia_fuel_report()
```

### 🔄 Пример 2: Мониторинг изменений цен

```python
#!/usr/bin/env python3
"""
Мониторинг изменений цен в популярных регионах
"""

import json
import os
from datetime import datetime, timedelta
from src.parsers.russiabase_parser import RussiaBaseRegionalParser

def monitor_price_changes():
    """Мониторинг изменений цен"""
    
    parser = RussiaBaseRegionalParser()
    
    # Популярные регионы для мониторинга
    monitoring_regions = [
        {'id': 77, 'name': 'Москва'},
        {'id': 78, 'name': 'Санкт-Петербург'},
        {'id': 50, 'name': 'Московская область'},
        {'id': 23, 'name': 'Краснодарский край'}
    ]
    
    print("📊 Мониторинг цен в ключевых регионах...")
    
    # Получаем текущие цены
    current_results = parser.parse_multiple_regions(monitoring_regions)
    current_data = {}
    
    for result in current_results:
        if result.status == 'success':
            current_data[result.region_name] = result.fuel_prices
    
    # Попытка загрузить предыдущие данные
    previous_file = "previous_monitoring_data.json"
    previous_data = {}
    
    if os.path.exists(previous_file):
        with open(previous_file, 'r', encoding='utf-8') as f:
            previous_data = json.load(f)
    
    # Сравниваем и выводим изменения
    print("\n🔍 Изменения цен:")
    
    for region_name, current_prices in current_data.items():
        print(f"\n📍 {region_name}:")
        
        if region_name in previous_data:
            previous_prices = previous_data[region_name]
            
            for fuel_type, current_price in current_prices.items():
                if fuel_type in previous_prices:
                    previous_price = previous_prices[fuel_type]
                    change = current_price - previous_price
                    
                    if abs(change) > 0.01:  # Изменение больше 1 копейки
                        direction = "📈" if change > 0 else "📉"
                        print(f"  {fuel_type}: {previous_price:.2f} → {current_price:.2f} "
                              f"{direction} {change:+.2f}")
                    else:
                        print(f"  {fuel_type}: {current_price:.2f} (без изменений)")
                else:
                    print(f"  {fuel_type}: {current_price:.2f} (новые данные)")
        else:
            print(f"  Первый запуск мониторинга")
            for fuel_type, price in current_prices.items():
                print(f"  {fuel_type}: {price:.2f}")
    
    # Сохраняем текущие данные для следующего сравнения
    with open(previous_file, 'w', encoding='utf-8') as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)
    
    # Сохраняем исторические данные
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_file = f"price_history_{timestamp}.json"
    
    history_data = {
        'timestamp': datetime.now().isoformat(),
        'regions': current_data
    }
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Данные сохранены: {history_file}")

if __name__ == "__main__":
    monitor_price_changes()
```

### 📊 Пример 3: Генерация Excel отчета

```python
#!/usr/bin/env python3
"""
Создание подробного Excel отчета по региональным ценам
"""

import pandas as pd
from datetime import datetime
from src.parsers.russiabase_parser import RussiaBaseRegionalParser

def create_excel_report():
    """Создает подробный Excel отчет"""
    
    parser = RussiaBaseRegionalParser()
    
    # Получаем данные по всем регионам
    all_regions = parser.get_all_regions()
    regions_list = list(all_regions.items())[:20]  # Ограничиваем для примера
    
    regions_for_parsing = [
        {'id': region_id, 'name': region_name}
        for region_id, region_name in regions_list
    ]
    
    print(f"📊 Создаем Excel отчет для {len(regions_for_parsing)} регионов...")
    
    results = parser.parse_multiple_regions(regions_for_parsing)
    
    # Подготавливаем данные для Excel
    data_rows = []
    statistics_data = {}
    
    for result in results:
        if result.status == 'success':
            for fuel_type, price in result.fuel_prices.items():
                data_rows.append({
                    'Регион ID': result.region_id,
                    'Название региона': result.region_name,
                    'Тип топлива': fuel_type,
                    'Цена (руб/л)': price,
                    'Время обновления': result.timestamp
                })
                
                # Собираем статистику
                if fuel_type not in statistics_data:
                    statistics_data[fuel_type] = []
                statistics_data[fuel_type].append(price)
    
    # Создаем DataFrame
    df_main = pd.DataFrame(data_rows)
    
    # Статистика по топливу
    stats_rows = []
    for fuel_type, prices in statistics_data.items():
        stats_rows.append({
            'Тип топлива': fuel_type,
            'Средняя цена': round(sum(prices) / len(prices), 2),
            'Минимальная цена': min(prices),
            'Максимальная цена': max(prices),
            'Количество регионов': len(prices),
            'Разброс цен': round(max(prices) - min(prices), 2)
        })
    
    df_stats = pd.DataFrame(stats_rows)
    
    # Сводная таблица (регионы × топливо)
    df_pivot = df_main.pivot(index='Название региона', 
                            columns='Тип топлива', 
                            values='Цена (руб/л)')
    
    # Сохраняем в Excel с несколькими листами
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"regional_prices_report_{timestamp}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Основные данные
        df_main.to_excel(writer, sheet_name='Детальные данные', index=False)
        
        # Статистика
        df_stats.to_excel(writer, sheet_name='Статистика', index=False)
        
        # Сводная таблица
        df_pivot.to_excel(writer, sheet_name='Сводная таблица')
        
        # Карта регионов
        regions_df = pd.DataFrame([
            {'ID': region_id, 'Название': region_name}
            for region_id, region_name in all_regions.items()
        ])
        regions_df.to_excel(writer, sheet_name='Карта регионов', index=False)
    
    print(f"✅ Excel отчет создан: {filename}")
    print(f"📊 Листы: Детальные данные, Статистика, Сводная таблица, Карта регионов")
    
    return filename

if __name__ == "__main__":
    create_excel_report()
```

---

## 🛠️ Устранение неполадок

### ❌ Частые ошибки и решения

#### 1. Ошибка подключения к сети

```
ConnectionError: HTTPSConnectionPool(host='russiabase.ru', port=443)
```

**Решения:**
```bash
# Увеличить таймаут
python regional_parser.py --popular-regions --delay 3.0

# Проверить интернет-соединение
ping russiabase.ru

# Попробовать через VPN (если заблокирован)
```

#### 2. Ошибка парсинга JSON

```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Решения:**
- Сайт может временно возвращать HTML вместо JSON
- Увеличить задержку между запросами
- Попробовать позже

#### 3. Пустые результаты

```
Получено 0 регионов с данными
```

**Диагностика:**
```python
# Проверим доступность API
parser = RussiaBaseRegionalParser()
regions = parser.get_all_regions()
print(f"Доступно регионов: {len(regions)}")

# Тестируем один регион
test_result = parser.get_region_prices(77, "Москва")
print(f"Статус: {test_result.status}")
if test_result.error_message:
    print(f"Ошибка: {test_result.error_message}")
```

#### 4. Медленная работа

**Оптимизация:**
```bash
# Уменьшить задержку (осторожно!)
python regional_parser.py --popular-regions --delay 1.0

# Ограничить количество регионов
python regional_parser.py --all-regions --max-regions 20

# Использовать популярные регионы вместо всех
python regional_parser.py --popular-regions
```

### 🔍 Отладка

#### Включение подробного логирования

```bash
python regional_parser.py --popular-regions --verbose
```

#### Программная отладка

```python
import logging
from loguru import logger

# Настройка детального логирования
logger.add("debug.log", level="DEBUG")

# Тестирование с отладкой
parser = RussiaBaseRegionalParser()
parser.debug = True  # Если поддерживается

result = parser.get_region_prices(77, "Москва")
logger.debug(f"Результат: {result}")
```

---

## 📞 Поддержка

### 🆘 Если ничего не работает

1. **Проверьте доступность сайта:**
   ```bash
   curl -I https://russiabase.ru/prices
   ```

2. **Проверьте версии библиотек:**
   ```bash
   pip list | grep -E "(requests|beautifulsoup4|lxml)"
   ```

3. **Очистите кэш и попробуйте снова:**
   ```bash
   pip cache purge
   pip install --upgrade requests beautifulsoup4
   ```

4. **Создайте issue в репозитории** с подробным описанием ошибки.

### 📧 Контакты

- GitHub Issues: [создать issue]
- Email: [ваш email]
- Telegram: [ваш телеграм]

---

## 📚 Дополнительные ресурсы

- [Основной README](README.md) - общая документация проекта
- [Архитектура проекта](ARCHITECTURE.md) - техническая документация
- [Примеры использования](example_usage.py) - готовые примеры кода

---

**💡 Совет:** Для продакшн использования рекомендуется настроить мониторинг и автоматические уведомления об изменениях цен.

**⚠️ Предупреждение:** Соблюдайте этику парсинга - не создавайте излишнюю нагрузку на серверы, используйте разумные задержки между запросами.