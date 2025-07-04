# AZS Prices Parser

Сбор цен на топливо различных сетей АЗС России.

## Структура проекта

```
azs_prices/            # python-пакет с реализацией парсеров
  base.py              # базовый интерфейс
  parsers/             # конкретные реализации
      russiabase.py    # универсальный парсер для russiabase.ru
      gazprom.py       # API Газпромнефть
      tatneft.py       # API Татнефть
      yandex.py        # скрейпер Яндекс.Карт (экспериментально)
run_parser.py          # CLI-утилита
notebooks/             # исторические Jupyter-ноутбуки (для справки)
```

## Установка зависимостей

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Использование

1. Сохранить данные по Bashneft (brand 292) c первых 10 страниц:

```bash
python run_parser.py bashneft -p 10
```

2. Получить цены Газпромнефть из официального API:

```bash
python run_parser.py gazprom
```

3. Скрейпинг Яндекс.Карт (понадобится Google Chrome):

```bash
python run_parser.py yandex
```

CSV-файлы сохраняются в директории `data/`.

## Подходы, реализованные в проекте

| Сеть | Источник | Особенности |
|------|----------|-------------|
| Bashneft, Lukoil, Нефтьмагистраль | russiabase.ru | Разбор JSON-LD внутри `<script>` тегов, пагинация. |
| Gazprom | gpnbonus.ru API | Открытый REST-API, требуется два запроса: список АЗС и детали каждой станции. |
| Tatneft | api.gs.tatneft.ru | Единый JSON со списком АЗС и ценами. |
| Yandex (разные бренды) | yandex.ru/maps | Парсинг через Selenium, имитируется прокрутка / переходы. |

## TODO

- Юнит-тесты.
- Dockerfile для воспроизводимого окружения.
- Хранение истории цен в базе данных.
