#!/usr/bin/env python3
"""
Основной скрипт для создания интерактивных карт с ценами на топливо.
Автоматически создает маппинг регионов и генерирует HTML карты.
"""

import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Устанавливает необходимые зависимости."""
    print("Установка зависимостей...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Зависимости установлены успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка установки зависимостей: {e}")
        return False

def run_region_mapping():
    """Запускает создание маппинга регионов."""
    print("\n" + "="*50)
    print("СОЗДАНИЕ МАППИНГА РЕГИОНОВ")
    print("="*50)
    
    try:
        subprocess.check_call([sys.executable, "visualizations/region_mapping.py"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка создания маппинга: {e}")
        return False

def run_map_generation():
    """Запускает генерацию карт."""
    print("\n" + "="*50)
    print("СОЗДАНИЕ ИНТЕРАКТИВНЫХ КАРТ")
    print("="*50)
    
    try:
        subprocess.check_call([sys.executable, "visualizations/fuel_price_map.py"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка создания карт: {e}")
        return False

def main():
    """Основная функция."""
    print("Генератор карт с ценами на топливо")
    print("=" * 50)
    
    # Проверяем наличие необходимых файлов
    required_files = [
        "data/geojson/russia_reg v2.geojson",
        "regional_prices_20250707_145425.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("ОШИБКА: Отсутствуют необходимые файлы:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("\nУбедитесь, что файлы находятся в правильных местах:")
        print("  - Файл russia_reg v2.geojson должен быть в data/geojson/")
        print("  - Файл с ценами на топливо должен быть в корне проекта")
        return False
    
    # Устанавливаем зависимости
    if not install_dependencies():
        return False
    
    # Создаем маппинг регионов
    if not run_region_mapping():
        return False
    
    # Генерируем карты
    if not run_map_generation():
        return False
    
    print("\n" + "="*50)
    print("УСПЕШНО ЗАВЕРШЕНО!")
    print("="*50)
    
    # Показываем созданные файлы
    maps_dir = Path("data/maps")
    if maps_dir.exists():
        print("\nСозданные карты:")
        for map_file in maps_dir.glob("*.html"):
            print(f"  - {map_file}")
            print(f"    Откройте в браузере: file://{map_file.absolute()}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)