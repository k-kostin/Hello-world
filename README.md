# Парсер цен сетей АЗС

Комплексная система парсинга цен топлива с различных сетей автозаправочных станций в России.

## 🚀 Возможности

- **Поддержка множественных источников**: Лукойл, Газпром, Башнефть, Яндекс Карты и другие
- **Различные методы парсинга**: HTML/JSON extraction, REST API, Selenium WebDriver
- **Автоматическое извлечение регионов**: Полная карта всех 84 регионов России из JSON структуры
- **🆕 Региональный парсинг**: **Средние цены по всем видам топлива по регионам России**
- **Параллельная обработка**: Одновременный парсинг нескольких сетей
- **Унифицированный формат данных**: Все данные приводятся к единой схеме
- **Автоматическое сохранение**: Результаты сохраняются в Excel файлы
- **Детальное логирование**: Отслеживание процесса и ошибок
- **Гибкая конфигурация**: Легко добавлять новые сети

## 📋 Поддерживаемые сети АЗС

| Сеть | Источник | Метод парсинга | Количество регионов |
|------|----------|----------------|-------------------|
| **Лукойл** | russiabase.ru | HTML + JSON + Региональная карта | **84 региона** |
| **Башнефть** | russiabase.ru | HTML + JSON + Региональная карта | **84 региона** |
| **Газпром** | gpnbonus.ru | REST API | Динамически |
| **Яндекс Карты** | yandex.ru/maps | Selenium | По запросу |
| **🆕 Региональные цены** | russiabase.ru | **Специальный региональный парсер** | **ВСЕ 84 региона** |

### 🗺️ Новинка: Автоматическое извлечение карты регионов

Парсер russiabase.ru теперь **автоматически извлекает полную карту всех 84 регионов России** из JSON структуры, встроенной в HTML код страницы. Это обеспечивает:

- ✅ **100% точность названий** регионов (Москва, Санкт-Петербург, Республика Татарстан)
- ✅ **Полное покрытие** всех субъектов РФ
- ✅ **Эффективность** - одним запросом получаем всю карту регионов  
- ✅ **Актуальность** - данные всегда синхронизированы с сайтом

**Пример извлеченной JSON структуры:**
```json
"regions":[
  {"id":"90","value":"Москва"},
  {"id":"99","value":"Санкт-Петербург"},
  {"id":"78","value":"Камчатский край"},
  {"id":"43","value":"Республика Татарстан"}
  // ... все 84 региона
]
```

## 🌍 Региональный парсинг средних цен

### 📊 Что такое региональный парсинг?

**Региональный парсер** - это специальный модуль, который извлекает **средние цены на топливо по регионам России**. В отличие от обычного парсинга конкретных АЗС, региональный парсер получает **усредненные данные по всем заправкам в регионе**.

**Преимущества:**
- 📈 **Средние цены** - не конкретные АЗС, а средние значения по региону
- 🗺️ **Полное покрытие** - все 84 субъекта Российской Федерации
- ⚡ **Быстрая работа** - один запрос = данные по всему региону
- 📊 **Аналитика** - идеально для исследований и статистики
- 💾 **Компактность** - меньший объем данных при большем охвате

### 🚀 Быстрый старт регионального парсинга

#### Вариант 1: Простой запуск (все регионы)
```bash
python regional_parser_final.py --all-regions
```

#### Вариант 2: Популярные регионы
```bash
python regional_parser_final.py --popular-regions
```

#### Вариант 3: Конкретные регионы
```bash
python regional_parser_final.py --regions 77 78 50  # Москва, СПб, Московская область
```

#### Вариант 4: Через основной интерфейс
```bash
python main.py --networks regional_prices
```

### 📋 Детальные команды регионального парсинга

#### Показать все доступные регионы
```bash
python regional_parser_final.py --list-regions
```

#### Ограничить количество регионов
```bash
python regional_parser_final.py --all-regions --max-regions 10
```

#### Настроить задержку между запросами
```bash
python regional_parser_final.py --popular-regions --delay 2.0
```

#### Подробное логирование
```bash
python regional_parser_final.py --all-regions --verbose
```

#### Интегрированный режим (через оркестратор)
```bash
python regional_parser_final.py --popular-regions --use-orchestrator
```

