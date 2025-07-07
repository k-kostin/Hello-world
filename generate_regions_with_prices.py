#!/usr/bin/env python3
"""
Генератор таблицы регионов России с ценами на топливо на основе russiabase.ru
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Tuple, Any, Optional
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Попытка импорта loguru, если не установлен - используем стандартный logging
try:
    from loguru import logger
    LOGURU_AVAILABLE = True
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    logger = logging.getLogger(__name__)
    LOGURU_AVAILABLE = False

# Настройка логирования
if LOGURU_AVAILABLE:
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        level="INFO"
    )

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


class RegionPriceParser:
    """Парсер для получения списка регионов с ценами на топливо с russiabase.ru"""
    
    def __init__(self, timeout: int = 30, retries: int = 3, offline_mode: bool = False, max_workers: int = 5):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.base_url = "https://russiabase.ru/prices"
        self.timeout = timeout
        self.retries = retries
        self.offline_mode = offline_mode
        self.max_workers = max_workers
        
    def fetch_regions_with_prices(self, sample_regions: bool = False) -> List[Dict[str, Any]]:
        """Получает список всех регионов с ценами на топливо"""
        if self.offline_mode:
            logger.info("Запущен offline режим - используем встроенный список регионов без цен")
            return self._get_known_regions_offline()
            
        logger.info("Получение списка регионов с ценами с russiabase.ru...")
        
        # Сначала получаем список регионов
        regions = self._get_regions_list()
        
        if sample_regions:
            # Для демонстрации берем только популярные регионы
            popular_ids = [77, 78, 50, 40, 23, 66, 52, 16]  # Москва, СПб, Московская, Курская и др.
            regions = [r for r in regions if r['id'] in popular_ids]
            logger.info(f"Режим выборки: обрабатываем {len(regions)} популярных регионов")
        
        # Получаем цены для каждого региона
        regions_with_prices = self._fetch_prices_for_regions(regions)
        
        return regions_with_prices
    
    def _get_regions_list(self) -> List[Dict[str, Any]]:
        """Получает базовый список регионов"""
        logger.info("Получение базового списка регионов...")
        
        # Используем встроенный список регионов
        known_regions = [
            (1, "Республика Адыгея"), (2, "Республика Алтай"), (3, "Республика Башкортостан"),
            (4, "Республика Бурятия"), (5, "Республика Дагестан"), (6, "Республика Ингушетия"),
            (7, "Кабардино-Балкарская Республика"), (8, "Республика Калмыкия"), 
            (9, "Карачаево-Черкесская Республика"), (10, "Республика Карелия"),
            (11, "Республика Коми"), (12, "Республика Марий Эл"), (13, "Республика Мордовия"),
            (14, "Республика Саха (Якутия)"), (15, "Республика Северная Осетия — Алания"),
            (16, "Республика Татарстан"), (17, "Республика Тыва"), (18, "Удмуртская Республика"),
            (19, "Республика Хакасия"), (20, "Чеченская Республика"), (21, "Чувашская Республика"),
            (22, "Алтайский край"), (23, "Краснодарский край"), (24, "Красноярский край"),
            (25, "Приморский край"), (26, "Ставропольский край"), (27, "Хабаровский край"),
            (28, "Амурская область"), (29, "Архангельская область"), (30, "Астраханская область"),
            (31, "Белгородская область"), (32, "Брянская область"), (33, "Владимирская область"),
            (34, "Волгоградская область"), (35, "Вологодская область"), (36, "Воронежская область"),
            (37, "Ивановская область"), (38, "Иркутская область"), (39, "Калининградская область"),
            (40, "Курская область"), (41, "Калужская область"), (42, "Камчатский край"),
            (43, "Кемеровская область"), (44, "Кировская область"), (45, "Костромская область"),
            (46, "Курганская область"), (47, "Ленинградская область"), (48, "Липецкая область"),
            (49, "Магаданская область"), (50, "Московская область"), (51, "Мурманская область"),
            (52, "Нижегородская область"), (53, "Новгородская область"), (54, "Новосибирская область"),
            (55, "Омская область"), (56, "Оренбургская область"), (57, "Орловская область"),
            (58, "Пензенская область"), (59, "Пермский край"), (60, "Псковская область"),
            (61, "Ростовская область"), (62, "Рязанская область"), (63, "Самарская область"),
            (64, "Саратовская область"), (65, "Сахалинская область"), (66, "Свердловская область"),
            (67, "Смоленская область"), (68, "Тамбовская область"), (69, "Тверская область"),
            (70, "Томская область"), (71, "Тульская область"), (72, "Тюменская область"),
            (73, "Ульяновская область"), (74, "Челябинская область"), (75, "Забайкальский край"),
            (76, "Ярославская область"), (77, "Москва"), (78, "Санкт-Петербург"),
            (79, "Еврейская автономная область"), (80, "Ненецкий автономный округ"),
            (81, "Ханты-Мансийский автономный округ — Югра"), (82, "Чукотский автономный округ"),
            (83, "Ямало-Ненецкий автономный округ"), (84, "Республика Крым"), (85, "Севастополь")
        ]
        
        regions = []
        for region_id, region_name in known_regions:
            regions.append({
                'id': region_id,
                'name': region_name,
                'url': f"{self.base_url}?region={region_id}"
            })
        
        return regions
    
    def _fetch_prices_for_regions(self, regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Получает цены для списка регионов параллельно"""
        logger.info(f"Получение цен для {len(regions)} регионов...")
        
        regions_with_prices = []
        
        # Параллельная обработка регионов
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_region = {
                executor.submit(self._fetch_region_prices, region): region 
                for region in regions
            }
            
            completed = 0
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                completed += 1
                
                try:
                    region_with_prices = future.result()
                    if region_with_prices:
                        regions_with_prices.append(region_with_prices)
                        logger.info(f"✅ {completed}/{len(regions)} - {region['name']}")
                    else:
                        logger.warning(f"❌ {completed}/{len(regions)} - {region['name']} (нет данных)")
                        
                except Exception as e:
                    logger.error(f"❌ {completed}/{len(regions)} - {region['name']}: {e}")
                
                # Добавляем небольшую задержку между запросами
                time.sleep(0.5)
        
        # Сортируем по названию
        regions_with_prices.sort(key=lambda x: x['name'])
        
        logger.info(f"Успешно получены цены для {len(regions_with_prices)} регионов")
        return regions_with_prices
    
    def _fetch_region_prices(self, region: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Получает цены на топливо для конкретного региона"""
        for attempt in range(self.retries):
            try:
                response = self.session.get(region['url'], timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                prices = self._parse_fuel_prices(soup)
                
                if prices:
                    region_data = region.copy()
                    region_data.update(prices)
                    return region_data
                    
            except requests.exceptions.Timeout:
                if attempt < self.retries - 1:
                    time.sleep(2)
                    continue
            except Exception as e:
                if attempt < self.retries - 1:
                    time.sleep(2)
                    continue
                    
        return None
    
    def _parse_fuel_prices(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Парсит цены на топливо со страницы региона"""
        prices = {}
        
        # Ищем таблицу с ценами или блок с информацией о ценах
        # Вариант 1: Ищем текст "средняя цена на топливо"
        price_text = soup.get_text()
        
        # Паттерны для поиска цен
        fuel_patterns = {
            'ai_92': [r'Аи-92[+\s]*(\d+[\.,]\d+)', r'АИ-92[+\s]*(\d+[\.,]\d+)', r'92[+\s]*(\d+[\.,]\d+)'],
            'ai_95': [r'Аи-95[+\s]*(\d+[\.,]\d+)', r'АИ-95[+\s]*(\d+[\.,]\d+)', r'95[+\s]*(\d+[\.,]\d+)'],
            'ai_98': [r'Аи-98[+\s]*(\d+[\.,]\d+)', r'АИ-98[+\s]*(\d+[\.,]\d+)', r'98[+\s]*(\d+[\.,]\d+)'],
            'ai_100': [r'Аи-100[+\s]*(\d+[\.,]\d+)', r'АИ-100[+\s]*(\d+[\.,]\d+)', r'100[+\s]*(\d+[\.,]\d+)'],
            'diesel': [r'ДТ[+\s]*(\d+[\.,]\d+)', r'дизель[+\s]*(\d+[\.,]\d+)', r'Дизель[+\s]*(\d+[\.,]\d+)'],
            'gas': [r'Газ[+\s]*(\d+[\.,]\d+)', r'газ[+\s]*(\d+[\.,]\d+)', r'ГАЗ[+\s]*(\d+[\.,]\d+)']
        }
        
        # Ищем цены в тексте
        for fuel_type, patterns in fuel_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, price_text, re.IGNORECASE)
                if matches:
                    try:
                        # Берем первое найденное значение и конвертируем
                        price_str = matches[0].replace(',', '.')
                        prices[fuel_type] = float(price_str)
                        break
                    except (ValueError, IndexError):
                        continue
        
        # Альтернативный способ - ищем в HTML элементах
        if not prices:
            prices = self._parse_prices_from_elements(soup)
        
        # Вычисляем среднюю цену, если есть данные
        if prices:
            valid_prices = [price for price in prices.values() if isinstance(price, (int, float)) and price > 0]
            if valid_prices:
                prices['avg_price'] = round(statistics.mean(valid_prices), 2)
                prices['min_price'] = round(min(valid_prices), 2)
                prices['max_price'] = round(max(valid_prices), 2)
                prices['price_count'] = len(valid_prices)
        
        return prices
    
    def _parse_prices_from_elements(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Альтернативный парсинг цен из HTML элементов"""
        prices = {}
        
        # Ищем элементы, которые могут содержать цены
        price_elements = soup.find_all(['td', 'span', 'div'], string=re.compile(r'\d+[\.,]\d+'))
        
        for element in price_elements:
            text = element.get_text(strip=True)
            # Простой поиск чисел, похожих на цены на топливо (от 30 до 200 рублей)
            price_match = re.search(r'(\d+[\.,]\d+)', text)
            if price_match:
                try:
                    price = float(price_match.group(1).replace(',', '.'))
                    if 30 <= price <= 200:  # Разумный диапазон цен на топливо
                        # Определяем тип топлива по контексту
                        context = element.get_text().lower()
                        if 'аи-92' in context or '92' in context:
                            prices['ai_92'] = price
                        elif 'аи-95' in context or '95' in context:
                            prices['ai_95'] = price
                        elif 'аи-98' in context or '98' in context:
                            prices['ai_98'] = price
                        elif 'дт' in context or 'дизель' in context:
                            prices['diesel'] = price
                        elif 'газ' in context:
                            prices['gas'] = price
                except ValueError:
                    continue
        
        return prices
    
    def _get_known_regions_offline(self) -> List[Dict[str, Any]]:
        """Возвращает список регионов без цен (offline режим)"""
        regions = self._get_regions_list()
        
        # Добавляем пустые данные о ценах
        for region in regions:
            region.update({
                'ai_92': None,
                'ai_95': None,
                'ai_98': None,
                'ai_100': None,
                'diesel': None,
                'gas': None,
                'avg_price': None,
                'min_price': None,
                'max_price': None,
                'price_count': 0
            })
        
        return regions
    
    def save_to_markdown(self, regions: List[Dict[str, Any]], filename: str = "regions_with_prices.md"):
        """Сохраняет список регионов с ценами в markdown файл"""
        logger.info(f"Сохранение {len(regions)} регионов с ценами в файл {filename}")
        
        # Подсчитываем статистику
        regions_with_prices = [r for r in regions if r.get('price_count', 0) > 0]
        
        content = f"""# Регионы России с ценами на топливо - RussiaBase.ru

Таблица регионов с ID, названиями и актуальными ценами на топливо

Сгенерировано: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Общая информация

- Всего регионов: {len(regions)}
- Регионов с ценами: {len(regions_with_prices)}
- Базовый URL: https://russiabase.ru/prices
- URL региона: https://russiabase.ru/prices?region={{ID}}

## Сводка по ценам

"""
        
        if regions_with_prices:
            all_avg_prices = [r['avg_price'] for r in regions_with_prices if r.get('avg_price')]
            if all_avg_prices:
                content += f"""- Средняя цена по всем регионам: {statistics.mean(all_avg_prices):.2f} руб/л
- Минимальная цена: {min(all_avg_prices):.2f} руб/л  
- Максимальная цена: {max(all_avg_prices):.2f} руб/л
"""
        
        content += f"""
## Таблица регионов с ценами

| ID | Название региона | АИ-92 | АИ-95 | АИ-98 | ДТ | Газ | Средняя | URL |
|----|------------------|-------|-------|-------|----|----|---------|-----|
"""
        
        for region in regions:
            ai_92 = f"{region.get('ai_92', 0):.2f}" if region.get('ai_92') else "—"
            ai_95 = f"{region.get('ai_95', 0):.2f}" if region.get('ai_95') else "—"
            ai_98 = f"{region.get('ai_98', 0):.2f}" if region.get('ai_98') else "—"
            diesel = f"{region.get('diesel', 0):.2f}" if region.get('diesel') else "—"
            gas = f"{region.get('gas', 0):.2f}" if region.get('gas') else "—"
            avg = f"{region.get('avg_price', 0):.2f}" if region.get('avg_price') else "—"
            
            content += f"| {region['id']} | {region['name']} | {ai_92} | {ai_95} | {ai_98} | {diesel} | {gas} | {avg} | {region['url']} |\n"
        
        content += f"""
## Использование

```python
# Пример получения данных о регионе с ценами
region_data = {{
    'id': 40,
    'name': 'Курская область',
    'ai_92': 57.50,
    'ai_95': 62.30,
    'diesel': 71.00,
    'avg_price': 63.60,
    'url': 'https://russiabase.ru/prices?region=40'
}}
```

## JSON формат

```json
[
"""
        
        for i, region in enumerate(regions):
            comma = "," if i < len(regions) - 1 else ""
            region_json = {
                'id': region['id'],
                'name': region['name'],
                'ai_92': region.get('ai_92'),
                'ai_95': region.get('ai_95'), 
                'ai_98': region.get('ai_98'),
                'ai_100': region.get('ai_100'),
                'diesel': region.get('diesel'),
                'gas': region.get('gas'),
                'avg_price': region.get('avg_price'),
                'url': region['url']
            }
            
            content += f'  {str(region_json).replace("None", "null")}{comma}\n'
            
        content += "]\n```\n"
        
        # Добавляем информацию о методологии
        content += f"""
## Методология

### Источники данных
- Основной источник: russiabase.ru
- Парсинг актуальных цен по регионам
- Автоматический расчет средних значений

### Типы топлива
- **АИ-92** - бензин Аи-92
- **АИ-95** - бензин Аи-95  
- **АИ-98** - бензин Аи-98
- **ДТ** - дизельное топливо
- **Газ** - природный газ (метан)

### Обозначения
- **—** - данные недоступны
- **Средняя** - среднее арифметическое доступных цен по региону

## Устранение неполадок

```bash
# Полный парсинг всех регионов (медленно)
python generate_regions_with_prices.py

# Быстрый режим - только популярные регионы
python generate_regions_with_prices.py --sample

# Offline режим без цен
python generate_regions_with_prices.py --offline

# Настройка производительности
python generate_regions_with_prices.py --workers 10 --timeout 60
```
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Регионы с ценами сохранены в файл {filename}")


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Генератор таблицы регионов России с ценами на топливо для russiabase.ru",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python generate_regions_with_prices.py                # Полный парсинг всех регионов
  python generate_regions_with_prices.py --sample       # Только популярные регионы
  python generate_regions_with_prices.py --offline      # Offline режим (без цен)
  python generate_regions_with_prices.py --workers 10   # 10 параллельных потоков
        """
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout для HTTP запросов в секундах (по умолчанию 30)"
    )
    
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Количество попыток подключения (по умолчанию 3)"
    )
    
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Offline режим - только список регионов без цен"
    )
    
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Режим выборки - только популярные регионы (быстрее)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Количество параллельных потоков для парсинга (по умолчанию 5)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="regions_with_prices.md",
        help="Имя выходного файла (по умолчанию regions_with_prices.md)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробное логирование"
    )
    
    return parser.parse_args()


