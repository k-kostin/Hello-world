#!/usr/bin/env python3
"""
Скрипт для создания интерактивной карты России с ценами на топливо.
Использует folium для создания надежной карты с переключаемыми слоями топлива.
"""

import json
import folium
from folium.features import GeoJson, GeoJsonPopup, GeoJsonTooltip
from branca.element import Element
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

class FuelPriceMapGenerator:
    """Класс для создания карт с ценами на топливо на основе folium."""
    
    def __init__(self, geojson_path: str, prices_path: str):
        """
        Инициализация генератора карт.
        
        Args:
            geojson_path: Путь к файлу с границами регионов
            prices_path: Путь к файлу с ценами на топливо
        """
        self.geojson_path = geojson_path
        self.prices_path = prices_path
        self.geojson_data = None
        self.price_data = None
        
        # Доступные виды топлива с цветами для слоев
        self.fuel_colors = {
            "АИ-92": "#228B22",      # Зелёный
            "АИ-92+": "#32CD32",     # Светло-зелёный
            "АИ-95": "#4169E1",      # Синий
            "АИ-95+": "#1E90FF",     # Светло-синий
            "АИ-98": "#800080",      # Фиолетовый
            "АИ-100": "#FFA500",     # Оранжевый
            "АИ-100+": "#DAA520",    # Золотисто-коричневый
            "ДТ": "#8B4513",         # Коричневый
            "ДТ+": "#A0522D",        # Светло-коричневый
            "Газ": "#FFD700",        # Золотой
            "Пропан": "#FF69B4",     # Розовый
        }
        
        # Отображаемые названия типов топлива
        self.fuel_display_names = {
            "АИ-92": "АИ‑92",
            "АИ-92+": "АИ‑92+", 
            "АИ-95": "АИ‑95",
            "АИ-95+": "АИ‑95+",
            "АИ-98": "АИ‑98",
            "АИ-100": "АИ‑100",
            "АИ-100+": "АИ‑100+",
            "ДТ": "Дизель",
            "ДТ+": "Дизель+",
            "Газ": "Газ",
            "Пропан": "Пропан",
        }
    
    def load_data(self):
        """Загружает данные из файлов."""
        print("Загрузка геоданных...")
        with open(self.geojson_path, 'r', encoding='utf-8') as f:
            self.geojson_data = json.load(f)
        
        print("Загрузка данных о ценах...")
        with open(self.prices_path, 'r', encoding='utf-8') as f:
            price_list = json.load(f)
        
        # Преобразуем в словарь для быстрого поиска
        self.price_data = {}
        for item in price_list:
            if item.get('status') == 'success':
                self.price_data[item['region_name']] = item['fuel_prices']
        
        print(f"Загружено {len(self.geojson_data['features'])} регионов из geojson")
        print(f"Загружено {len(self.price_data)} регионов с ценами")
    
    def normalize_region_name(self, name: str) -> str:
        """Нормализует название региона для поиска."""
        import re
        
        # Словарь для прямого сопоставления особых случаев
        special_mappings = {
            'Москва': 'Москва',
            'г. Москва': 'Москва',
            'Санкт-Петербург': 'Санкт-Петербург',
            'Севастополь': 'Севастополь',
            'Республика Крым': 'Республика Крым',
            'Ненецкий автономный округ': 'Ненецкий автономный округ',
            'Ханты-Мансийский автономный округ — Югра': 'Ханты-Мансийский автономный округ',
            'Ханты-Мансийский автономный округ - Югра': 'Ханты-Мансийский автономный округ',
            'Ямало-Ненецкий автономный округ': 'Ямало-Ненецкий автономный округ',
            'Чукотский автономный округ': 'Чукотский автономный округ',
            'Еврейская автономная область': 'Еврейская автономная область',
            'Камчатский край': 'Камчатский край',
            'Тамбовская область': 'Тамбовская область',
        }
        
        # Сначала проверяем прямые совпадения
        if name in special_mappings:
            return special_mappings[name]
        
        # Затем стандартная нормализация (более осторожная)
        normalized = name.strip()
        
        # Не применяем нормализацию к коротким названиям
        if len(normalized.split()) <= 2:
            return normalized
            
        # Убираем окончания только если они есть в конце
        if normalized.endswith(' область'):
            normalized = normalized[:-8]
        elif normalized.endswith(' край'):
            normalized = normalized[:-5]
        elif normalized.startswith('Республика '):
            normalized = normalized[11:]
        elif normalized.endswith(' республика'):
            normalized = normalized[:-11]
        
        return normalized
    
    def find_region_prices(self, region_name: str) -> Optional[Dict]:
        """Находит цены для региона по имени."""
        # Прямое сопоставление
        if region_name in self.price_data:
            return self.price_data[region_name]
        
        # Нормализованное сопоставление
        normalized_input = self.normalize_region_name(region_name)
        for price_region, prices in self.price_data.items():
            normalized_price = self.normalize_region_name(price_region)
            if normalized_price == normalized_input:
                return prices
        
        # Дополнительный поиск по частичному совпадению (без учета регистра)
        region_lower = region_name.lower()
        for price_region, prices in self.price_data.items():
            price_lower = price_region.lower()
            if region_lower == price_lower:
                return prices
            # Проверяем вхождение для случаев типа "Ханты-Мансийский автономный округ"
            if (region_lower in price_lower or price_lower in region_lower) and len(region_lower) > 5:
                return prices
        
        return None
    
    def get_available_fuel_types(self) -> List[str]:
        """Возвращает список доступных типов топлива в правильном порядке (АИ-92 первый)."""
        if self.price_data is None:
            return []
        fuel_types = set()
        for prices in self.price_data.values():
            fuel_types.update(prices.keys())
        
        # Определяем правильный порядок топлива (АИ-92 должен быть первым)
        preferred_order = ["АИ-92", "АИ-92+", "АИ-95", "АИ-95+", "АИ-98", "АИ-100", "АИ-100+", "ДТ", "ДТ+", "Газ", "Пропан"]
        
        # Сортируем согласно предпочтительному порядку
        sorted_fuels = []
        for fuel in preferred_order:
            if fuel in fuel_types:
                sorted_fuels.append(fuel)
        
        # Добавляем оставшиеся типы топлива, которые не были в предпочтительном списке
        for fuel in sorted(fuel_types):
            if fuel not in sorted_fuels:
                sorted_fuels.append(fuel)
        
        return sorted_fuels
    
    def create_interactive_map(self, output_path: str = "fuel_price_map.html") -> folium.Map:
        """
        Создает интерактивную карту с ценами на топливо.
        
        Args:
            output_path: Путь для сохранения HTML файла
            
        Returns:
            Объект карты folium
        """
        if self.geojson_data is None or self.price_data is None:
            raise ValueError("Данные не загружены. Вызовите load_data() сначала.")
        
        # Создаём карту полностью без тайлов
        m = folium.Map(
            location=[61, 105],  # Центр России
            zoom_start=3,
            height=920,
            width="100%",
            tiles=None
        )
        
        # Добавляем OpenStreetMap как базовый тайл-слой
        folium.TileLayer(
            tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            name='OpenStreetMap',
            attr='OpenStreetMap',
            control=False,
            overlay=False,
            show=True
        ).add_to(m)
        
        # Получаем доступные типы топлива
        available_fuels = self.get_available_fuel_types()
        print(f"Доступные типы топлива: {available_fuels}")
        
        # Создаем слои для каждого типа топлива
        for idx, fuel_type in enumerate(available_fuels):
            if fuel_type not in self.fuel_colors:
                continue  # Пропускаем неизвестные типы топлива
            
            # Создаём глубокую копию GeoJSON для этого слоя
            gcopy = json.loads(json.dumps(self.geojson_data))
            display_name = self.fuel_display_names.get(fuel_type, fuel_type)
            
            # Подготавливаем данные для каждого региона
            for feat in gcopy["features"]:
                props = feat["properties"]
                props["fuel_type"] = fuel_type
                
                region = props.get("name", "")
                html = [f"<b>Регион: {region}</b>"]
                
                # Находим цены для региона
                region_prices = self.find_region_prices(region)
                if region_prices is not None and fuel_type in region_prices:
                    price = region_prices[fuel_type]
                    html.append(f"<br/>{display_name}: {price:.2f} руб/л")
                    props["has_price"] = True
                    props["fuel_price"] = price
                else:
                    html.append(f"<br/>{display_name}: нет данных")
                    props["has_price"] = False
                    props["fuel_price"] = None
                
                props["tooltip_html"] = "".join(html)
                props["popup_html"] = "".join(html)
            
            # Функция стилизации регионов - добавляем цветную заливку
            def style_fn(feat, fuel_type=fuel_type):
                has_price = feat["properties"].get("has_price", False)
                base_color = self.fuel_colors.get(fuel_type, "#e0e0e0")
                
                if has_price:
                    # Если есть данные - используем цвет топлива с прозрачностью
                    return {
                        "fillColor": base_color,
                        "color": "#333333",
                        "weight": 1,
                        "fillOpacity": 0.7
                    }
                else:
                    # Если нет данных - светло-серый цвет
                    return {
                        "fillColor": "#f0f0f0",
                        "color": "#cccccc", 
                        "weight": 0.5,
                        "fillOpacity": 0.3
                    }
            
            # Создаём слой GeoJSON
            gj = GeoJson(
                gcopy,
                name=display_name,
                overlay=False,  # Базовый слой, не оверлей
                show=(idx == 0),  # Показывать только первый слой по умолчанию
                style_function=style_fn,
                tooltip=GeoJsonTooltip(
                    fields=["tooltip_html"],
                    labels=False,
                    sticky=True,
                    style="background-color: rgba(0,0,0,0.8); color:white; padding:8px; border-radius:5px;"
                ),
                popup=GeoJsonPopup(
                    fields=["popup_html"],
                    labels=False,
                    style="background-color: white; color:black; border-radius:5px; max-width:300px;"
                )
            )
            gj.add_to(m)
        
        # Добавляем заголовок карты
        folium.Element('''
        <div style="position: fixed; top: 10px; left: 50px; z-index: 1000; 
                    font-size: 18px; font-weight: bold; background: white; 
                    padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
            Цены на топливо по регионам России
        </div>
        ''').add_to(m)
        
        # Добавляем контроллер слоев
        folium.LayerControl(collapsed=False, autoZIndex=True).add_to(m)
        
        # Добавляем стили для улучшения интерфейса
        css = """
        <style>
          /* Перемещаем контроллер масштаба в левый нижний угол */
          .leaflet-control-zoom {
            position: fixed !important;
            bottom: 60px !important;
            left: 10px !important;
            top: auto !important;
          }
          
          /* Фиксируем панель выбора слоёв в правом верхнем углу */
          .leaflet-top.leaflet-right .leaflet-control-layers {
            position: fixed !important;
            top: 80px !important;
            right: 10px !important;
          }
          
          /* Убираем прямоугольную обводку при клике на регион */
          .leaflet-interactive:focus {
            outline: none !important;
          }
          
          /* Стилизуем всплывающее окно */
          .leaflet-popup-content-wrapper {
            background-color: white;
            color: black;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
          }
          
          .leaflet-popup-tip-container {
            display: none !important;
          }
          
          .leaflet-popup-close-button {
            color: black !important;
            font-size: 18px !important;
          }
          
          /* Hover эффект для регионов */
          .leaflet-interactive:hover {
            stroke-width: 3 !important;
            stroke: #000000 !important;
            fill-opacity: 0.9 !important;
          }
        </style>
        """
        m.get_root().html.add_child(Element(css))
        
        # Добавляем поле поиска
        search_html = """
        <div id="search-container" style="position: fixed; top: 10px; left: 10px; z-index: 1000; width: 280px;">
          <div style="position: relative;">
            <input
              type="text"
              id="search-input"
              placeholder="Поиск региона..."
              style="width:100%; padding: 8px 30px 8px 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px;"
            />
            <button
              type="button"
              id="clear-search"
              aria-label="Очистить поиск"
              style="
                display: none;
                position: absolute;
                top: 50%;
                right: 8px;
                transform: translateY(-50%);
                border: none;
                background: transparent;
                font-size: 18px;
                color: #888;
                cursor: pointer;
              "
            >&times;</button>
          </div>
          <div id="search-results" style="
            max-height: 200px;
            overflow-y: auto;
            margin-top: 5px;
            display: none;
            background: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
          "></div>
        </div>
        """
        m.get_root().html.add_child(Element(search_html))
        
        # Убираем префикс атрибуции
        map_var = m.get_name()
        js_attrib = f"""
        <script>
        setTimeout(function() {{
            const map = {map_var};
            if (map.attributionControl) {{
                map.removeControl(map.attributionControl);
            }}
            L.control.attribution({{ prefix: false }}).addTo(map);
        }}, 500);
        </script>
        """
        m.get_root().html.add_child(Element(js_attrib))
        
        # Скрипт функционала поиска и hover эффектов
        js_search = f"""
        <script>
        setTimeout(function() {{
          const map = {map_var};
          
          // Собираем все названия регионов для поиска
          const regionNames = new Set();
          map.eachLayer(layer => {{
            if (layer.feature && layer.feature.properties && layer.feature.properties.name) {{
              regionNames.add(layer.feature.properties.name);
              
              // Добавляем hover эффекты для каждого слоя
              if (layer.feature) {{
                const originalStyle = layer.options.style ? layer.options.style(layer.feature) : {{}};
                
                layer.on('mouseover', function(e) {{
                  const layer = e.target;
                  const hasPrice = layer.feature.properties.has_price;
                  
                  layer.setStyle({{
                    weight: 3,
                    color: '#000000',
                    fillOpacity: hasPrice ? 0.9 : 0.5
                  }});
                  
                  if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {{
                    layer.bringToFront();
                  }}
                }});
                
                layer.on('mouseout', function(e) {{
                  const layer = e.target;
                  layer.setStyle(originalStyle);
                }});
              }}
            }}
          }});
          const regionsList = Array.from(regionNames).sort();
          
          // Функция поиска регионов
          function searchRegions(query) {{
            if (!query) return [];
            query = query.toLowerCase();
            return regionsList.filter(name => 
              name.toLowerCase().includes(query)
            );
          }}
          
          // Обработчик ввода в поле поиска
          const searchInput = document.getElementById('search-input');
          const searchResults = document.getElementById('search-results');
          const clearBtn = document.getElementById('clear-search');
          
          searchInput.addEventListener('input', function() {{
            const query = this.value.trim();
            clearBtn.style.display = this.value ? 'block' : 'none';
            
            const results = searchRegions(query);
            
            searchResults.innerHTML = '';
            if (results.length > 0 && query) {{
              results.forEach(name => {{
                const div = document.createElement('div');
                div.style.cssText = 'padding: 8px; cursor: pointer; border-bottom: 1px solid #eee;';
                div.textContent = name;
                div.addEventListener('mouseenter', function() {{ this.style.backgroundColor = '#f0f0f0'; }});
                div.addEventListener('mouseleave', function() {{ this.style.backgroundColor = 'white'; }});
                div.addEventListener('click', function() {{
                  // Находим регион на карте и центрируем на нём
                  let foundLayer = null;
                  map.eachLayer(layer => {{
                    if (layer.feature && 
                        layer.feature.properties && 
                        layer.feature.properties.name === name) {{
                      foundLayer = layer;
                      const bounds = layer.getBounds();
                      map.fitBounds(bounds);
                    }}
                  }});
                  
                  // Открываем попап после центрирования карты
                  if (foundLayer) {{
                    setTimeout(() => {{
                      const center = foundLayer.getBounds().getCenter();
                      const popupContent = foundLayer.feature.properties.popup_html;
                      foundLayer.bindPopup(popupContent).openPopup(center);
                    }}, 100);
                  }}
                  
                  searchInput.value = name;
                  searchResults.style.display = 'none';
                }});
                searchResults.appendChild(div);
              }});
              searchResults.style.display = 'block';
            }} else {{
              searchResults.style.display = 'none';
            }}
          }});
          
          // Очистить поле по нажатию «×»
          clearBtn.addEventListener('click', function() {{
            searchInput.value = '';
            clearBtn.style.display = 'none';
            searchResults.innerHTML = '';
            searchResults.style.display = 'none';
            searchInput.focus();
          }});
          
          // Скрываем результаты при клике вне поля поиска
          document.addEventListener('click', function(e) {{
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target) && !clearBtn.contains(e.target)) {{
              searchResults.style.display = 'none';
            }}
          }});
          
          // Скрываем OpenStreetMap из контроллера слоев
          document.querySelectorAll('.leaflet-control-layers-base label').forEach(label => {{
            if (label.textContent.includes('OpenStreetMap')) {{
              const parent = label.closest('div');
              if (parent) parent.style.display = 'none';
            }}
          }});
        }}, 500);
        </script>
        """
        m.get_root().html.add_child(Element(js_search))
        
        # Сохраняем карту
        m.save(output_path)
        print(f"Карта сохранена в: {output_path}")
        
        return m

