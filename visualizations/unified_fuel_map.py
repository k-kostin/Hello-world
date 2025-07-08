#!/usr/bin/env python3
"""
Упрощенная карта с ценами на топливо - вся информация в одном попапе.
Убирает сложность слоев и показывает все виды топлива при клике на регион.
"""

import json
import folium
from branca.element import Element
from pathlib import Path
from typing import Dict, List, Optional
import glob

class UnifiedFuelMapGenerator:
    """Генератор единой карты с ценами на топливо."""
    
    def __init__(self, geojson_path: str, prices_path: str):
        self.geojson_path = geojson_path
        self.prices_path = prices_path
        self.geojson_data = None
        self.price_data = None
        
        # Цвета для топлива
        self.fuel_colors = {
            "АИ-92": "#228B22", "АИ-92+": "#32CD32",
            "АИ-95": "#4169E1", "АИ-95+": "#1E90FF", 
            "АИ-98": "#800080", "АИ-100": "#FFA500", 
            "АИ-100+": "#DAA520", "ДТ": "#8B4513", 
            "ДТ+": "#A0522D", "Газ": "#FFD700", "Пропан": "#FF69B4"
        }
        
        self.fuel_display_names = {
            "АИ-92": "АИ‑92", "АИ-92+": "АИ‑92+", "АИ-95": "АИ‑95",
            "АИ-95+": "АИ‑95+", "АИ-98": "АИ‑98", "АИ-100": "АИ‑100",
            "АИ-100+": "АИ‑100+", "ДТ": "Дизель", "ДТ+": "Дизель+",
            "Газ": "Газ", "Пропан": "Пропан"
        }
    
    def load_data(self):
        """Загружает данные."""
        with open(self.geojson_path, 'r', encoding='utf-8') as f:
            self.geojson_data = json.load(f)
        
        with open(self.prices_path, 'r', encoding='utf-8') as f:
            price_list = json.load(f)
        
        self.price_data = {}
        for item in price_list:
            if item.get('status') == 'success':
                self.price_data[item['region_name']] = item['fuel_prices']
    
    def normalize_region_name(self, name: str) -> str:
        """Нормализует название региона для поиска."""
        if not name:
            return ""
        
        # Базовая очистка
        normalized = name.strip()
        
        # Словарь синонимов для регионов
        synonyms = {
            "Москва": ["Московская область", "г. Москва", "Москва г"],
            "Санкт-Петербург": ["Ленинградская область", "г. Санкт-Петербург", "СПб"],
            "Ханты-Мансийский автономный округ - Югра": ["ХМАО", "Югра", "Ханты-Мансийский автономный округ (Югра)"],
            "Удмуртская Республика": ["Республика Удмуртия"],
            "Ямало-Ненецкий автономный округ": ["ЯНАО", "Ямало-Ненецкий АО"],
            "Республика Саха (Якутия)": ["Якутия", "Саха"],
            "Карачаево-Черкесская Республика": ["КЧР", "Карачаево-Черкесия"],
            "Кабардино-Балкарская Республика": ["КБР", "Кабардино-Балкария"],
            "Чеченская Республика": ["Чечня"],
            "Республика Северная Осетия - Алания": ["Северная Осетия", "РСО-Алания"],
        }
        
        # Ищем по синонимам
        for canonical, variants in synonyms.items():
            if normalized in variants or normalized == canonical:
                return canonical
        
        return normalized
    
    def find_region_prices(self, region_name: str) -> Optional[Dict]:
        """Ищет цены для региона."""
        if not self.price_data:
            return None
            
        # Прямое совпадение
        if region_name in self.price_data:
            return self.price_data[region_name]
        
        # Нормализованный поиск
        normalized_target = self.normalize_region_name(region_name)
        for price_region, prices in self.price_data.items():
            if self.normalize_region_name(price_region) == normalized_target:
                return prices
        
        # Поиск без учета регистра
        for price_region, prices in self.price_data.items():
            if region_name.lower() == price_region.lower():
                return prices
            
        # Поиск вхождения
        for price_region, prices in self.price_data.items():
            if region_name.lower() in price_region.lower() or price_region.lower() in region_name.lower():
                return prices
        
        return None

    def create_map(self, output_path: str = "unified_fuel_map.html"):
        """Создает единую карту с ограничениями камеры."""
        # Определяем границы карты для России (приблизительные координаты)
        # Севернее, южнее, западнее, восточнее
        north = 82.0   # Северная граница (острова в Северном Ледовитом океане)
        south = 41.0   # Южная граница (Кавказ)
        west = 19.0    # Западная граница (Калининградская область)
        east = 170.0   # Восточная граница (Чукотка)
        
        # Создаем карту с ограничениями камеры
        m = folium.Map(
            location=[61, 105], 
            zoom_start=3, 
            tiles='OpenStreetMap',
            max_bounds=True,  # Включаем ограничения
            min_zoom=2,       # Минимальный зуум
            max_zoom=10       # Максимальный зуум
        )
        
        # Устанавливаем границы карты
        m.fit_bounds([[south, west], [north, east]])
        
        # Подготовка данных
        gcopy = json.loads(json.dumps(self.geojson_data))
        
        for feat in gcopy["features"]:
            props = feat["properties"]
            region = props.get("name", "")
            region_prices = self.find_region_prices(region)
            
            if region_prices:
                # Создание подробного попапа
                popup_html = f"<div style='font-family: Arial; min-width: 300px; max-width: 400px;'>"
                popup_html += f"<h3 style='color: #2c3e50; margin: 0 0 15px 0; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 8px;'>{region}</h3>"
                popup_html += "<table style='width: 100%; border-collapse: collapse;'>"
                
                # Сортировка топлива по приоритету
                fuel_order = ["АИ-92", "АИ-92+", "АИ-95", "АИ-95+", "АИ-98", "АИ-100", "АИ-100+", "ДТ", "ДТ+", "Газ", "Пропан"]
                sorted_fuels = [(f, region_prices[f]) for f in fuel_order if f in region_prices]
                
                for fuel_type, price in sorted_fuels:
                    display_name = self.fuel_display_names.get(fuel_type, fuel_type)
                    color = self.fuel_colors.get(fuel_type, "#666")
                    
                    # Определяем правильные единицы измерения
                    if fuel_type == "Газ":
                        unit = "руб/м³"
                    elif fuel_type == "Пропан":
                        unit = "руб/кг"
                    else:
                        unit = "руб/л"
                    
                    popup_html += f"""
                    <tr style='border-bottom: 1px solid #eee;'>
                        <td style='padding: 8px 15px 8px 0; font-weight: bold; font-size: 14px;'>
                            <span style='color: {color}; margin-right: 8px; font-size: 16px;'>●</span>{display_name}:
                        </td>
                        <td style='padding: 8px 0; text-align: right; font-weight: bold; color: #27ae60; font-size: 15px;'>
                            {price:.2f} {unit}
                        </td>
                    </tr>"""
                
                popup_html += "</table>"
                popup_html += "</div>"
                
                # Цвет региона - базовая светло-зеленая заливка
                props["popup_html"] = popup_html
                props["base_color"] = "#90EE90"  # Светло-зеленый для всех регионов с данными
                props["has_data"] = True
                props["fuel_count"] = len(sorted_fuels)
                props["region_name"] = region
                props["fuel_prices"] = region_prices
            else:
                popup_html = f"<div style='text-align: center; padding: 20px; font-family: Arial;'>"
                popup_html += f"<h3 style='color: #e74c3c; margin: 0 0 10px 0;'>{region}</h3>"
                popup_html += "<p style='color: #7f8c8d; font-size: 14px; margin: 0;'>Нет данных о ценах на топливо</p>"
                popup_html += "<p style='color: #95a5a6; font-size: 12px; margin: 10px 0 0 0;'>Данные могут появиться после обновления</p>"
                popup_html += "</div>"
                
                props["popup_html"] = popup_html
                props["base_color"] = "#90EE90"  # Светло-зеленый и для регионов без данных (включая Магадан)
                props["has_data"] = False
                props["fuel_count"] = 0
                props["region_name"] = region
                props["fuel_prices"] = {}
        
        # Стили для регионов - все получают светло-зеленую заливку
        def style_function(feature):
            has_data = feature["properties"].get("has_data", False)
            
            # Все регионы получают одинаковую светло-зеленую заливку
            return {
                "fillColor": "#90EE90",  # Светло-зеленый для всех
                "color": "#2c3e50",
                "weight": 1.5 if has_data else 1,
                "fillOpacity": 0.6 if has_data else 0.4
            }
        
        # Добавление слоя
        folium.GeoJson(
            gcopy,
            style_function=style_function,
            popup=folium.GeoJsonPopup(
                fields=["popup_html"], aliases=[""], labels=False,
                style="max-width: 450px;"
            ),
            tooltip=folium.GeoJsonTooltip(
                fields=["name"],
                aliases=["Регион:"],
                sticky=True,
                style="background-color: rgba(0,0,0,0.8); color: white; padding: 8px; border-radius: 4px; font-size: 14px;"
            )
        ).add_to(m)
        
        # Заголовок и легенда
        header_html = '''
        <div style="position: fixed; top: 10px; left: 50px; z-index: 1000; 
                    background: white; padding: 15px; border-radius: 8px; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2); max-width: 400px;">
            <h2 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 18px;">
                🗺️ Цены на топливо по регионам России
            </h2>
            <p style="margin: 0; color: #7f8c8d; font-size: 14px;">
                Кликните на регион для просмотра цен
            </p>
        </div>'''
        
        folium.Element(header_html).add_to(m)
        
        # Легенда с типами топлива
        legend_html = '''
        <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; 
                    background: white; padding: 15px; border-radius: 8px; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2); min-width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 16px;">Типы топлива:</h4>
            <div style="font-size: 13px; line-height: 20px;">
                <div><span style="color: #228B22;">●</span> АИ-92 / АИ-92+</div>
                <div><span style="color: #4169E1;">●</span> АИ-95 / АИ-95+</div>
                <div><span style="color: #800080;">●</span> АИ-98</div>
                <div><span style="color: #FFA500;">●</span> АИ-100+</div>
                <div><span style="color: #8B4513;">●</span> Дизель / Дизель+</div>
                <div><span style="color: #FF69B4;">●</span> Пропан</div>
            </div>
        </div>'''
        
        folium.Element(legend_html).add_to(m)
        
        # Поиск регионов
        search_html = """
        <div style="position: fixed; top: 10px; left: 10px; z-index: 1000; width: 250px;">
            <div style="position: relative;">
                <span style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); z-index: 1001; color: #666; pointer-events: none;">🔍</span>
                <input type="text" id="search-input" placeholder="Поиск региона..." 
                       style="width: 100%; padding: 10px 10px 10px 35px; border: 2px solid #ddd; border-radius: 6px; 
                              font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            </div>
            <div id="search-results" style="max-height: 200px; overflow-y: auto; margin-top: 5px; 
                                          display: none; background: white; border: 2px solid #ddd; 
                                          border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);"></div>
        </div>
        """
        m.get_root().html.add_child(Element(search_html))
        
        # CSS для улучшения интерфейса
        style_css = """
        <style>
        /* Перемещение кнопок масштаба значительно ниже поля поиска */
        .leaflet-control-zoom {
            top: 320px !important;
            left: 10px !important;
        }
        
        /* Убираем прямоугольную обводку при клике */
        .leaflet-interactive:focus {
            outline: none !important;
        }
        
        /* Улучшаем внешний вид кнопок масштаба */
        .leaflet-control-zoom a {
            background-color: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid #ccc !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        }
        
        /* Стили для выделенного региона */
        .region-selected {
            stroke: #006400 !important;
            stroke-width: 4 !important;
            fill: #006400 !important;
            fill-opacity: 0.8 !important;
        }
        </style>
        """
        m.get_root().html.add_child(Element(style_css))

        # JavaScript для поиска и интерактивности
        map_var = m.get_name()
        js_code = f"""
        <script>
        setTimeout(function() {{
            const map = {map_var};
            
            // Собираем все регионы
            const regions = [];
            map.eachLayer(layer => {{
                if (layer.feature && layer.feature.properties && layer.feature.properties.name) {{
                    const regionName = layer.feature.properties.name;
                    regions.push({{
                        name: regionName,
                        layer: layer,
                        hasData: layer.feature.properties.has_data,
                        prices: layer.feature.properties.fuel_prices || {{}}
                    }});
                    
                    // Hover эффекты
                    layer.on('mouseover', function(e) {{
                        const l = e.target;
                        l.setStyle({{
                            weight: 3,
                            color: '#000000',
                            fillOpacity: 0.9
                        }});
                        l.bringToFront();
                    }});
                    
                    layer.on('mouseout', function(e) {{
                        const l = e.target;
                        const isClicked = l.isClicked;
                        
                        if (isClicked) {{
                            // Оставляем темно-зеленую заливку для кликнутых регионов
                            l.setStyle({{
                                weight: 4,
                                color: '#006400',
                                fillColor: '#006400',
                                fillOpacity: 0.8
                            }});
                        }} else {{
                            // Возвращаем обычную светло-зеленую заливку
                            l.setStyle({{
                                weight: l.feature.properties.has_data ? 1.5 : 1,
                                color: '#2c3e50',
                                fillColor: '#90EE90',
                                fillOpacity: l.feature.properties.has_data ? 0.6 : 0.4
                            }});
                        }}
                    }});
                    
                    // Обработчик клика для выделения региона
                    layer.on('click', function(e) {{
                        const regionName = e.target.feature.properties.region_name;
                        highlightRegion(e.target, regionName);
                    }});
                }}
            }});
            
            // Функция выделения региона (используется как при клике, так и при поиске)
            function highlightRegion(layer, regionName) {{
                // Сбрасываем выделение у всех других регионов
                regions.forEach(region => {{
                    if (region.name !== regionName) {{
                        region.layer.setStyle({{
                            fillColor: '#90EE90',
                            fillOpacity: region.layer.feature.properties.has_data ? 0.6 : 0.4,
                            weight: region.layer.feature.properties.has_data ? 1.5 : 1,
                            color: '#2c3e50'
                        }});
                        region.layer.isClicked = false;
                    }}
                }});
                
                // Меняем цвет на темно-зеленый при клике
                layer.setStyle({{
                    fillColor: '#006400',
                    fillOpacity: 0.8,
                    weight: 4,
                    color: '#006400'
                }});
                
                // Помечаем как кликнутый
                layer.isClicked = true;
                
                console.log('Region highlighted:', regionName);
            }}
            
            // Поиск
            const searchInput = document.getElementById('search-input');
            const searchResults = document.getElementById('search-results');
            
            searchInput.addEventListener('input', function() {{
                const query = this.value.trim().toLowerCase();
                
                if (!query) {{
                    searchResults.style.display = 'none';
                    return;
                }}
                
                const matches = regions.filter(r => 
                    r.name.toLowerCase().includes(query)
                ).slice(0, 8);
                
                if (matches.length > 0) {{
                    searchResults.innerHTML = '';
                    matches.forEach(match => {{
                        const div = document.createElement('div');
                        div.style.cssText = `
                            padding: 12px; cursor: pointer; border-bottom: 1px solid #eee;
                            ${{match.hasData ? 'color: #2c3e50;' : 'color: #7f8c8d;'}}
                        `;
                        div.innerHTML = `
                            <strong>${{match.name}}</strong>
                            <div style="font-size: 12px; color: #95a5a6;">
                                ${{match.hasData ? 'Есть данные о ценах' : 'Нет данных'}}
                            </div>
                        `;
                        
                        div.addEventListener('mouseenter', () => div.style.backgroundColor = '#f8f9fa');
                        div.addEventListener('mouseleave', () => div.style.backgroundColor = 'white');
                        
                        div.addEventListener('click', () => {{
                            const bounds = match.layer.getBounds();
                            map.fitBounds(bounds);
                            
                            // Выделяем регион и открываем попап
                            setTimeout(() => {{
                                const center = bounds.getCenter();
                                match.layer.bindPopup(match.layer.feature.properties.popup_html).openPopup(center);
                                
                                // Выделяем регион так же, как при клике
                                highlightRegion(match.layer, match.name);
                            }}, 300);
                            
                            searchInput.value = match.name;
                            searchResults.style.display = 'none';
                        }});
                        
                        searchResults.appendChild(div);
                    }});
                    searchResults.style.display = 'block';
                }} else {{
                    searchResults.style.display = 'none';
                }}
            }});
            
            // Скрыть результаты при клике вне
            document.addEventListener('click', function(e) {{
                if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {{
                    searchResults.style.display = 'none';
                }}
            }});
        }}, 1000);
        </script>
        """
        m.get_root().html.add_child(Element(js_code))
        
        m.save(output_path)
        print(f"[OK] Единая карта сохранена: {output_path}")
        return m

