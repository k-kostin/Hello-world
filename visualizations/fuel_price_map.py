#!/usr/bin/env python3
"""
Скрипт для создания интерактивной карты России с ценами на топливо.
Использует leafmap для создания карты и отображения данных при наведении мышки.
"""

import json
import leafmap
import geopandas as gpd
import pandas as pd
from pathlib import Path
import numpy as np
from typing import Dict, List, Optional

class FuelPriceMapGenerator:
    """Класс для создания карт с ценами на топливо."""
    
    def __init__(self, geojson_path: str, mapping_path: str):
        """
        Инициализация генератора карт.
        
        Args:
            geojson_path: Путь к файлу с границами регионов
            mapping_path: Путь к файлу с маппингом регионов
        """
        self.geojson_path = geojson_path
        self.mapping_path = mapping_path
        self.gdf = None
        self.mapping_data = None
        
    def load_data(self):
        """Загружает данные из файлов."""
        print("Загрузка геоданных...")
        self.gdf = gpd.read_file(self.geojson_path)
        
        print("Загрузка маппинга...")
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            self.mapping_data = json.load(f)
        
        print(f"Загружено {len(self.gdf)} регионов из geojson")
        print(f"Маппинг содержит {len(self.mapping_data['mapping'])} сопоставлений")
    
    def add_fuel_prices_to_geodata(self, fuel_type: str = "АИ-95") -> gpd.GeoDataFrame:
        """
        Добавляет цены на топливо к геоданным.
        
        Args:
            fuel_type: Тип топлива для отображения
            
        Returns:
            GeoDataFrame с добавленными ценами
        """
        if self.gdf is None or self.mapping_data is None:
            raise ValueError("Данные не загружены. Вызовите load_data() сначала.")
        
        # Создаем копию геоданных
        gdf_with_prices = self.gdf.copy()
        
        # Преобразуем все временные столбцы в строки для избежания проблем с JSON
        for col in gdf_with_prices.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf_with_prices[col]):
                gdf_with_prices[col] = gdf_with_prices[col].astype(str)
        
        # Добавляем колонки для цен
        gdf_with_prices['fuel_price'] = np.nan
        gdf_with_prices['fuel_type'] = fuel_type
        gdf_with_prices['region_info'] = ''
        
        # Заполняем данные из маппинга
        mapping = self.mapping_data['mapping']
        
        for idx, row in gdf_with_prices.iterrows():
            region_name = row['name']
            
            if region_name in mapping:
                fuel_data = mapping[region_name]
                fuel_prices = fuel_data.get('fuel_prices', {})
                
                # Устанавливаем цену на указанный тип топлива
                if fuel_type in fuel_prices:
                    gdf_with_prices.at[idx, 'fuel_price'] = fuel_prices[fuel_type]
                
                # Создаем информационную строку со всеми ценами
                info_lines = [f"<b>{region_name}</b>"]
                for fuel, price in fuel_prices.items():
                    info_lines.append(f"{fuel}: {price} руб/л")
                
                gdf_with_prices.at[idx, 'region_info'] = "<br>".join(info_lines)
            else:
                gdf_with_prices.at[idx, 'region_info'] = f"<b>{region_name}</b><br>Нет данных о ценах"
        
        return gdf_with_prices
    
    def create_interactive_map(self, fuel_type: str = "АИ-95", output_path: str = "fuel_price_map.html") -> leafmap.Map:
        """
        Создает интерактивную карту с ценами на топливо.
        
        Args:
            fuel_type: Тип топлива для отображения
            output_path: Путь для сохранения HTML файла
            
        Returns:
            Объект карты leafmap
        """
        # Получаем данные с ценами
        gdf_with_prices = self.add_fuel_prices_to_geodata(fuel_type)
        
        # Создаем карту
        m = leafmap.Map(center=[61, 105], zoom=3)
        
        # Определяем цветовую схему
        # Фильтруем только регионы с данными о ценах
        price_data = gdf_with_prices[gdf_with_prices['fuel_price'].notna()]
        
        if len(price_data) > 0:
            min_price = price_data['fuel_price'].min()
            max_price = price_data['fuel_price'].max()
            
            print(f"Диапазон цен на {fuel_type}: {min_price:.2f} - {max_price:.2f} руб/л")
            
            # Добавляем слой с данными
            m.add_gdf(
                gdf_with_prices,
                layer_name=f"Цены на {fuel_type}",
                fill_colors=['red', 'yellow', 'green'],  # От высоких к низким ценам
                fill_opacity=0.7,
                stroke_width=1,
                stroke_color='black',
                stroke_opacity=0.8,
                info_mode='on_click',  # Показывать информацию при клике
                style_column='fuel_price',  # Колонка для стилизации
                legend_title=f"Цена {fuel_type} (руб/л)",
                classification_method='quantiles',  # Метод классификации
                num_classes=5
            )
        else:
            # Если нет данных о ценах, просто показываем границы
            m.add_gdf(
                gdf_with_prices,
                layer_name="Регионы России",
                fill_opacity=0.3,
                stroke_width=1,
                stroke_color='black',
                info_mode='on_click'
            )
            print("Предупреждение: нет данных о ценах для отображения")
        
        # Добавляем контроль слоев
        m.add_layer_control()
        
        # Сохраняем карту
        m.to_html(output_path)
        print(f"Карта сохранена в: {output_path}")
        
        return m
    
    def create_comparison_map(self, fuel_types: List[str], output_path: str = "fuel_comparison_map.html"):
        """
        Создает карту для сравнения цен на разные типы топлива.
        
        Args:
            fuel_types: Список типов топлива для сравнения
            output_path: Путь для сохранения HTML файла
        """
        m = leafmap.Map(center=[61, 105], zoom=3)
        
        for fuel_type in fuel_types:
            gdf_with_prices = self.add_fuel_prices_to_geodata(fuel_type)
            
            # Фильтруем только регионы с данными о ценах
            price_data = gdf_with_prices[gdf_with_prices['fuel_price'].notna()]
            
            if len(price_data) > 0:
                m.add_gdf(
                    gdf_with_prices,
                    layer_name=f"Цены на {fuel_type}",
                    fill_opacity=0.6,
                    stroke_width=1,
                    stroke_color='black',
                    stroke_opacity=0.8,
                    info_mode='on_click',
                    style_column='fuel_price',
                    legend_title=f"Цена {fuel_type} (руб/л)",
                    classification_method='quantiles',
                    num_classes=5
                )
        
        m.add_layer_control()
        m.to_html(output_path)
        print(f"Карта сравнения сохранена в: {output_path}")
        
        return m
    
    def get_available_fuel_types(self) -> List[str]:
        """Возвращает список доступных типов топлива."""
        if self.mapping_data is None:
            raise ValueError("Данные не загружены. Вызовите load_data() сначала.")
        
        fuel_types = set()
        
        for region_data in self.mapping_data['mapping'].values():
            fuel_prices = region_data.get('fuel_prices', {})
            fuel_types.update(fuel_prices.keys())
        
        return sorted(list(fuel_types))

