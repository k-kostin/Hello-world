#!/usr/bin/env python3
"""
Демонстрационный скрипт для создания полной выгрузки цен по всем регионам России.
Этот скрипт показывает как получить файл с правильным неймингом и полными данными.
"""

import subprocess
import sys
from datetime import datetime


def main():
    """Демонстрация полного парсинга и создания карт"""
    print("🗺️ ДЕМОНСТРАЦИЯ ПОЛНОГО ПАРСИНГА РЕГИОНАЛЬНЫХ ЦЕН")
    print("=" * 60)
    print()
    
    print("ЧТО ИСПРАВЛЕНО:")
    print("✅ Система нейминга файлов по полноте выгрузки")
    print("✅ Приоритет полным выгрузкам при создании карт")
    print("✅ Правильные единицы измерения: Газ (руб/м³), Пропан (руб/кг)")
    print("✅ Предупреждения о неполных выгрузках")
    print()
    
    print("СИСТЕМА НЕЙМИНГА ФАЙЛОВ:")
    print("• all_regions_full_XXXreg_* - полная выгрузка (80+ регионов)")
    print("• all_regions_major_XXXreg_* - крупная выгрузка (50+ регионов)")
    print("• regional_prices_medium_XXXreg_* - средняя выгрузка (20+ регионов)")
    print("• regional_prices_small_XXXreg_* - малая выгрузка (10+ регионов)")
    print("• regional_prices_demo_XXXreg_* - демо/тестовая выгрузка (<10 регионов)")
    print()
    
    choice = input("Запустить полный парсинг всех регионов? (y/N): ").strip().lower()
    
    if choice in ['y', 'yes', 'да']:
        print("\n🚀 ЗАПУСК ПОЛНОГО ПАРСИНГА...")
        print("⚠️  Это может занять 10-15 минут для ~85 регионов")
        print()
        
        try:
            # Запускаем полный парсинг
            result = subprocess.run([
                sys.executable, "regional_parser.py", 
                "--all-regions",
                "--verbose"
            ], capture_output=False, text=True)
            
            if result.returncode == 0:
                print("\n✅ ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
                print("📁 Файлы сохранены с правильными названиями")
                print()
                
                # Запускаем создание карт
                create_maps = input("Создать карты на основе новых данных? (y/N): ").strip().lower()
                if create_maps in ['y', 'yes', 'да']:
                    print("\n🗺️ СОЗДАНИЕ КАРТ...")
                    map_result = subprocess.run([
                        sys.executable, "run_visualization.py"
                    ], capture_output=False, text=True)
                    
                    if map_result.returncode == 0:
                        print("\n✅ КАРТЫ СОЗДАНЫ УСПЕШНО!")
                        print("🌐 Теперь карты используют полные данные со всеми регионами")
                        print("📊 Единицы измерения исправлены: Газ (руб/м³), Пропан (руб/кг)")
            else:
                print("\n❌ ОШИБКА ПРИ ПАРСИНГЕ")
                
        except KeyboardInterrupt:
            print("\n⏸️ Парсинг прерван пользователем")
        except Exception as e:
            print(f"\n❌ ОШИБКА: {e}")
    
    else:
        print("\n📖 ДЛЯ РУЧНОГО ЗАПУСКА ИСПОЛЬЗУЙТЕ:")
        print("python regional_parser.py --all-regions")
        print("python run_visualization.py")
        print()
        print("ПРОВЕРКА СУЩЕСТВУЮЩИХ ФАЙЛОВ:")
        
        import glob
        import json
        from pathlib import Path
        
        patterns = ["all_regions_*.json", "*_full_*.json", "regional_prices_*.json"]
        
        for pattern in patterns:
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        count = sum(1 for item in data if item.get('status') == 'success')
                        size = Path(file_path).stat().st_size // 1024
                        
                    if count >= 50:
                        status = "✅ ПОЛНАЯ"
                    elif count >= 20:
                        status = "⚠️  ЧАСТИЧНАЯ"
                    else:
                        status = "❌ НЕПОЛНАЯ"
                        
                    print(f"{status} - {file_path} ({count} регионов, {size} KB)")
                except:
                    continue


if __name__ == "__main__":
    main()