### 💡 Примеры использования в коде

#### Базовый пример - все регионы
```python
from src.parsers.russiabase_parser import RussiaBaseRegionalParser

# Создаем парсер
parser = RussiaBaseRegionalParser()

# Получаем все доступные регионы
all_regions = parser.get_all_regions()
print(f"Доступно регионов: {len(all_regions)}")

# Конвертируем в список для парсинга
regions_list = [
    {'id': region_id, 'name': region_name}
    for region_id, region_name in all_regions.items()
]

# Парсим все регионы
results = parser.parse_multiple_regions(regions_list)

# Выводим результаты
for result in results:
    if result.status == 'success':
        print(f"\n{result.region_name}:")
        for fuel_type, price in result.fuel_prices.items():
            print(f"  {fuel_type}: {price:.2f} руб/л")
```

#### Пример - популярные регионы
```python
from config import REGIONS_CONFIG

# Популярные регионы из конфигурации
popular_regions_ids = REGIONS_CONFIG['default_regions']  # [77, 78, 50, 40, 23, 66]

# Получаем названия регионов
all_regions = parser.get_all_regions()
popular_regions = [
    {'id': region_id, 'name': all_regions[region_id]}
    for region_id in popular_regions_ids
    if region_id in all_regions
]

# Парсим популярные регионы
results = parser.parse_multiple_regions(popular_regions)
```

#### Пример - анализ средних цен
```python
# Парсим данные
results = parser.parse_multiple_regions(regions_list)

# Группируем цены по типам топлива
fuel_stats = {}
for result in results:
    if result.status == 'success' and result.fuel_prices:
        for fuel_type, price in result.fuel_prices.items():
            if fuel_type not in fuel_stats:
                fuel_stats[fuel_type] = []
            fuel_stats[fuel_type].append(price)

# Вычисляем средние цены по России
print("Средние цены по России:")
for fuel_type, prices in fuel_stats.items():
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    print(f"{fuel_type}: среднее {avg_price:.2f}, мин {min_price:.2f}, макс {max_price:.2f} руб/л")
```

#### Пример - сохранение в файл
```python
import json
from datetime import datetime

# Конвертируем результаты в JSON
json_data = []
for result in results:
    json_data.append({
        'region_id': result.region_id,
        'region_name': result.region_name,
        'fuel_prices': result.fuel_prices,
        'timestamp': result.timestamp,
        'status': result.status
    })

# Сохраняем в файл
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"regional_prices_{timestamp}.json"

with open(filename, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)
```

### 📊 Структура данных регионального парсинга

#### Формат результата для каждого региона:
```python
@dataclass
class RegionalPriceResult:
    region_id: int              # ID региона (77 для Москвы)
    region_name: str            # Название ("Москва")
    fuel_prices: Dict[str, float]  # {"АИ-92": 45.50, "АИ-95": 48.20, ...}
    url: str                    # URL запроса
    timestamp: str              # Время получения данных
    status: str                 # 'success' или 'error'
    error_message: str = None   # Сообщение об ошибке (если есть)
```

#### Пример данных fuel_prices:
```json
{
  "АИ-92": 45.50,
  "АИ-95": 48.20,
  "АИ-98": 52.10,
  "ДТ": 49.80,
  "Пропан": 26.30
}
```

### 🗂️ Выходные файлы регионального парсинга

После выполнения регионального парсинга создаются файлы:

#### Standalone режим:
- `regional_prices_YYYYMMDD_HHMMSS.json` - результаты в JSON формате

#### Оркестратор режим:
- `data/regional_prices_YYYYMMDD_HHMMSS.xlsx` - результаты в Excel
- `data/all_gas_stations_YYYYMMDD_HHMMSS.xlsx` - объединенные данные (если есть другие сети)

#### Специальные тестовые файлы:
- `test_regional_prices_optimized.xlsx` - тестовые результаты с листами:
  - **Regional_Prices** - цены по регионам
  - **All_Regions_Map** - карта всех 84 регионов
  - **Statistics** - статистика парсинга
  - **Details** - детальная информация

### ⚙️ Конфигурация регионального парсинга

В файле `config.py`:

