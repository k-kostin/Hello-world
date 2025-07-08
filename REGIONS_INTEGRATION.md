# Интеграция системы управления регионами

Добавлена полноценная система управления регионами России для работы с сайтом russiabase.ru

## Что добавлено

### 1. Генератор таблицы регионов (`generate_regions.py`)
- Автоматическое получение списка регионов с russiabase.ru
- Парсинг региональных данных с различными стратегиями
- Fallback на встроенный список из 85 регионов России
- Экспорт в markdown с таблицей и JSON форматом

### 2. Система управления регионами (`src/regions.py`)
- Класс `RegionManager` для работы с регионами
- Автоматическая загрузка из `regions.md` файла
- API для поиска, фильтрации и валидации регионов
- Утилитарные функции для быстрого доступа

### 3. Интеграция в основной проект
- Обновленная конфигурация с поддержкой регионов
- Расширенная схема выходных данных
- Готовность к использованию в парсерах

## Созданные файлы

| Файл | Описание |
|------|----------|
| `regions.md` | Таблица регионов с ID и URL (85 регионов) |
| `generate_regions.py` | Скрипт генерации таблицы регионов |
| `src/regions.py` | Модуль управления регионами |
| `example_regions.py` | Демонстрация функциональности |
| `REGIONS_INTEGRATION.md` | Документация (этот файл) |

## Использование

### Базовые операции
```python
from src.regions import region_manager, get_region_id_by_name

# Получить все регионы
regions = region_manager.get_all_regions()

# Найти регион по ID
region = region_manager.get_region_by_id(40)  # Курская область

# Найти ID региона по названию
moscow_id = get_region_id_by_name("Москва")  # Вернет 77

# Получить URL для парсинга
url = region_manager.get_region_url(40)
# https://russiabase.ru/prices?region=40
```

### Поиск и фильтрация
```python
# Поиск по части названия
regions = region_manager.search_regions("област")

# Получить регионы по типу
republics = region_manager.get_regions_by_type("республика")
regions = region_manager.get_regions_by_type("область") 
cities = region_manager.get_regions_by_type("город")

# Популярные регионы
popular = region_manager.get_popular_regions()
```

### Валидация
```python
from src.regions import is_valid_region_id

# Проверить валидность ID
is_valid = is_valid_region_id(40)  # True
is_invalid = is_valid_region_id(999)  # False
```

## Интеграция с парсерами

### Обновленная конфигурация
Все сети типа `russiabase` теперь поддерживают регионы:
```python
GAS_STATION_NETWORKS = {
    "lukoil": {
        "supports_regions": True,
        # ...
    }
}
```

### Расширенная схема данных
```python
OUTPUT_SCHEMA = {
    # ... существующие поля ...
    "region": str,      # Название региона
    "region_id": int,   # ID региона
}
```

### Региональные настройки
```python
REGIONS_CONFIG = {
    "regions_file": "regions.md",
    "default_regions": [77, 78, 50, 40, 23, 66, 96],
    "enable_region_filtering": True,
    "enable_multi_region_parsing": True,
    "max_regions_per_network": 10
}
```

## Примеры URL для парсинга

| Регион | ID | URL |
|--------|----|----- |
| Москва | 77 | https://russiabase.ru/prices?region=77 |
| Санкт-Петербург | 78 | https://russiabase.ru/prices?region=78 |
| Курская область | 40 | https://russiabase.ru/prices?region=40 |
| Московская область | 50 | https://russiabase.ru/prices?region=50 |

### Парсинг конкретной сети в регионе
```bash
# Лукойл в Курской области
https://russiabase.ru/prices?brand=119&region=40

# Башнефть в Москве  
https://russiabase.ru/prices?brand=292&region=77
```

## Статистика регионов

- **Всего регионов**: 85
- **Республики**: 22
- **Области**: 47  
- **Края**: 9
- **Города**: 3 (Москва, СПб, Севастополь)
- **Округа**: 4

## Тестирование

Запустите демонстрацию:
```bash
python3 example_regions.py
```

Сгенерируйте новую таблицу регионов:
```bash
python3 generate_regions.py
```

## Дальнейшее развитие

1. **Интеграция в парсеры**: Добавить поддержку региональных параметров в существующие парсеры
2. **Кэширование**: Добавить кэширование региональных данных для повышения производительности
3. **Автообновление**: Периодическое обновление таблицы регионов
4. **Географические данные**: Добавить координаты и административное деление
5. **Валидация данных**: Проверка актуальности региональных ссылок

## Примеры использования в парсерах

### Парсинг всех популярных регионов
```python
from src.regions import region_manager

popular_regions = region_manager.get_popular_regions()
for region in popular_regions:
    url = f"https://russiabase.ru/prices?brand=119&region={region['id']}"
    # Парсить URL...
```

### Парсинг конкретного региона
```python
from src.regions import get_region_id_by_name, get_region_url_by_id

# По названию
region_id = get_region_id_by_name("Курская область")
if region_id:
    url = get_region_url_by_id(region_id)
    # Парсить URL...
```

Система готова к использованию и легко расширяется для добавления новых региональных функций.