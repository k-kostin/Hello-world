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
    """Ищет файл с ценами на топливо. ТОЛЬКО полные выгрузки всех регионов!"""
    import json
    
    # Строгий приоритет ТОЛЬКО полным выгрузкам (по аналогии с all_gas_stations_)
    patterns = [
        "all_regions_*.json",           # Полные выгрузки всех регионов (>=80 регионов)
    ]
    
    best_file = None
    max_regions = 0
    min_required_regions = 80  # СТРОГО: минимум 80 регионов для полной выгрузки
    
    print(f"[SEARCH] Поиск файлов с ПОЛНОЙ выгрузкой региональных цен (>={min_required_regions} регионов)...")
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Считаем успешные регионы
                    region_count = sum(1 for item in data if item.get('status') == 'success')
                    
                    print(f"[CHECK] {file_path}: {region_count} регионов")
                    
                    # СТРОГО: принимаем только файлы с полной выгрузкой
                    if region_count >= min_required_regions:
                        if region_count > max_regions:
                            max_regions = region_count
                            best_file = file_path
                    else:
                        print(f"[REJECT] {file_path}: недостаточно регионов ({region_count} < {min_required_regions})")
            except Exception as e:
                print(f"[ERROR] Ошибка чтения {file_path}: {e}")
                continue
    
    # Проверяем результат
    if best_file and max_regions >= min_required_regions:
        print(f"[SUCCESS] Найден файл с ПОЛНОЙ выгрузкой: {best_file} ({max_regions} регионов)")
        return best_file
    
    # Если полной выгрузки нет - отклоняем все частичные файлы
    print(f"[FAIL] НЕ НАЙДЕН файл с полной выгрузкой (>={min_required_regions} регионов)")
    
    # Ищем частичные выгрузки только для информирования
    partial_patterns = [
        "regions_*.json",
        "regional_prices_*.json"
    ]
    
    partial_files = []
    for pattern in partial_patterns:
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    region_count = sum(1 for item in data if item.get('status') == 'success')
                    partial_files.append((file_path, region_count))
            except:
                continue
    
    if partial_files:
        print(f"[INFO] Найдены файлы с частичными выгрузками (НЕ подходят для карт):")
        for file_path, count in sorted(partial_files, key=lambda x: x[1], reverse=True):
            print(f"  - {file_path}: {count} регионов")
    
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
        print("[ERROR] ОШИБКА: Не найден файл с ПОЛНОЙ выгрузкой региональных цен!")
        print("\n[REQUIREMENT] ДЛЯ СОЗДАНИЯ КАРТ ТРЕБУЕТСЯ:")
        print("   ✅ Файл с полной выгрузкой региональных цен (>=80 регионов)")
        print("   ✅ Название файла должно начинаться с 'all_regions_'")
        print("   ✅ Файл должен находиться в корневой папке проекта")
        print("\n[HOW-TO] КАК ПОЛУЧИТЬ ПОЛНУЮ ВЫГРУЗКУ:")
        print("   1. Запустите: python regional_parser.py --all-regions")
        print("   2. Дождитесь завершения парсинга (~10-15 минут)")
        print("   3. Будет создан файл вида: all_regions_YYYYMMDD_HHMMSS.json")
        print("   4. Повторно запустите создание карты")
        print("\n[IMPORTANT] ПОЧЕМУ НУЖНА ПОЛНАЯ ВЫГРУЗКА:")
        print("   • Карта должна показывать все регионы России")
        print("   • Частичные выгрузки не дают полную картину цен")
        print("   • Пользователи ожидают видеть данные по всей стране")
        print("\n[FILES] ФАЙЛЫ НЕ ПОДХОДЯЩИЕ ДЛЯ КАРТ:")
        print("   ❌ regional_prices_*.json (частичные выгрузки)")
        print("   ❌ regions_partial_*.json (неполные данные)")
        print("   ❌ regions_*of85_*.json (крупные, но не полные)")
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