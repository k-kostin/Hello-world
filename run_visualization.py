#!/usr/bin/env python3
"""
Основной скрипт для создания интерактивных карт с ценами на топливо.
Генерирует HTML карту на основе folium с переключаемыми слоями топлива.
"""

import sys
import subprocess
from pathlib import Path
import glob

def install_dependencies():
    """Устанавливает необходимые зависимости."""
    print("Установка зависимостей...")
    try:
        # Устанавливаем основные зависимости
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                             "folium", "branca", "pandas", "--break-system-packages"])
        print("Зависимости установлены успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка установки зависимостей: {e}")
        return False

def find_price_file():
    """Ищет файл с ценами на топливо. Приоритет полным выгрузкам всех регионов."""
    import json
    
    # Возможные паттерны имен файлов (приоритет полным выгрузкам)
    patterns = [
        "all_regions_*.json",           # Полные выгрузки всех регионов
        "*_full_*.json",                # Файлы с пометкой "full"
        "*_complete_*.json",            # Файлы с пометкой "complete"
        "regional_prices_*.json",       # Обычные региональные выгрузки
        "prices_*.json", 
        "fuel_prices_*.json"
    ]
    
    best_file = None
    max_regions = 0
    min_required_regions = 50  # Минимум регионов для "полной" выгрузки
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Считаем успешные регионы
                    region_count = sum(1 for item in data if item.get('status') == 'success')
                    
                    # Приоритет файлам с большим количеством регионов
                    if region_count > max_regions:
                        max_regions = region_count
                        best_file = file_path
            except:
                continue
    
    # Проверяем полноту выгрузки
    if best_file and max_regions > 0:
        if max_regions >= min_required_regions:
            print(f"[OK] Найден файл с ПОЛНОЙ выгрузкой: {best_file} ({max_regions} регионов)")
        else:
            print(f"[WARNING] Найден файл с ЧАСТИЧНОЙ выгрузкой: {best_file} ({max_regions} регионов)")
            print(f"[RECOMMEND] Рекомендуется запустить: python regional_parser.py --all-regions")
            
        return best_file
    
    return None

def run_map_generation():
    """Запускает генерацию карт."""
    print("\n" + "="*50)
    print("СОЗДАНИЕ УПРОЩЕННОЙ КАРТЫ")
    print("="*50)
    
    try:
        # Используем новую упрощенную карту
        subprocess.check_call([sys.executable, "visualizations/unified_fuel_map.py"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка создания карты: {e}")
        return False

def main():
    """Основная функция."""
    print("Генератор карт с ценами на топливо (обновлённая версия)")
    print("=" * 60)
    
    # Проверяем наличие файла с ценами
    price_file = find_price_file()
    
    if not price_file:
        print("[ERROR] ОШИБКА: Не найден файл с ценами на топливо!")
        print("\n[INFO] ТРЕБУЕТСЯ ФАЙЛ С ЦЕНАМИ:")
        print("   Файл должен находиться в корневой папке проекта")
        print("   Возможные имена файлов:")
        print("   • regional_prices_YYYYMMDD_HHMMSS.json")
        print("   • prices_YYYYMMDD_HHMMSS.json")
        print("   • fuel_prices_YYYYMMDD_HHMMSS.json")
        print("\n[HOW-TO] КАК ПОЛУЧИТЬ ФАЙЛ С ЦЕНАМИ:")
        print("   1. Запустите парсер: python regional_parser.py")
        print("   2. Или используйте существующий файл: regional_prices_20250707_145425.json")
        print("   3. Убедитесь, что файл содержит данные в формате JSON с ценами")
        print("\n[EXAMPLE] ПРИМЕР СОДЕРЖИМОГО ФАЙЛА:")
        print("   [")
        print('     {"region_id": 77, "region_name": "Регион", "fuel_prices": {"АИ-92": 56.5, "Пропан": 27.5}}')
        print("   ]")
        return False
    
    print(f"[OK] Найден файл с ценами: {price_file}")
    
    # Проверяем geojson файл в разных местах
    geojson_paths = [
        "data/geojson/russia_reg v2.geojson",
        "src/russia_reg v2.geojson"
    ]
    
    geojson_found = False
    for geojson_path in geojson_paths:
        if Path(geojson_path).exists():
            geojson_found = True
            print(f"[OK] Найден файл границ: {geojson_path}")
            break
    
    if not geojson_found:
        print("[ERROR] ОШИБКА: Не найден файл с границами регионов!")
        print("Ожидаемые расположения:")
        for path in geojson_paths:
            print(f"  - {path}")
        return False
    
    print("[OK] Все необходимые файлы найдены")
    
    # Устанавливаем зависимости
    if not install_dependencies():
        return False
    
    # Генерируем карту
    if not run_map_generation():
        return False
    
    print("\n" + "="*60)
    print("[SUCCESS] УСПЕШНО ЗАВЕРШЕНО!")
    print("="*60)
    
    # Показываем созданный файл
    maps_dir = Path("data/maps")
    if maps_dir.exists():
        print("\n[MAP] Созданная карта:")
        map_file = maps_dir / "unified_fuel_map.html"
        if map_file.exists():
            print(f"   {map_file}")
            print(f"[BROWSER] Откройте в браузере: file://{map_file.absolute()}")
            print("\n[FEATURES] Функции упрощенной карты:")
            print("   • Вся информация о топливе в одном попапе")
            print("   • Поиск регионов в левом верхнем углу")
            print("   • Красивые попапы с таблицей цен")
            print("   • Цветовая индикация регионов по типу топлива")
            print("   • Легенда с типами топлива")
            print("   • Hover эффекты при наведении на регионы")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)