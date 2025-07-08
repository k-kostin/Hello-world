#!/usr/bin/env python3
"""
Основной скрипт для создания интерактивных карт с ценами на топливо.
Генерирует HTML карту на основе folium с переключаемыми слоями топлива.
"""

import sys
import subprocess
from pathlib import Path

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
    
    # Проверяем наличие необходимых файлов
    required_files = [
        "regional_prices_20250707_145425.json"
    ]
    
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
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ ОШИБКА: Отсутствуют необходимые файлы:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("\nУбедитесь, что файл с ценами находится в корне проекта")
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
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)