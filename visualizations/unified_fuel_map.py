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
            "Ханты-Мансийский автономный округ - Югра": ["ХМАО", "Югра"],
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
        """Создает единую карту."""
        m = folium.Map(location=[61, 105], zoom_start=3, tiles='OpenStreetMap')
        
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
                popup_html += f"<div style='text-align: center; margin-top: 10px; color: #7f8c8d; font-size: 12px;'>Нажмите на другой регион для сравнения</div>"
                popup_html += "</div>"
                
                # Цвет региона по основному топливу (АИ-92 приоритет)
                main_fuel = "АИ-92" if "АИ-92" in region_prices else sorted_fuels[0][0]
                base_color = self.fuel_colors.get(main_fuel, "#3498db")
                
                props["popup_html"] = popup_html
                props["base_color"] = base_color
                props["has_data"] = True
                props["fuel_count"] = len(sorted_fuels)
            else:
                popup_html = f"<div style='text-align: center; padding: 20px; font-family: Arial;'>"
                popup_html += f"<h3 style='color: #e74c3c; margin: 0 0 10px 0;'>{region}</h3>"
                popup_html += "<p style='color: #7f8c8d; font-size: 14px; margin: 0;'>Нет данных о ценах на топливо</p>"
                popup_html += "<p style='color: #95a5a6; font-size: 12px; margin: 10px 0 0 0;'>Данные могут появиться после обновления</p>"
                popup_html += "</div>"
                
                props["popup_html"] = popup_html
                props["base_color"] = "#bdc3c7"
                props["has_data"] = False
                props["fuel_count"] = 0
        
        # Стили для регионов
        def style_function(feature):
            has_data = feature["properties"].get("has_data", False)
            color = feature["properties"].get("base_color", "#bdc3c7")
            fuel_count = feature["properties"].get("fuel_count", 0)
            
            if has_data:
                # Чем больше видов топлива, тем ярче
                opacity = min(0.8, 0.4 + (fuel_count * 0.05))
                return {
                    "fillColor": color,
                    "color": "#2c3e50",
                    "weight": 1.5,
                    "fillOpacity": opacity
                }
            else:
                return {
                    "fillColor": "#f8f9fa",
                    "color": "#dee2e6",
                    "weight": 0.8,
                    "fillOpacity": 0.3
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
                Кликните на регион для просмотра всех цен на топливо
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
            <input type="text" id="search-input" placeholder="🔍 Поиск региона..." 
                   style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 6px; 
                          font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div id="search-results" style="max-height: 200px; overflow-y: auto; margin-top: 5px; 
                                          display: none; background: white; border: 2px solid #ddd; 
                                          border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);"></div>
        </div>
        """
        m.get_root().html.add_child(Element(search_html))
        
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
                    regions.push({{
                        name: layer.feature.properties.name,
                        layer: layer,
                        hasData: layer.feature.properties.has_data
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
                        const hasData = l.feature.properties.has_data;
                        const color = l.feature.properties.base_color || '#bdc3c7';
                        const fuelCount = l.feature.properties.fuel_count || 0;
                        const opacity = hasData ? Math.min(0.8, 0.4 + (fuelCount * 0.05)) : 0.3;
                        
                        l.setStyle({{
                            weight: hasData ? 1.5 : 0.8,
                            color: hasData ? '#2c3e50' : '#dee2e6',
                            fillOpacity: opacity
                        }});
                    }});
                }}
            }});
            
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
                            
                            setTimeout(() => {{
                                const center = bounds.getCenter();
                                match.layer.bindPopup(match.layer.feature.properties.popup_html).openPopup(center);
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
    """Ищет файл с ценами, СТРОГИЙ приоритет ТОЛЬКО полным выгрузкам всех регионов."""
    patterns = [
        "all_regions_*.json",           # ТОЛЬКО полные выгрузки всех регионов (>=80 регионов)
    ]
    
    best_file = None
    max_regions = 0
    min_required_regions = 80  # СТРОГО: минимум 80 регионов для полной выгрузки
    
    print(f"[VISUAL] Поиск файлов с ПОЛНОЙ выгрузкой региональных цен (>={min_required_regions} регионов)...")
    
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    count = sum(1 for item in data if item.get('status') == 'success')
                    
                    print(f"[CHECK] {file_path}: {count} регионов")
                    
                    # СТРОГО: принимаем только файлы с полной выгрузкой
                    if count >= min_required_regions and count > max_regions:
                        max_regions = count
                        best_file = file_path
                    elif count < min_required_regions:
                        print(f"[REJECT] {file_path}: недостаточно регионов ({count} < {min_required_regions})")
            except Exception as e:
                print(f"[ERROR] Ошибка чтения {file_path}: {e}")
                continue
    
    # Если нашли полную выгрузку - возвращаем её
    if best_file and max_regions >= min_required_regions:
        print(f"[SUCCESS] Файл для визуализации: {best_file} ({max_regions} регионов)")
        return best_file, max_regions
    
    # Если полной выгрузки нет - отклоняем частичные файлы и показываем инструкцию
    print(f"[FAIL] НЕ НАЙДЕН файл с полной выгрузкой региональных цен!")
    print(f"[REQUIRE] Для создания карты нужен файл с полной выгрузкой (>={min_required_regions} регионов)")
    
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
                    count = sum(1 for item in data if item.get('status') == 'success')
                    partial_files.append((file_path, count))
            except:
                continue
    
    if partial_files:
        print(f"[INFO] Найдены файлы с частичными выгрузками (НЕ подходят для визуализации):")
        for file_path, count in sorted(partial_files, key=lambda x: x[1], reverse=True):
            print(f"  - {file_path}: {count} регионов (недостаточно)")
    
    print(f"[SOLUTION] Для получения полной выгрузки запустите:")
    print(f"  python regional_parser.py --all-regions")
    
    return None, 0

def main():
    """Основная функция."""
    geojson_path = "data/geojson/russia_reg v2.geojson"
    
    if not Path(geojson_path).exists():
        print("[ERROR] Файл границ регионов не найден")
        return
    
    # Поиск файла с ценами - ТОЛЬКО полные выгрузки
    prices_path, region_count = find_price_file()
    
    if not prices_path or region_count == 0:
        print("[ERROR] ВИЗУАЛИЗАЦИЯ ОСТАНОВЛЕНА - нет файла с полной выгрузкой региональных цен")
        print("[REQUIRE] Нужен файл с полной выгрузкой всех регионов (>=80 регионов)")
        print("[ACTION] Запустите: python regional_parser.py --all-regions")
        return
    
    print(f"[INFO] Используется файл: {prices_path} ({region_count} регионов)")
    print(f"[OK] Полная выгрузка найдена - создаем карту...")
    
    generator = UnifiedFuelMapGenerator(geojson_path, prices_path)
    generator.load_data()
    
    Path("data/maps").mkdir(parents=True, exist_ok=True)
    generator.create_map("data/maps/unified_fuel_map.html")
    
    print("[SUCCESS] Упрощенная карта создана: data/maps/unified_fuel_map.html")
    print(f"[BROWSER] Откройте: file://{Path('data/maps/unified_fuel_map.html').absolute()}")

if __name__ == "__main__":
    main()