```python
# Основная конфигурация
GAS_STATION_NETWORKS["regional_prices"] = {
    "name": "Региональные цены",
    "type": "russiabase_regional",
    "base_url": "https://russiabase.ru/prices",
    "delay": 1.5,                    # Задержка между запросами
    "max_regions": None,             # Максимум регионов (None = без ограничений)
    "description": "Средние цены на топливо по регионам России"
}

# Настройки регионов
REGIONS_CONFIG = {
    "default_regions": [77, 78, 50, 40, 23, 66],  # Популярные регионы
    "max_regions_per_network": 10,                 # Лимит на одну сеть
    "enable_multi_region_parsing": True            # Множественный парсинг
}
```

## 🛠 Установка

### Предварительные требования

- Python 3.8+
- Google Chrome (для Selenium)

### Установка зависимостей

```bash
# Клонируем репозиторий
git clone <repository-url>
cd gas-station-parser

# Устанавливаем зависимости
pip install -r requirements.txt
```

### Основные библиотеки

- `polars` - быстрая обработка данных
- `requests` - HTTP запросы
- `beautifulsoup4` - парсинг HTML
- `selenium` - автоматизация браузера
- `loguru` - логирование
- `openpyxl` - работа с Excel

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

### 🆕 Региональный парсинг средних цен

```bash
# Все регионы России (84 региона)
python regional_parser_final.py --all-regions

# Популярные регионы (Москва, СПб, МО и др.)
python regional_parser_final.py --popular-regions

# Конкретные регионы
python regional_parser_final.py --regions 77 78 50

# Через основной интерфейс
python main.py --networks regional_prices
```

### Параллельный парсинг

```bash
python main.py --networks lukoil bashneft --parallel --workers 2
```

### Подробное логирование

```bash
python main.py --all --verbose
python regional_parser_final.py --all-regions --verbose
```

## 📊 Структура выходных данных

### Основные сети АЗС

Все данные приводятся к единой схеме:

| Поле | Тип | Описание |
|------|-----|----------|
| `station_id` | str | Уникальный ID станции |
| `network_name` | str | Название сети АЗС |
| `station_name` | str | Название станции |
| `address` | str | Полный адрес |
| `city` | str | Город |
| `region` | str | Регион |
| `region_id` | int | ID региона |
| `latitude` | float | Широта (если доступно) |
| `longitude` | float | Долгота (если доступно) |
| `fuel_type` | str | Тип топлива (АИ-92, АИ-95, ДТ и т.д.) |
| `price` | float | Цена за литр |
| `currency` | str | Валюта (обычно RUB) |
| `last_updated` | str | Время последнего обновления |
| `source` | str | Источник данных |

### 🆕 Региональные средние цены

| Поле | Тип | Описание |
|------|-----|----------|
| `region_id` | int | ID региона (77 для Москвы) |
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
│   │   └── parser_factory.py    # Фабрика парсеров
│   ├── orchestrator.py          # Оркестратор парсеров
│   └── __init__.py
├── data/                        # Выходные данные
├── logs/                        # Логи
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

### Работа с картой регионов russiabase.ru