def main():
    """Основная функция для создания карт."""
    
    # Пути к файлам
    geojson_path = "data/geojson/russia_reg v2.geojson"
    mapping_path = "data/region_mapping.json"
    
    # Проверяем наличие файлов
    if not Path(geojson_path).exists():
        print(f"Ошибка: файл {geojson_path} не найден")
        return
    
    if not Path(mapping_path).exists():
        print(f"Ошибка: файл {mapping_path} не найден")
        print("Сначала запустите region_mapping.py для создания маппинга")
        return
    
    # Создаем генератор карт
    generator = FuelPriceMapGenerator(geojson_path, mapping_path)
    generator.load_data()
    
    # Получаем доступные типы топлива
    available_fuels = generator.get_available_fuel_types()
    print(f"Доступные типы топлива: {available_fuels}")
    
    # Создаем папку для сохранения карт
    Path("data/maps").mkdir(exist_ok=True)
    
    # Создаем карту для АИ-95
    if "АИ-95" in available_fuels:
        print("\nСоздание карты для АИ-95...")
        generator.create_interactive_map(
            fuel_type="АИ-95",
            output_path="data/maps/ai95_price_map.html"
        )
    
    # Создаем карту для ДТ (дизельное топливо)
    if "ДТ" in available_fuels:
        print("\nСоздание карты для ДТ...")
        generator.create_interactive_map(
            fuel_type="ДТ",
            output_path="data/maps/diesel_price_map.html"
        )
    
    # Создаем карту сравнения основных типов топлива
    main_fuels = ["АИ-92", "АИ-95", "ДТ"]
    available_main_fuels = [f for f in main_fuels if f in available_fuels]
    
    if available_main_fuels:
        print(f"\nСоздание карты сравнения для {available_main_fuels}...")
        generator.create_comparison_map(
            fuel_types=available_main_fuels,
            output_path="data/maps/fuel_comparison_map.html"
        )
    
    print("\nГенерация карт завершена!")
    print("Созданные файлы:")
    maps_dir = Path("data/maps")
    if maps_dir.exists():
        for map_file in maps_dir.glob("*.html"):
            print(f"  - {map_file}")

if __name__ == "__main__":
    main()