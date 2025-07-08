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
        
        # Словарь для сопоставления особых случаев
        special_mappings = {
            'Москва': 'Москва',
            'Санкт-Петербург': 'Санкт-Петербург',
            'Севастополь': 'Севастополь',
            'Республика Крым': 'Республика Крым',
            'Ненецкий автономный округ': 'Ненецкий автономный округ',
            'Ханты-Мансийский автономный округ — Югра': 'Ханты-Мансийский автономный округ',
            'Ямало-Ненецкий автономный округ': 'Ямало-Ненецкий автономный округ',
            'Чукотский автономный округ': 'Чукотский автономный округ',
            'Еврейская автономная область': 'Еврейская автономная область',
        }
        
        if name in special_mappings:
            return special_mappings[name]
        
        # Стандартная нормализация
        name = name.strip()
        name = re.sub(r'\s+область$', '', name)
        name = re.sub(r'\s+край$', '', name)
        name = re.sub(r'^Республика\s+', '', name)
        name = re.sub(r'\s+республика$', '', name)
        
        return name
    
    def find_region_prices(self, region_name: str) -> Optional[Dict]:
        """Находит цены для региона по имени."""
        # Прямое сопоставление
        if region_name in self.price_data:
            return self.price_data[region_name]
        
        # Нормализованное сопоставление
        normalized = self.normalize_region_name(region_name)
        for price_region, prices in self.price_data.items():
            if self.normalize_region_name(price_region) == normalized:
                return prices
        
        return None
    
    def get_available_fuel_types(self) -> List[str]:
        """Возвращает список доступных типов топлива."""
        if self.price_data is None:
            return []
        fuel_types = set()
        for prices in self.price_data.values():
            fuel_types.update(prices.keys())
        return sorted(list(fuel_types))
    
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
            
            # Функция стилизации регионов - без цветной покраски
            def style_fn(feat, fuel_type=fuel_type):
                has_price = feat["properties"].get("has_price", False)
                return {
                    "fillColor": "#e0e0e0",  # Серый цвет для всех регионов
                    "color": "#000000",      # Чёрный цвет границы
                    "weight": 0.5,           # Толщина границы
                    "fillOpacity": 0.6 if has_price else 0.1  # Прозрачность в зависимости от наличия данных
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
        
        # Скрипт функционала поиска
        js_search = f"""
        <script>
        setTimeout(function() {{
          const map = {map_var};
          
          // Собираем все названия регионов для поиска
          const regionNames = new Set();
          map.eachLayer(layer => {{
            if (layer.feature && layer.feature.properties && layer.feature.properties.name) {{
              regionNames.add(layer.feature.properties.name);
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

def main():
    """Основная функция для создания карт."""
    
    # Пути к файлам
    geojson_path = "data/geojson/russia_reg v2.geojson"
    prices_path = "regional_prices_20250707_145425.json"
    
    # Проверяем наличие файлов
    if not Path(geojson_path).exists():
        print(f"Ошибка: файл {geojson_path} не найден")
        
        # Попробуем альтернативный путь
        alt_geojson = "src/russia_reg v2.geojson"
        if Path(alt_geojson).exists():
            geojson_path = alt_geojson
            print(f"Используем альтернативный путь: {geojson_path}")
        else:
            return
    
    if not Path(prices_path).exists():
        print(f"Ошибка: файл {prices_path} не найден")
        return
    
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