def find_price_file():
    """Ищет файл с ценами на топливо с наибольшим количеством данных."""
    import glob
    import json
    
    # Возможные паттерны имен файлов (в порядке приоритета)
    patterns = [
        "all_regions_*.json",           # Приоритет файлам со всеми регионами
        "*all_regions*.json",           # Альтернативные названия
        "regional_prices_*.json",       # Стандартные файлы
        "prices_*.json", 
        "fuel_prices_*.json"
    ]
    
    best_file = None
    max_regions = 0
    
    print("Поиск файла с данными о ценах...")
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Считаем регионы со статусом success
                    success_count = sum(1 for item in data if item.get('status') == 'success')
                    print(f"  {file_path}: {success_count} регионов")
                    
                    # Бонус для файлов с "all_regions" в названии
                    priority_bonus = 1000 if "all_regions" in file_path.lower() else 0
                    
                    if success_count + priority_bonus > max_regions:
                        max_regions = success_count + priority_bonus
                        best_file = file_path
            except Exception as e:
                print(f"  {file_path}: ошибка чтения ({e})")
                continue
    
    if best_file:
        print(f"Выбран файл: {best_file}")
    else:
        print("Файлы с данными не найдены")
    
    return best_file

def check_and_parse_all_regions():
    """Проверяет количество регионов и при необходимости запускает парсинг всех регионов."""
    import subprocess
    import sys
    
    prices_path = find_price_file()
    
    if prices_path:
        try:
            with open(prices_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                success_count = sum(1 for item in data if item.get('status') == 'success')
                
                print(f"Найден файл с {success_count} регионами")
                
                # Если регионов мало, предлагаем запустить полный парсинг
                if success_count < 20:
                    print(f"\n⚠️  В файле только {success_count} регионов из ~85 возможных")
                    print("💡 Рекомендуется получить данные по всем регионам")
                    
                    response = input("Запустить парсинг всех регионов? (y/N): ").strip().lower()
                    if response in ['y', 'yes', 'да']:
                        print("\n🚀 Запуск парсинга всех регионов...")
                        print("⏳ Это может занять несколько минут...")
                        
                        try:
                            result = subprocess.run([
                                sys.executable, "regional_parser.py", 
                                "--all-regions", "--max-regions", "50"
                            ], capture_output=True, text=True, timeout=300)
                            
                            if result.returncode == 0:
                                print("✅ Парсинг завершен успешно!")
                                # Обновляем путь к файлу
                                new_prices_path = find_price_file()
                                if new_prices_path and new_prices_path != prices_path:
                                    print(f"Новый файл: {new_prices_path}")
                                    return new_prices_path
                            else:
                                print(f"❌ Ошибка парсинга: {result.stderr}")
                                
                        except subprocess.TimeoutExpired:
                            print("⏰ Превышено время ожидания парсинга")
                        except Exception as e:
                            print(f"❌ Ошибка запуска парсера: {e}")
                
        except Exception as e:
            print(f"Ошибка чтения файла: {e}")
    
    return prices_path

def main():
    """Основная функция для создания карт."""
    
    # Пути к файлам
    geojson_path = "data/geojson/russia_reg v2.geojson"
    
    # Проверяем наличие geojson файла
    if not Path(geojson_path).exists():
        print(f"Ошибка: файл {geojson_path} не найден")
        
        # Попробуем альтернативный путь
        alt_geojson = "src/russia_reg v2.geojson"
        if Path(alt_geojson).exists():
            geojson_path = alt_geojson
            print(f"Используем альтернативный путь: {geojson_path}")
        else:
            return
    
    # Ищем файл с ценами и при необходимости запускаем парсинг
    prices_path = check_and_parse_all_regions()
    
    if not prices_path or not Path(prices_path).exists():
        print("Ошибка: файл с ценами не найден")
        print("Ожидаемые файлы: all_regions_*.json, regional_prices_*.json, prices_*.json")
        return
    
    print(f"\nИспользуется файл с ценами: {prices_path}")
    
    # Создаем генератор карт
    generator = FuelPriceMapGenerator(geojson_path, prices_path)
    generator.load_data()
    
    # Создаем папку для сохранения карт
    Path("data/maps").mkdir(parents=True, exist_ok=True)
    
    # Создаем интерактивную карту со всеми видами топлива
    print("\nСоздание интерактивной карты со всеми видами топлива...")
    generator.create_interactive_map(output_path="data/maps/fuel_price_interactive_map.html")
    
    print("\nГенерация карты завершена!")
    print("Созданный файл:")
    print("  - data/maps/fuel_price_interactive_map.html")
    print(f"  - Откройте в браузере: file://{Path('data/maps/fuel_price_interactive_map.html').absolute()}")

if __name__ == "__main__":
    main()