def main():
    """Главная функция"""
    args = parse_arguments()
    
    # Настройка уровня логирования
    if args.verbose and LOGURU_AVAILABLE:
        logger.remove()
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
            level="DEBUG"
        )
    
    logger.info("🚀 Запуск генератора таблицы регионов с ценами")
    
    if args.offline:
        logger.info("🌐 Offline режим: только список регионов")
    elif args.sample:
        logger.info("📊 Режим выборки: популярные регионы")
    else:
        logger.info("🗺️ Полный режим: все регионы с ценами")
        logger.warning("⚠️ Это может занять 10-15 минут...")
    
    parser = RegionPriceParser(
        timeout=args.timeout,
        retries=args.retries,
        offline_mode=args.offline,
        max_workers=args.workers
    )
    
    try:
        start_time = time.time()
        regions = parser.fetch_regions_with_prices(sample_regions=args.sample)
        end_time = time.time()
        
        if regions:
            parser.save_to_markdown(regions, args.output)
            
            # Статистика
            regions_with_prices = [r for r in regions if r.get('price_count', 0) > 0]
            elapsed = end_time - start_time
            
            print(f"\n✅ Успешно сгенерирована таблица регионов с ценами:")
            print(f"   📊 Всего регионов: {len(regions)}")
            print(f"   💰 Регионов с ценами: {len(regions_with_prices)}")
            print(f"   📁 Файл: {args.output}")
            print(f"   ⏱️ Время выполнения: {elapsed:.1f} секунд")
            
            if regions_with_prices:
                avg_prices = [r['avg_price'] for r in regions_with_prices if r.get('avg_price')]
                if avg_prices:
                    print(f"   💵 Средняя цена: {statistics.mean(avg_prices):.2f} руб/л")
            
        else:
            logger.error("Не удалось получить данные о регионах")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Генерация прервана пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()