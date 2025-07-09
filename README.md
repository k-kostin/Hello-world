# Парсер цен сетей АЗС

Система парсинга цен топлива с различных сетей автозаправочных станций в России.

## 🚀 Возможности

- **Поддержка множественных источников**: Лукойл, Газпром, Башнефть, Яндекс Карты, Татнефть
- **Различные методы парсинга**: HTML/JSON extraction, REST API, Selenium WebDriver
- **Региональный парсинг**: Средние цены по всем видам топлива по регионам России
- **Параллельная обработка**: Одновременный парсинг нескольких сетей
- **Унифицированный формат данных**: Все данные приводятся к единой схеме
- **Автоматическое сохранение**: Результаты сохраняются в Excel файлы

## 📋 Поддерживаемые сети АЗС

| Сеть | Источник | Метод парсинга | Особенности |
|------|----------|----------------|-------------|
| **Лукойл** | russiabase.ru | HTML + JSON | Региональные данные |
| **Башнефть** | russiabase.ru | HTML + JSON | Региональные данные |
| **Газпром** | gpnbonus.ru | REST API | Динамические данные |
| **Яндекс Карты** | yandex.ru/maps | Selenium | Поиск по карте |
| **Татнефть** | api.gs.tatneft.ru | REST API | Станции и цены |
| **Региональные цены** | russiabase.ru | Специальный парсер | Все 84 региона РФ |

## 🛠 Установка

### Требования
- Python 3.8+
- Google Chrome (для Selenium)

### Установка зависимостей
```bash
git clone <repository-url>
cd gas-station-parser
pip install -r requirements.txt
```

## 🏃‍♂️ Быстрый старт

### Список доступных сетей
```bash
python main.py --list
```

### Парсинг всех сетей
```bash
python main.py --all
```

### Парсинг конкретных сетей
```bash
python main.py --networks lukoil gazprom
```

### Региональный парсинг средних цен
```bash
python main.py --networks regional_prices
```

### Параллельный парсинг
```bash
python main.py --networks lukoil bashneft --parallel --workers 2
```

## 📊 Структура выходных данных

### Основные сети АЗС
| Поле | Тип | Описание |
|------|-----|----------|
| `station_id` | str | Уникальный ID станции |
| `network_name` | str | Название сети АЗС |
| `station_name` | str | Название станции |
| `address` | str | Полный адрес |
| `city` | str | Город |
| `region` | str | Регион |
| `region_id` | int | ID региона |
| `latitude` | float | Широта |
| `longitude` | float | Долгота |
| `fuel_type` | str | Тип топлива (АИ-92, АИ-95, ДТ и т.д.) |
| `price` | float | Цена за литр |
| `currency` | str | Валюта (обычно RUB) |
| `last_updated` | str | Время последнего обновления |
| `source` | str | Источник данных |

### Региональные средние цены
| Поле | Тип | Описание |
|------|-----|----------|
| `region_id` | int | ID региона |
| `region_name` | str | Название региона |
| `fuel_type` | str | Тип топлива |
| `avg_price` | float | **Средняя цена** по региону |
| `currency` | str | Валюта (RUB) |
| `data_source` | str | "regional_average" |
| `timestamp` | str | Время получения данных |

## 📁 Структура проекта

```
gas-station-parser/
├── src/
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py              # Базовый класс парсера
│   │   ├── russiabase_parser.py # Парсер для russiabase.ru
│   │   ├── gazprom_parser.py    # Парсер для API Газпром
│   │   ├── yandex_parser.py     # Парсер для Яндекс Карт
│   │   ├── tatneft_parser.py    # Парсер для API Татнефть
│   │   └── parser_factory.py    # Фабрика парсеров
│   ├── orchestrator.py          # Оркестратор парсеров
│   └── __init__.py
├── data/                        # Выходные данные
├── config.py                    # Конфигурация
├── main.py                      # Точка входа
├── requirements.txt             # Зависимости
└── README.md                    # Документация
```

## 🔧 Конфигурация

Настройки находятся в файле `config.py`:

### Добавление новой сети
```python
GAS_STATION_NETWORKS["new_network"] = {
    "name": "Новая сеть",
    "type": "russiabase",  # или "api", "selenium"
    "base_url": "https://example.com/prices",
    "max_pages": 10
}
```

### Настройка задержек
```python
REQUEST_DELAY = (1, 3)  # От 1 до 3 секунд между запросами
RETRY_COUNT = 3         # Количество повторных попыток
```

## 🎯 Примеры использования

### В коде Python
```python
from src.orchestrator import GasStationOrchestrator

# Создаем оркестратор
orchestrator = GasStationOrchestrator(
    networks=['lukoil', 'gazprom'],
    parallel=True,
    max_workers=2
)

# Запускаем парсинг
results = orchestrator.run()

# Получаем сводку
summary = orchestrator.get_summary()
print(f"Всего записей: {summary['total_records']}")
```

### Работа с региональными ценами
```python
from src.parsers.russiabase_parser import RussiaBaseRegionalParser

# Создаем парсер
parser = RussiaBaseRegionalParser()

# Получаем все доступные регионы
all_regions = parser.get_all_regions()
print(f"Доступно регионов: {len(all_regions)}")

# Парсинг конкретного региона
region_id = 77  # Москва
region_name = all_regions[region_id]
prices = parser.get_region_prices(region_id, region_name)

if prices:
    print(f"\nЦены в {prices.region_name}:")
    for fuel_type, price in prices.fuel_prices.items():
        print(f"  {fuel_type}: {price} руб.")
```

### Анализ данных
```python
import polars as pl

# Загружаем данные
df = pl.read_excel("data/all_gas_stations_20241201_120000.xlsx")

# Средние цены по городам
avg_prices = df.group_by("city").agg([
    pl.col("price").mean().alias("avg_price"),
    pl.count().alias("stations_count")
]).sort("avg_price", descending=True)

print(avg_prices)
```

## 📈 Выходные файлы

После выполнения парсинга создаются файлы в директории `data/`:

- `all_gas_stations_YYYYMMDD_HHMMSS.xlsx` - объединенные данные всех сетей
- `[network_name]_YYYYMMDD_HHMMSS.xlsx` - данные конкретной сети
- `regional_prices_YYYYMMDD_HHMMSS.json` - региональные цены (JSON)

## 🚨 Важные примечания

- Соблюдайте задержки между запросами для избежания блокировок
- Для Selenium требуется установленный Google Chrome
- Некоторые источники могут изменять структуру данных
- Региональные цены обновляются реже обычных данных АЗС

## 📝 Лицензия

Проект предназначен для образовательных и исследовательских целей.