```python
from src.parsers.russiabase_parser import RussiaBaseRegionalParser

# Создаем парсер
parser = RussiaBaseRegionalParser()

# Автоматически получаем все 84 региона из JSON структуры
all_regions = parser.get_all_regions()
print(f"Доступно регионов: {len(all_regions)}")

# Примеры регионов
for region_id, region_name in list(all_regions.items())[:5]:
    print(f"ID {region_id}: {region_name}")

# Парсинг конкретного региона с правильным названием
region_id = 90  # Москва
correct_name = all_regions[region_id]
prices = parser.get_region_prices(region_id, correct_name)

if prices:
    print(f"\nЦены в {prices.region_name}:")
    for fuel_type, price in prices.fuel_prices.items():
        print(f"  {fuel_type}: {price} руб.")

# Парсинг нескольких регионов
test_regions = [
    {'id': 90, 'name': 'Москва'},
    {'id': 99, 'name': 'Санкт-Петербург'},
    {'id': 78, 'name': 'Камчатский край'}
]
results = parser.parse_multiple_regions(test_regions)
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

## 📈 Результаты

После успешного выполнения создаются файлы:

- `data/lukoil_20241201_120000.xlsx` - данные по Лукойл
- `data/gazprom_20241201_120000.xlsx` - данные по Газпром
- `data/all_gas_stations_20241201_120000.xlsx` - объединенные данные
- `logs/gas_stations_parsing_20241201_120000.log` - лог выполнения

### Специальные файлы для russiabase.ru

При тестировании регионального парсера создаются дополнительные файлы:

- `test_regional_prices_optimized.xlsx` - результаты тестирования с тремя листами:
  - **Regional_Prices** - цены по тестовым регионам
  - **All_Regions_Map** - полная карта всех 84 регионов с ID
  - **Statistics** - статистика парсинга
  - **Details** - детальная информация о каждом запросе
- `REGIONS_ID_MAPPING_RESEARCH.md` - исследование карты регионов с техническими деталями

## ⚙️ Особенности работы

### Методы парсинга

1. **RussiaBase парсер** (`russiabase`)
   - **Автоматическое извлечение карты регионов** из JSON структуры в HTML
   - Извлекает JSON-LD данные из HTML для цен
   - **84 региона России** с правильными названиями
   - Поддерживает пагинацию
   - Кэширование карты регионов для оптимизации
   - Используется для Лукойл, Башнефть

2. **API парсер** (`api`)
   - Работает с REST API
   - Получает структурированные данные
   - Используется для Газпром

3. **Selenium парсер** (`selenium`)
   - Автоматизация браузера
   - Обход JavaScript защиты
   - Используется для Яндекс Карт

### Обработка ошибок

- Автоматические повторные попытки
- Пропуск проблемных записей
- Детальное логирование ошибок
- Graceful degradation

## 🚨 Важные замечания

1. **Соблюдение robots.txt** - проект уважает ограничения сайтов
2. **Задержки между запросами** - предотвращение перегрузки серверов
3. **User-Agent** - используются реалистичные заголовки
4. **Мониторинг нагрузки** - контроль частоты запросов

## 🛡️ Ограничения и этика

- Используйте парсер ответственно
- Соблюдайте ToS сайтов
- Не перегружайте серверы частыми запросами
- Данные предназначены для аналитических целей

## 🐛 Устранение неполадок

### Ошибки Selenium

```bash
# Обновите Chrome драйвер
pip install --upgrade webdriver-manager
```

### Ошибки сети

```bash
# Проверьте подключение к интернету
# Увеличьте таймауты в config.py
TIMEOUT = 60
```

### Ошибки памяти

```bash
# Уменьшите количество воркеров
python main.py --networks lukoil --workers 1
```

## 📚 Дополнительные ресурсы

- **[📍 ПОЛНОЕ РУКОВОДСТВО ПО РЕГИОНАЛЬНОМУ ПАРСИНГУ](REGIONAL_PARSING_GUIDE.md)** - **детальное руководство по парсингу средних цен**
- [Архитектура проекта](ARCHITECTURE.md) - техническая документация
- [Примеры использования](example_usage.py) - готовые примеры кода
- [Финализация проекта](FINALIZATION_REPORT.md) - отчет о завершении
- [Интеграция регионов](REGIONS_INTEGRATION.md) - техническая документация

## 🎯 Краткая сводка: Как парсить средние цены по регионам

**📋 Быстрые команды:**

```bash
# Все 84 региона России
python regional_parser_final.py --all-regions

# Популярные регионы (Москва, СПб, МО и др.)
python regional_parser_final.py --popular-regions

# Конкретные регионы (Москва=77, СПб=78, МО=50)
python regional_parser_final.py --regions 77 78 50

# Через основной интерфейс
python main.py --networks regional_prices

# Показать все доступные регионы
python regional_parser_final.py --list-regions
```

**📊 Результат:** Средние цены на топливо (АИ-92, АИ-95, АИ-98, ДТ, Пропан) по каждому региону России.

**📄 Подробные инструкции:** [REGIONAL_PARSING_GUIDE.md](REGIONAL_PARSING_GUIDE.md)

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Добавьте новый парсер в `src/parsers/`
4. Обновите конфигурацию
5. Добавьте тесты
6. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE

## 👥 Авторы

- Основной разработчик: [Ваше имя]
- Контрибьюторы: см. CONTRIBUTORS.md

---

**Примечание**: Этот проект создан для образовательных и аналитических целей. Используйте его ответственно и в соответствии с правилами использования источников данных.
