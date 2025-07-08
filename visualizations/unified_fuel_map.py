#!/usr/bin/env python3
"""
Упрощенная карта с ценами на топливо - вся информация в одном попапе.
Убирает сложность слоев и показывает все виды топлива при клике на регион.
Включает режим сравнения двух регионов.
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
        
    def create_comparison_table_html(self, region1_data, region2_data):
        """Создает HTML таблицу для сравнения двух регионов."""
        if not region1_data or not region2_data:
            return ""
            
        # Собираем все виды топлива из обоих регионов
        all_fuels = set()
        if region1_data.get('prices'):
            all_fuels.update(region1_data['prices'].keys())
        if region2_data.get('prices'):
            all_fuels.update(region2_data['prices'].keys())
        
        # Сортировка топлива по приоритету
        fuel_order = ["АИ-92", "АИ-92+", "АИ-95", "АИ-95+", "АИ-98", "АИ-100", "АИ-100+", "ДТ", "ДТ+", "Газ", "Пропан"]
        sorted_fuels = [f for f in fuel_order if f in all_fuels]
        
        table_html = "<table style='width: 100%; border-collapse: collapse; font-size: 12px;'>"
        table_html += "<tr style='background: #f8f9fa;'>"
        table_html += "<th style='padding: 8px; border: 1px solid #ddd; text-align: left;'>Топливо</th>"
        table_html += f"<th style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{region1_data['name']}</th>"
        table_html += f"<th style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{region2_data['name']}</th>"
        table_html += "<th style='padding: 8px; border: 1px solid #ddd; text-align: center;'>Разница</th>"
        table_html += "</tr>"
        
        for fuel_type in sorted_fuels:
            display_name = self.fuel_display_names.get(fuel_type, fuel_type)
            color = self.fuel_colors.get(fuel_type, "#666")
            
            price1 = region1_data.get('prices', {}).get(fuel_type)
            price2 = region2_data.get('prices', {}).get(fuel_type)
            
            # Определяем единицы измерения
            if fuel_type == "Газ":
                unit = "руб/м³"
            elif fuel_type == "Пропан":
                unit = "руб/кг"
            else:
                unit = "руб/л"
            
            # Ячейка с ценой 1
            price1_cell = f"{price1:.2f} {unit}" if price1 else "—"
            price2_cell = f"{price2:.2f} {unit}" if price2 else "—"
            
            # Вычисляем разницу
            diff_cell = "—"
            diff_style = ""
            if price1 and price2:
                diff = price2 - price1
                if abs(diff) < 0.01:
                    diff_cell = "≈ 0"
                    diff_style = "color: #6c757d;"
                elif diff > 0:
                    diff_cell = f"+{diff:.2f}"
                    diff_style = "color: #dc3545; font-weight: bold;"
                else:
                    diff_cell = f"{diff:.2f}"
                    diff_style = "color: #28a745; font-weight: bold;"
            
            table_html += f"""
            <tr>
                <td style='padding: 6px 8px; border: 1px solid #ddd;'>
                    <span style='color: {color}; margin-right: 6px;'>●</span>{display_name}
                </td>
                <td style='padding: 6px 8px; border: 1px solid #ddd; text-align: center;'>{price1_cell}</td>
                <td style='padding: 6px 8px; border: 1px solid #ddd; text-align: center;'>{price2_cell}</td>
                <td style='padding: 6px 8px; border: 1px solid #ddd; text-align: center; {diff_style}'>{diff_cell}</td>
            </tr>"""
        
        table_html += "</table>"
        return table_html

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
                # Создание подробного попапа с кнопкой сравнения
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
                
                # Добавляем кнопку сравнения
                popup_html += f"""
                <div style='text-align: center; margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;'>
                    <button onclick='toggleRegionComparison("{region}")' 
                            id='compare-btn-{region.replace(" ", "-").replace("(", "").replace(")", "")}' 
                            style='background: #7db8e8; color: white; border: none; padding: 8px 16px; 
                                   border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; 
                                   transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'
                            onmouseover='this.style.background="#6ba6d6"; this.style.boxShadow="0 4px 8px rgba(0,0,0,0.15)";'
                            onmouseout='updateCompareButtonStyle("{region}")'>
                        <span id='compare-text-{region.replace(" ", "-").replace("(", "").replace(")", "")}'>📊 Добавить в сравнение</span>
                    </button>
                </div>"""
                
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
                Кликните на регион для просмотра цен • Режим сравнения регионов
            </p>
        </div>'''
        
        folium.Element(header_html).add_to(m)
        
        # Окно сравнения регионов
        comparison_html = '''
        <div id="comparison-panel" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; 
                                         background: white; padding: 15px; border-radius: 8px; 
                                         box-shadow: 0 4px 15px rgba(0,0,0,0.2); min-width: 400px; max-width: 500px; 
                                         display: none;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin: 0; color: #2c3e50; font-size: 16px;">📊 Сравнение регионов</h4>
                <button onclick="closeComparison()" style="background: #e74c3c; color: white; border: none; 
                                                           padding: 4px 8px; border-radius: 3px; cursor: pointer;">✕</button>
            </div>
            <div id="comparison-content">
                <div style="margin-bottom: 10px; color: #7f8c8d; font-size: 14px;">
                    Выберите два региона для сравнения цен на топливо
                </div>
                <div id="selected-regions" style="margin-bottom: 15px;">
                    <div id="region1-slot" style="padding: 8px; border: 2px dashed #ddd; border-radius: 4px; margin-bottom: 8px; color: #999;">
                        Регион 1: не выбран
                    </div>
                    <div id="region2-slot" style="padding: 8px; border: 2px dashed #ddd; border-radius: 4px; color: #999;">
                        Регион 2: не выбран
                    </div>
                </div>
                <div id="comparison-table"></div>
                <div style="text-align: center; margin-top: 10px;">
                    <button onclick="clearComparison()" style="background: #6c757d; color: white; border: none; 
                                                              padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        Очистить выбор
                    </button>
                </div>
            </div>
        </div>'''
        
        folium.Element(comparison_html).add_to(m)
        
        # Легенда с типами топлива (размещена выше окна сравнения)
        legend_html = '''
        <div style="position: fixed; bottom: 350px; right: 20px; z-index: 1000; 
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

        # JavaScript для поиска, интерактивности и сравнения
        map_var = m.get_name()
        js_code = f"""
        <script>
        setTimeout(function() {{
            const map = {map_var};
            let selectedRegions = [];
            let regionLayers = new Map();
            
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
                    
                    regionLayers.set(regionName, layer);
                    
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
                        // Проверяем, выбран ли регион для сравнения или просто кликнут
                        const isSelected = selectedRegions.some(r => r.name === l.feature.properties.region_name);
                        const isClicked = l.isClicked;
                        
                        if (isSelected || isClicked) {{
                            // Оставляем темно-зеленую заливку для выбранных или кликнутых регионов
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
                        
                        // Всегда меняем цвет на темно-зеленый при клике
                        e.target.setStyle({{
                            fillColor: '#006400',
                            fillOpacity: 0.8,
                            weight: 4,
                            color: '#006400'
                        }});
                        
                        // Помечаем как кликнутый
                        e.target.isClicked = true;
                    }});
                }}
            }});
            
            // Функция переключения региона в сравнении
            window.toggleRegionComparison = function(regionName) {{
                const regionData = regions.find(r => r.name === regionName);
                if (!regionData) return;
                
                // Проверяем, выбран ли уже этот регион
                const isAlreadySelected = selectedRegions.some(r => r.name === regionName);
                
                if (isAlreadySelected) {{
                    // Убираем регион из сравнения
                    selectedRegions = selectedRegions.filter(r => r.name !== regionName);
                    const layer = regionLayers.get(regionName);
                    if (layer) {{
                        layer.setStyle({{
                            fillColor: '#90EE90',
                            fillOpacity: layer.feature.properties.has_data ? 0.6 : 0.4,
                            weight: layer.feature.properties.has_data ? 1.5 : 1,
                            color: '#2c3e50'
                        }});
                        layer.isClicked = false;
                    }}
                }} else {{
                    // Добавляем регион в сравнение
                    // Если уже выбраны 2 региона, заменяем первый
                    if (selectedRegions.length >= 2) {{
                        const oldRegion = selectedRegions.shift();
                        const oldLayer = regionLayers.get(oldRegion.name);
                        if (oldLayer) {{
                            oldLayer.setStyle({{
                                fillColor: '#90EE90',
                                fillOpacity: oldLayer.feature.properties.has_data ? 0.6 : 0.4,
                                weight: oldLayer.feature.properties.has_data ? 1.5 : 1,
                                color: '#2c3e50'
                            }});
                            oldLayer.isClicked = false;
                        }}
                        updateCompareButtonForRegion(oldRegion.name, false);
                    }}
                    
                    selectedRegions.push(regionData);
                    
                    // Меняем цвет региона на темно-зеленый
                    const layer = regionLayers.get(regionName);
                    if (layer) {{
                        layer.setStyle({{
                            fillColor: '#006400',
                            fillOpacity: 0.8,
                            weight: 4,
                            color: '#006400'
                        }});
                        layer.isClicked = true;
                    }}
                }}
                
                updateCompareButtonForRegion(regionName, !isAlreadySelected);
                updateComparisonPanel();
            }};
            
            // Функция обновления стиля кнопки сравнения
            window.updateCompareButtonStyle = function(regionName) {{
                const isSelected = selectedRegions.some(r => r.name === regionName);
                const cleanName = regionName.replace(/\s+/g, '-').replace(/[()]/g, '');
                const button = document.getElementById(`compare-btn-${{cleanName}}`);
                if (button) {{
                    if (isSelected) {{
                        button.style.background = '#5a9fd8';
                    }} else {{
                        button.style.background = '#7db8e8';
                    }}
                }}
            }};
            
            // Функция обновления кнопки для конкретного региона
            function updateCompareButtonForRegion(regionName, isSelected) {{
                const cleanName = regionName.replace(/\s+/g, '-').replace(/[()]/g, '');
                const button = document.getElementById(`compare-btn-${{cleanName}}`);
                const text = document.getElementById(`compare-text-${{cleanName}}`);
                
                if (button && text) {{
                    if (isSelected) {{
                        button.style.background = '#5a9fd8';
                        text.innerHTML = '📊 Убрать из сравнения';
                    }} else {{
                        button.style.background = '#7db8e8';
                        text.innerHTML = '📊 Добавить в сравнение';
                    }}
                }}
            }}
            
            // Функция обновления панели сравнения
            function updateComparisonPanel() {{
                const panel = document.getElementById('comparison-panel');
                const region1Slot = document.getElementById('region1-slot');
                const region2Slot = document.getElementById('region2-slot');
                const comparisonTable = document.getElementById('comparison-table');
                
                // Показываем панель если есть хотя бы один регион
                if (selectedRegions.length > 0) {{
                    panel.style.display = 'block';
                }} else {{
                    panel.style.display = 'none';
                    return;
                }}
                
                // Обновляем слоты регионов
                if (selectedRegions.length > 0) {{
                    region1Slot.innerHTML = `Регион 1: <strong>${{selectedRegions[0].name}}</strong>`;
                    region1Slot.style.borderColor = '#28a745';
                    region1Slot.style.backgroundColor = '#f8fff9';
                    region1Slot.style.color = '#155724';
                }} else {{
                    region1Slot.innerHTML = 'Регион 1: не выбран';
                    region1Slot.style.borderColor = '#ddd';
                    region1Slot.style.backgroundColor = 'white';
                    region1Slot.style.color = '#999';
                }}
                
                if (selectedRegions.length > 1) {{
                    region2Slot.innerHTML = `Регион 2: <strong>${{selectedRegions[1].name}}</strong>`;
                    region2Slot.style.borderColor = '#28a745';
                    region2Slot.style.backgroundColor = '#f8fff9';
                    region2Slot.style.color = '#155724';
                }} else {{
                    region2Slot.innerHTML = 'Регион 2: не выбран';
                    region2Slot.style.borderColor = '#ddd';
                    region2Slot.style.backgroundColor = 'white';
                    region2Slot.style.color = '#999';
                }}
                
                // Создаем таблицу сравнения, если выбраны оба региона
                if (selectedRegions.length === 2) {{
                    comparisonTable.innerHTML = createComparisonTable(selectedRegions[0], selectedRegions[1]);
                }} else {{
                    comparisonTable.innerHTML = '';
                }}
            }}
            
            // Функция создания таблицы сравнения
            function createComparisonTable(region1, region2) {{
                if (!region1.hasData && !region2.hasData) {{
                    return '<div style="text-align: center; color: #6c757d; padding: 20px;">У обоих регионов нет данных о ценах</div>';
                }}
                
                // Собираем все виды топлива из обоих регионов
                const allFuels = new Set();
                Object.keys(region1.prices || {{}}).forEach(fuel => allFuels.add(fuel));
                Object.keys(region2.prices || {{}}).forEach(fuel => allFuels.add(fuel));
                
                const fuelOrder = ["АИ-92", "АИ-92+", "АИ-95", "АИ-95+", "АИ-98", "АИ-100", "АИ-100+", "ДТ", "ДТ+", "Газ", "Пропан"];
                const sortedFuels = fuelOrder.filter(f => allFuels.has(f));
                
                const fuelDisplayNames = {{
                    "АИ-92": "АИ‑92", "АИ-92+": "АИ‑92+", "АИ-95": "АИ‑95",
                    "АИ-95+": "АИ‑95+", "АИ-98": "АИ‑98", "АИ-100": "АИ‑100",
                    "АИ-100+": "АИ‑100+", "ДТ": "Дизель", "ДТ+": "Дизель+",
                    "Газ": "Газ", "Пропан": "Пропан"
                }};
                
                const fuelColors = {{
                    "АИ-92": "#228B22", "АИ-92+": "#32CD32",
                    "АИ-95": "#4169E1", "АИ-95+": "#1E90FF", 
                    "АИ-98": "#800080", "АИ-100": "#FFA500", 
                    "АИ-100+": "#DAA520", "ДТ": "#8B4513", 
                    "ДТ+": "#A0522D", "Газ": "#FFD700", "Пропан": "#FF69B4"
                }};
                
                let table = '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">';
                table += '<tr style="background: #f8f9fa;">';
                table += '<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Топливо</th>';
                table += `<th style="padding: 8px; border: 1px solid #ddd; text-align: center;">${{region1.name}}</th>`;
                table += `<th style="padding: 8px; border: 1px solid #ddd; text-align: center;">${{region2.name}}</th>`;
                table += '<th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Разница</th>';
                table += '</tr>';
                
                sortedFuels.forEach(fuelType => {{
                    const displayName = fuelDisplayNames[fuelType] || fuelType;
                    const color = fuelColors[fuelType] || '#666';
                    
                    const price1 = region1.prices[fuelType];
                    const price2 = region2.prices[fuelType];
                    
                    // Определяем единицы измерения
                    let unit = 'руб/л';
                    if (fuelType === 'Газ') unit = 'руб/м³';
                    if (fuelType === 'Пропан') unit = 'руб/кг';
                    
                    const price1Cell = price1 ? `${{price1.toFixed(2)}} ${{unit}}` : '—';
                    const price2Cell = price2 ? `${{price2.toFixed(2)}} ${{unit}}` : '—';
                    
                    let diffCell = '—';
                    let diffStyle = '';
                    if (price1 && price2) {{
                        const diff = price2 - price1;
                        if (Math.abs(diff) < 0.01) {{
                            diffCell = '≈ 0';
                            diffStyle = 'color: #6c757d;';
                        }} else if (diff > 0) {{
                            diffCell = `+${{diff.toFixed(2)}}`;
                            diffStyle = 'color: #dc3545; font-weight: bold;';
                        }} else {{
                            diffCell = `${{diff.toFixed(2)}}`;
                            diffStyle = 'color: #28a745; font-weight: bold;';
                        }}
                    }}
                    
                    table += `<tr>
                        <td style='padding: 6px 8px; border: 1px solid #ddd;'>
                            <span style='color: ${{color}}; margin-right: 6px;'>●</span>${{displayName}}
                        </td>
                        <td style='padding: 6px 8px; border: 1px solid #ddd; text-align: center;'>${{price1Cell}}</td>
                        <td style='padding: 6px 8px; border: 1px solid #ddd; text-align: center;'>${{price2Cell}}</td>
                        <td style='padding: 6px 8px; border: 1px solid #ddd; text-align: center; ${{diffStyle}}'>${{diffCell}}</td>
                    </tr>`;
                }});
                
                table += '</table>';
                return table;
            }}
            
            // Функция закрытия панели сравнения
            window.closeComparison = function() {{
                document.getElementById('comparison-panel').style.display = 'none';
                clearComparison();
            }};
            
            // Функция очистки сравнения
            window.clearComparison = function() {{
                selectedRegions.forEach(region => {{
                    const layer = regionLayers.get(region.name);
                    if (layer) {{
                        layer.setStyle({{
                            fillColor: '#90EE90',
                            fillOpacity: layer.feature.properties.has_data ? 0.6 : 0.4,
                            weight: layer.feature.properties.has_data ? 1.5 : 1,
                            color: '#2c3e50'
                        }});
                        layer.isClicked = false;
                    }}
                    updateCompareButtonForRegion(region.name, false);
                }});
                selectedRegions = [];
                updateComparisonPanel();
            }};
            
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
    
    print("[SUCCESS] Обновленная карта создана: data/maps/unified_fuel_map.html")
    print(f"[BROWSER] Откройте: file://{Path('data/maps/unified_fuel_map.html').absolute()}")
    print("[NEW FEATURES] Новые функции карты:")
    print("  • Светло-зеленая заливка для всех регионов (включая Магадан)")
    print("  • Кнопки масштаба смещены ниже (не перекрываются поиском)")
    print("  • Режим сравнения регионов с кнопкой 'Сравнить регион'")
    print("  • Темно-зеленое выделение выбранных регионов")
    print("  • Таблица сравнения цен на топливо с разницей")
    print("  • Отображение всех видов топлива для совместимости")

if __name__ == "__main__":
    main()