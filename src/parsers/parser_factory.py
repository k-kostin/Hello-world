"""
Фабрика для создания парсеров
"""
from typing import Dict, Any
from .base import BaseParser
from .russiabase_parser import RussiaBaseParser
from .gazprom_parser import GazpromParser
from .yandex_parser import YandexMapsParser
from .tatneft_parser import TatneftParser


class ParserFactory:
    """Фабрика для создания парсеров цен АЗС"""
    
    _PARSER_MAPPING = {
        "russiabase": RussiaBaseParser,
        "api": GazpromParser,
        "selenium": YandexMapsParser,
        "tatneft_api": TatneftParser
    }
    
    @classmethod
    def create_parser(cls, network_name: str, config: Dict[str, Any]) -> BaseParser:
        """
        Создает парсер на основе конфигурации сети
        
        Args:
            network_name: Название сети АЗС
            config: Конфигурация сети
            
        Returns:
            Экземпляр парсера
            
        Raises:
            ValueError: Если тип парсера не поддерживается
        """
        parser_type = config.get("type")
        
        if parser_type not in cls._PARSER_MAPPING:
            raise ValueError(f"Неподдерживаемый тип парсера: {parser_type}")
        
        parser_class = cls._PARSER_MAPPING[parser_type]
        return parser_class(network_name, config)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Возвращает список поддерживаемых типов парсеров"""
        return list(cls._PARSER_MAPPING.keys())