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
    """Ищет файл с ценами на топливо."""
    # Возможные паттерны имен файлов
    patterns = [
        "regional_prices_*.json",
        "prices_*.json", 
        "fuel_prices_*.json"
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            # Возвращаем самый новый файл
            return max(files, key=lambda x: Path(x).stat().st_mtime)
    
    return None

def run_map_generation():
    """Запускает генерацию карт."""
    print("\n" + "="*50)
    print("СОЗДАНИЕ ИНТЕРАКТИВНОЙ КАРТЫ")
    print("="*50)
    
    try:
        subprocess.check_call([sys.executable, "visualizations/fuel_price_map.py"])
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
        print("❌ ОШИБКА: Не найден файл с ценами на топливо!")
        print("\n📍 ТРЕБУЕТСЯ ФАЙЛ С ЦЕНАМИ:")
        print("   Файл должен находиться в корневой папке проекта")
        print("   Возможные имена файлов:")
        print("   • regional_prices_YYYYMMDD_HHMMSS.json")
        print("   • prices_YYYYMMDD_HHMMSS.json")
        print("   • fuel_prices_YYYYMMDD_HHMMSS.json")
        print("\n🔧 КАК ПОЛУЧИТЬ ФАЙЛ С ЦЕНАМИ:")
        print("   1. Запустите парсер: python regional_parser.py")
        print("   2. Или используйте существующий файл: regional_prices_20250707_145425.json")
        print("   3. Убедитесь, что файл содержит данные в формате JSON с ценами")
        print("\n💡 ПРИМЕР СОДЕРЖИМОГО ФАЙЛА:")
        print("   [")
        print('     {"region_id": 77, "region_name": "Регион", "fuel_prices": {"АИ-92": 56.5, "Пропан": 27.5}}')
        print("   ]")
        return False
    
    print(f"✅ Найден файл с ценами: {price_file}")
    
    # Проверяем geojson файл в разных местах
    geojson_paths = [
        "data/geojson/russia_reg v2.geojson",
        "src/russia_reg v2.geojson"
    ]
    
    geojson_found = False
    for geojson_path in geojson_paths:
        if Path(geojson_path).exists():
            geojson_found = True
            print(f"✅ Найден файл границ: {geojson_path}")
            break
    
    if not geojson_found:
        print("❌ ОШИБКА: Не найден файл с границами регионов!")
        print("Ожидаемые расположения:")
        for path in geojson_paths:
            print(f"  - {path}")
        return False
    
    print("✅ Все необходимые файлы найдены")
    
    # Устанавливаем зависимости
    if not install_dependencies():
        return False
    
    # Генерируем карту
    if not run_map_generation():
        return False
    
    print("\n" + "="*60)
    print("🎉 УСПЕШНО ЗАВЕРШЕНО!")
    print("="*60)
    
    # Показываем созданный файл
    maps_dir = Path("data/maps")
    if maps_dir.exists():
        print("\n📍 Созданная карта:")
        map_file = maps_dir / "fuel_price_interactive_map.html"
        if map_file.exists():
            print(f"   {map_file}")
            print(f"🌐 Откройте в браузере: file://{map_file.absolute()}")
            print("\n🔧 Функции карты:")
            print("   • Переключение между видами топлива через контроллер слоёв")
            print("   • Поиск регионов в левом верхнем углу")
            print("   • Клик на регион для просмотра цен")
            print("   • Стабильные границы при масштабировании")
            print("   • По умолчанию показывается АИ-92 (самое популярное топливо)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)