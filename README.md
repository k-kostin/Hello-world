# Парсер цен сетей АЗС

Комплексная система парсинга цен топлива с различных сетей автозаправочных станций в России.

## 🚀 Возможности

- **Поддержка множественных источников**: Лукойл, Газпром, Башнефть, Яндекс Карты и другие
- **Различные методы парсинга**: HTML/JSON extraction, REST API, Selenium WebDriver
- **Параллельная обработка**: Одновременный парсинг нескольких сетей
- **Унифицированный формат данных**: Все данные приводятся к единой схеме
- **Автоматическое сохранение**: Результаты сохраняются в Excel файлы
- **Детальное логирование**: Отслеживание процесса и ошибок
- **Гибкая конфигурация**: Легко добавлять новые сети

## 📋 Поддерживаемые сети АЗС

| Сеть | Источник | Метод парсинга | Количество страниц |
|------|----------|----------------|-------------------|
| **Лукойл** | russiabase.ru | HTML + JSON-LD | ~98 страниц |
| **Башнефть** | russiabase.ru | HTML + JSON-LD | ~24 страницы |
| **Газпром** | gpnbonus.ru | REST API | Динамически |
| **Яндекс Карты** | yandex.ru/maps | Selenium | По запросу |

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

### Параллельный парсинг

```bash
python main.py --networks lukoil bashneft --parallel --workers 2
```

### Подробное логирование

```bash
python main.py --all --verbose
```

## 📊 Структура выходных данных

Все данные приводятся к единой схеме:

| Поле | Тип | Описание |
|------|-----|----------|
| `station_id` | str | Уникальный ID станции |
| `network_name` | str | Название сети АЗС |
| `station_name` | str | Название станции |
| `address` | str | Полный адрес |
| `city` | str | Город |
| `latitude` | float | Широта (если доступно) |
| `longitude` | float | Долгота (если доступно) |
| `fuel_type` | str | Тип топлива (АИ-92, АИ-95, ДТ и т.д.) |
| `price` | float | Цена за литр |
| `currency` | str | Валюта (обычно RUB) |
| `last_updated` | str | Время последнего обновления |
| `source` | str | Источник данных |

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

## ⚙️ Особенности работы

### Методы парсинга

1. **RussiaBase парсер** (`russiabase`)
   - Извлекает JSON-LD данные из HTML
   - Поддерживает пагинацию
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
