#!/usr/bin/env python3
"""
Генератор таблицы регионов России на основе russiabase.ru
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Tuple, Any
import sys

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


class RegionParser:
    """Парсер для получения списка регионов с russiabase.ru"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.base_url = "https://russiabase.ru/prices"
        
    def fetch_regions(self) -> List[Dict[str, Any]]:
        """Получает список всех регионов"""
        logger.info("Получение списка регионов с russiabase.ru...")
        
        try:
            # Получаем главную страницу с ценами
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            regions = []
            
            # Ищем выпадающий список регионов или ссылки на региональные страницы
            # Вариант 1: Поиск select с регионами
            region_select = soup.find('select', {'name': 'region'}) or soup.find('select', id=re.compile(r'region', re.I))
            
            if region_select:
                logger.info("Найден select с регионами")
                options = region_select.find_all('option')
                for option in options:
                    value = option.get('value')
                    text = option.get_text(strip=True)
                    
                    if value and value.isdigit() and text:
                        regions.append({
                            'id': int(value),
                            'name': text,
                            'url': f"{self.base_url}?region={value}"
                        })
            
            # Вариант 2: Поиск ссылок с параметром region
            if not regions:
                logger.info("Ищем ссылки с параметром region...")
                region_links = soup.find_all('a', href=re.compile(r'region=\d+'))
                
                for link in region_links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    # Извлекаем ID региона из URL
                    match = re.search(r'region=(\d+)', href)
                    if match and text:
                        region_id = int(match.group(1))
                        regions.append({
                            'id': region_id,
                            'name': text,
                            'url': f"https://russiabase.ru{href}" if href.startswith('/') else href
                        })
            
            # Вариант 3: Пробуем получить регионы через JavaScript/AJAX endpoint
            if not regions:
                logger.info("Пробуем найти AJAX endpoint для регионов...")
                regions = self._try_ajax_regions()
            
            # Вариант 4: Брутфорс известных регионов России
            if not regions:
                logger.info("Используем известные регионы России...")
                regions = self._get_known_regions()
            
            # Удаляем дубликаты по ID
            unique_regions = {}
            for region in regions:
                if region['id'] not in unique_regions:
                    unique_regions[region['id']] = region
                    
            regions = list(unique_regions.values())
            regions.sort(key=lambda x: x['name'])
            
            logger.info(f"Найдено {len(regions)} регионов")
            return regions
            
        except Exception as e:
            logger.error(f"Ошибка при получении регионов: {e}")
            return []
    
    def _try_ajax_regions(self) -> List[Dict[str, Any]]:
        """Пытается получить регионы через AJAX запросы"""
        ajax_endpoints = [
            "https://russiabase.ru/api/regions",
            "https://russiabase.ru/regions.json",
            "https://russiabase.ru/ajax/regions"
        ]
        
        for endpoint in ajax_endpoints:
            try:
                logger.debug(f"Пробуем endpoint: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        return [{'id': item.get('id'), 'name': item.get('name'), 'url': f"{self.base_url}?region={item.get('id')}"} 
                               for item in data if item.get('id') and item.get('name')]
                        
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} не сработал: {e}")
                continue
                
        return []
    
    def _get_known_regions(self) -> List[Dict[str, Any]]:
        """Возвращает список известных регионов России с их предполагаемыми ID"""
        known_regions = [
            (1, "Республика Адыгея"),
            (2, "Республика Алтай"),
            (3, "Республика Башкортостан"),
            (4, "Республика Бурятия"),
            (5, "Республика Дагестан"),
            (6, "Республика Ингушетия"),
            (7, "Кабардино-Балкарская Республика"),
            (8, "Республика Калмыкия"),
            (9, "Карачаево-Черкесская Республика"),
            (10, "Республика Карелия"),
            (11, "Республика Коми"),
            (12, "Республика Марий Эл"),
            (13, "Республика Мордовия"),
            (14, "Республика Саха (Якутия)"),
            (15, "Республика Северная Осетия — Алания"),
            (16, "Республика Татарстан"),
            (17, "Республика Тыва"),
            (18, "Удмуртская Республика"),
            (19, "Республика Хакасия"),
            (20, "Чеченская Республика"),
            (21, "Чувашская Республика"),
            (22, "Алтайский край"),
            (23, "Краснодарский край"),
            (24, "Красноярский край"),
            (25, "Приморский край"),
            (26, "Ставропольский край"),
            (27, "Хабаровский край"),
            (28, "Амурская область"),
            (29, "Архангельская область"),
            (30, "Астраханская область"),
            (31, "Белгородская область"),
            (32, "Брянская область"),
            (33, "Владимирская область"),
            (34, "Волгоградская область"),
            (35, "Вологодская область"),
            (36, "Воронежская область"),
            (37, "Ивановская область"),
            (38, "Иркутская область"),
            (39, "Калининградская область"),
            (40, "Курская область"),
            (41, "Калужская область"),
            (42, "Камчатский край"),
            (43, "Кемеровская область"),
            (44, "Кировская область"),
            (45, "Костромская область"),
            (46, "Курганская область"),
            (47, "Ленинградская область"),
            (48, "Липецкая область"),
            (49, "Магаданская область"),
            (50, "Московская область"),
            (51, "Мурманская область"),
            (52, "Нижегородская область"),
            (53, "Новгородская область"),
            (54, "Новосибирская область"),
            (55, "Омская область"),
            (56, "Оренбургская область"),
            (57, "Орловская область"),
            (58, "Пензенская область"),
            (59, "Пермский край"),
            (60, "Псковская область"),
            (61, "Ростовская область"),
            (62, "Рязанская область"),
            (63, "Самарская область"),
            (64, "Саратовская область"),
            (65, "Сахалинская область"),
            (66, "Свердловская область"),
            (67, "Смоленская область"),
            (68, "Тамбовская область"),
            (69, "Тверская область"),
            (70, "Томская область"),
            (71, "Тульская область"),
            (72, "Тюменская область"),
            (73, "Ульяновская область"),
            (74, "Челябинская область"),
            (75, "Забайкальский край"),
            (76, "Ярославская область"),
            (77, "Москва"),
            (78, "Санкт-Петербург"),
            (79, "Еврейская автономная область"),
            (80, "Ненецкий автономный округ"),
            (81, "Ханты-Мансийский автономный округ — Югра"),
            (82, "Чукотский автономный округ"),
            (83, "Ямало-Ненецкий автономный округ"),
            (84, "Республика Крым"),
            (85, "Севастополь")
        ]
        
        # Проверим реальность некоторых ID, делая запросы
        verified_regions = []
        logger.info("Проверяем доступность регионов...")
        
        for region_id, region_name in known_regions[:10]:  # Проверим первые 10 для экономии времени
            try:
                url = f"{self.base_url}?region={region_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200 and "Цены на бензин" in response.text:
                    verified_regions.append({
                        'id': region_id,
                        'name': region_name,
                        'url': url
                    })
                    logger.debug(f"Регион {region_name} (ID: {region_id}) подтвержден")
                else:
                    logger.debug(f"Регион {region_name} (ID: {region_id}) недоступен")
                    
                time.sleep(1)  # Задержка между запросами
                
            except Exception as e:
                logger.debug(f"Ошибка проверки региона {region_name}: {e}")
                continue
        
        # Если проверили хотя бы один регион, добавляем остальные без проверки
        if verified_regions:
            for region_id, region_name in known_regions:
                if region_id not in [r['id'] for r in verified_regions]:
                    verified_regions.append({
                        'id': region_id,
                        'name': region_name,
                        'url': f"{self.base_url}?region={region_id}"
                    })
        
        return verified_regions
    
    def save_to_markdown(self, regions: List[Dict[str, Any]], filename: str = "regions.md"):
        """Сохраняет список регионов в markdown файл"""
        logger.info(f"Сохранение {len(regions)} регионов в файл {filename}")
        
        content = f"""# Регионы России - RussiaBase.ru

Таблица регионов с ID для работы с сайтом russiabase.ru

Сгенерировано: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Общая информация

- Всего регионов: {len(regions)}
- Базовый URL: https://russiabase.ru/prices
- URL региона: https://russiabase.ru/prices?region={{ID}}

## Таблица регионов

| ID | Название региона | URL |
|----|------------------|-----|
"""
        
        for region in regions:
            content += f"| {region['id']} | {region['name']} | {region['url']} |\n"
        
        content += f"""
## Использование

```python
# Пример использования для получения цен в конкретном регионе
base_url = "https://russiabase.ru/prices"
region_id = 40  # Курская область
url = f"{{base_url}}?region={{region_id}}"
```

## JSON формат

```json
[
"""
        
        for i, region in enumerate(regions):
            comma = "," if i < len(regions) - 1 else ""
            content += f'  {{"id": {region["id"]}, "name": "{region["name"]}", "url": "{region["url"]}"}}{comma}\n'
            
        content += "]\n```\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Регионы сохранены в файл {filename}")


def main():
    """Главная функция"""
    logger.info("Запуск генератора таблицы регионов")
    
    parser = RegionParser()
    regions = parser.fetch_regions()
    
    if regions:
        parser.save_to_markdown(regions, "regions.md")
        
        # Краткая статистика
        print(f"\n✅ Успешно сгенерирована таблица регионов:")
        print(f"   📊 Всего регионов: {len(regions)}")
        print(f"   📁 Файл: regions.md")
        print(f"   🔗 Пример URL: {regions[0]['url'] if regions else 'N/A'}")
        
    else:
        logger.error("Не удалось получить список регионов")
        sys.exit(1)


if __name__ == "__main__":
    main()