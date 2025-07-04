from typing import Dict, Type

from .russiabase import RussiabaseParser
from .gazprom import GazpromParser
from .tatneft import TatneftParser
from .yandex import YandexMapParser

_PARSERS: Dict[str, Type] = {
    "bashneft": RussiabaseParser.with_brand(292),
    "lukoil": RussiabaseParser.with_brand(119),
    "neftmagistral": RussiabaseParser.with_brand(119),  # same brand id
    "gazprom": GazpromParser,
    "tatneft": TatneftParser,
    "yandex": YandexMapParser,
}


def get_parser(name: str):
    """Factory returning parser class (not instance)."""
    key = name.lower()
    if key not in _PARSERS:
        raise ValueError(f"Unknown parser name: {name}. Available: {list(_PARSERS)}")
    return _PARSERS[key]