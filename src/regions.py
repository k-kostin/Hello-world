"""
Модуль для работы с регионами России в russiabase.ru
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class RegionManager:
    """Менеджер для работы с регионами России"""
    
    def __init__(self, regions_file: str = "regions.md"):
        self.regions_file = Path(regions_file)
        self._regions: Optional[List[Dict[str, Any]]] = None
        
    def _load_regions(self) -> List[Dict[str, Any]]:
        """Загружает список регионов из markdown файла"""
        if self._regions is not None:
            return self._regions
            
        regions = []
        
        # Если файл regions.md не существует, используем встроенный список
        if not self.regions_file.exists():
            regions = self._get_builtin_regions()
        else:
            # Парсим markdown файл для извлечения JSON
            try:
                with open(self.regions_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Ищем JSON блок в файле
                json_start = content.find('```json\n[')
                if json_start != -1:
                    json_start += 8  # Длина '```json\n'
                    json_end = content.find('\n]', json_start) + 2
                    
                    if json_end > json_start:
                        json_str = content[json_start:json_end]
                        regions = json.loads(json_str)
                        
            except (json.JSONDecodeError, FileNotFoundError, Exception):
                # Если не удалось загрузить из файла, используем встроенные
                regions = self._get_builtin_regions()
        
        self._regions = regions
        return regions
    
    def _get_builtin_regions(self) -> List[Dict[str, Any]]:
        """Возвращает встроенный список основных регионов"""
        return [
            {"id": 1, "name": "Республика Адыгея", "url": "https://russiabase.ru/prices?region=1"},
            {"id": 22, "name": "Алтайский край", "url": "https://russiabase.ru/prices?region=22"},
            {"id": 28, "name": "Амурская область", "url": "https://russiabase.ru/prices?region=28"},
            {"id": 29, "name": "Архангельская область", "url": "https://russiabase.ru/prices?region=29"},
            {"id": 30, "name": "Астраханская область", "url": "https://russiabase.ru/prices?region=30"},
            {"id": 31, "name": "Белгородская область", "url": "https://russiabase.ru/prices?region=31"},
            {"id": 32, "name": "Брянская область", "url": "https://russiabase.ru/prices?region=32"},
            {"id": 33, "name": "Владимирская область", "url": "https://russiabase.ru/prices?region=33"},
            {"id": 34, "name": "Волгоградская область", "url": "https://russiabase.ru/prices?region=34"},
            {"id": 35, "name": "Вологодская область", "url": "https://russiabase.ru/prices?region=35"},
            {"id": 36, "name": "Воронежская область", "url": "https://russiabase.ru/prices?region=36"},
            {"id": 23, "name": "Краснодарский край", "url": "https://russiabase.ru/prices?region=23"},
            {"id": 24, "name": "Красноярский край", "url": "https://russiabase.ru/prices?region=24"},
            {"id": 40, "name": "Курская область", "url": "https://russiabase.ru/prices?region=40"},
            {"id": 47, "name": "Ленинградская область", "url": "https://russiabase.ru/prices?region=47"},
            {"id": 77, "name": "Москва", "url": "https://russiabase.ru/prices?region=77"},
            {"id": 50, "name": "Московская область", "url": "https://russiabase.ru/prices?region=50"},
            {"id": 52, "name": "Нижегородская область", "url": "https://russiabase.ru/prices?region=52"},
            {"id": 54, "name": "Новосибирская область", "url": "https://russiabase.ru/prices?region=54"},
            {"id": 59, "name": "Пермский край", "url": "https://russiabase.ru/prices?region=59"},
            {"id": 61, "name": "Ростовская область", "url": "https://russiabase.ru/prices?region=61"},
            {"id": 78, "name": "Санкт-Петербург", "url": "https://russiabase.ru/prices?region=78"},
            {"id": 66, "name": "Свердловская область", "url": "https://russiabase.ru/prices?region=66"},
            {"id": 16, "name": "Республика Татарстан", "url": "https://russiabase.ru/prices?region=16"},
            {"id": 74, "name": "Челябинская область", "url": "https://russiabase.ru/prices?region=74"}
        ]
    
    def get_all_regions(self) -> List[Dict[str, Any]]:
        """Возвращает список всех регионов"""
        return self._load_regions()
    
    def get_region_by_id(self, region_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает регион по ID"""
        regions = self._load_regions()
        for region in regions:
            if region['id'] == region_id:
                return region
        return None
    
    def get_region_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Возвращает регион по названию"""
        regions = self._load_regions()
        for region in regions:
            if name.lower() in region['name'].lower():
                return region
        return None
    
    def get_region_url(self, region_id: int) -> Optional[str]:
        """Возвращает URL для получения цен в регионе"""
        region = self.get_region_by_id(region_id)
        return region['url'] if region else None
    
    def get_popular_regions(self) -> List[Dict[str, Any]]:
        """Возвращает список популярных регионов (крупные города и области)"""
        popular_ids = [77, 78, 50, 47, 23, 66, 52, 16, 61, 54, 74, 59, 40]
        regions = self._load_regions()
        return [r for r in regions if r['id'] in popular_ids]
    
    def get_regions_count(self) -> int:
        """Возвращает количество доступных регионов"""
        return len(self._load_regions())
    
    def search_regions(self, query: str) -> List[Dict[str, Any]]:
        """Поиск регионов по названию"""
        regions = self._load_regions()
        query_lower = query.lower()
        
        return [
            region for region in regions 
            if query_lower in region['name'].lower()
        ]
    
    def get_regions_by_type(self, region_type: str) -> List[Dict[str, Any]]:
        """Возвращает регионы по типу (республика, область, край, город)"""
        regions = self._load_regions()
        
        type_mapping = {
            'республика': 'Республика',
            'область': 'область',
            'край': 'край',
            'город': ['Москва', 'Санкт-Петербург', 'Севастополь'],
            'округ': 'округ'
        }
        
        if region_type.lower() == 'город':
            cities = type_mapping['город']
            return [r for r in regions if r['name'] in cities]
        else:
            search_term = type_mapping.get(region_type.lower(), region_type)
            return [r for r in regions if search_term in r['name']]
    
    def validate_region_id(self, region_id: int) -> bool:
        """Проверяет, существует ли регион с данным ID"""
        return self.get_region_by_id(region_id) is not None
    
    def get_regions_summary(self) -> Dict[str, Any]:
        """Возвращает сводную информацию о регионах"""
        regions = self._load_regions()
        
        summary = {
            'total_regions': len(regions),
            'by_type': {},
            'popular_regions': len(self.get_popular_regions()),
            'id_range': {
                'min': min(r['id'] for r in regions) if regions else 0,
                'max': max(r['id'] for r in regions) if regions else 0
            }
        }
        
        # Подсчет по типам
        for region_type in ['республика', 'область', 'край', 'город', 'округ']:
            summary['by_type'][region_type] = len(self.get_regions_by_type(region_type))
        
        return summary


# Глобальный экземпляр менеджера регионов
region_manager = RegionManager()


def get_region_id_by_name(name: str) -> Optional[int]:
    """Утилитарная функция для получения ID региона по названию"""
    region = region_manager.get_region_by_name(name)
    return region['id'] if region else None


def get_region_url_by_id(region_id: int) -> Optional[str]:
    """Утилитарная функция для получения URL региона по ID"""
    return region_manager.get_region_url(region_id)


def get_all_region_ids() -> List[int]:
    """Утилитарная функция для получения всех ID регионов"""
    regions = region_manager.get_all_regions()
    return [r['id'] for r in regions]


def is_valid_region_id(region_id: int) -> bool:
    """Утилитарная функция для проверки валидности ID региона"""
    return region_manager.validate_region_id(region_id)