def find_price_file():
    """Ищет файл с ценами для демонстрации функций карты."""
    patterns = [
        "all_regions_*.json",           # Полные выгрузки всех регионов
        "regional_prices_*.json",       # Частичные выгрузки для тестирования
        "regions_*.json"                # Альтернативный формат
    ]
    
    best_file = None
    max_regions = 0
    
    print(f"[VISUAL] Поиск файлов с региональными ценами для демонстрации...")
    
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    count = sum(1 for item in data if item.get('status') == 'success')
                    
                    print(f"[CHECK] {file_path}: {count} регионов")
                    
                    if count > max_regions:
                        max_regions = count
                        best_file = file_path
            except Exception as e:
                print(f"[ERROR] Ошибка чтения {file_path}: {e}")
                continue
    
    if best_file and max_regions > 0:
        print(f"[SUCCESS] Файл для демонстрации: {best_file} ({max_regions} регионов)")
        return best_file, max_regions
    
    print(f"[FAIL] НЕ НАЙДЕН файл с региональными ценами!")
    return None, 0

def main():
    """Основная функция."""
    geojson_path = "data/geojson/russia_reg v2.geojson"
    
    if not Path(geojson_path).exists():
        geojson_path = "src/russia_reg v2.geojson"
        if not Path(geojson_path).exists():
            print("[ERROR] Файл границ регионов не найден")
            return
    
    # Поиск файла с ценами для демонстрации
    prices_path, region_count = find_price_file()
    
    if not prices_path or region_count == 0:
        print("[ERROR] ВИЗУАЛИЗАЦИЯ ОСТАНОВЛЕНА - нет файла с региональными ценами")
        print("[INFO] Для полной карты запустите: python regional_parser.py --all-regions")
        return
    
    print(f"[INFO] Используется файл: {prices_path} ({region_count} регионов)")
    print(f"[OK] Создаем демонстрационную карту с новыми функциями...")
    
    generator = UnifiedFuelMapGenerator(geojson_path, prices_path)
    generator.load_data()
    
    Path("data/maps").mkdir(parents=True, exist_ok=True)
    generator.create_map("data/maps/unified_fuel_map.html")
    
    print("[SUCCESS] Упрощенная карта создана: data/maps/unified_fuel_map.html")
    print(f"[BROWSER] Откройте: file://{Path('data/maps/unified_fuel_map.html').absolute()}")
    print("[FEATURES] Функции карты:")
    print("  • Светло-зеленая заливка для всех регионов")
    print("  • Кнопки масштаба смещены ниже (не перекрываются поиском)")
    print("  • Ограничения камеры - карта не выходит за пределы России")
    print("  • Темно-зеленое выделение кликнутого региона")
    print("  • Поиск регионов с автодополнением")
    print("  • Отображение всех видов топлива в одном попапе")

if __name__ == "__main__":
    main()