"""
Утилиты для обработки и анализа данных
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import polars as pl
import pandas as pd
from loguru import logger


class DataProcessor:
    """Класс для обработки и анализа данных цен АЗС"""
    
    @staticmethod
    def load_latest_data(data_dir: str = "data") -> Optional[pl.DataFrame]:
        """
        Загружает последний файл с объединенными данными
        
        Args:
            data_dir: Директория с данными
            
        Returns:
            DataFrame или None если файлы не найдены
        """
        if not os.path.exists(data_dir):
            logger.error(f"Директория {data_dir} не существует")
            return None
        
        # Ищем файлы с объединенными данными (поддерживает новую и старую схему именования)
        all_files = os.listdir(data_dir)
        
        # Новая схема: all_gas_stations_, gas_stations_ (включая варианты с именами сетей)
        combined_files = [f for f in all_files if 
                         (f.startswith("all_gas_stations_") or f.startswith("gas_stations_")) 
                         and f.endswith(".xlsx")]
        
        if not combined_files:
            logger.error("Файлы с объединенными данными не найдены")
            return None
        
        # Сортируем по дате в названии файла (извлекаем дату из конца имени файла)
        def extract_timestamp(filename):
            try:
                # Извлекаем YYYYMMDD_HHMMSS из конца файла
                name_parts = filename.replace('.xlsx', '').split('_')
                # Ищем части, которые выглядят как дата и время
                if len(name_parts) >= 2:
                    date_part = name_parts[-2]  # YYYYMMDD
                    time_part = name_parts[-1]  # HHMMSS
                    if len(date_part) == 8 and len(time_part) == 6:
                        return datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
            except:
                pass
            return datetime.min
        
        combined_files.sort(key=extract_timestamp, reverse=True)
        latest_file = combined_files[0]
        
        filepath = os.path.join(data_dir, latest_file)
        logger.info(f"Загружаем данные из {filepath}")
        
        try:
            return pl.read_excel(filepath)
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
            return None
    
    @staticmethod
    def clean_data(df: pl.DataFrame) -> pl.DataFrame:
        """
        Очищает данные от некорректных записей
        
        Args:
            df: Исходный DataFrame
            
        Returns:
            Очищенный DataFrame
        """
        logger.info(f"Очистка данных. Исходно записей: {len(df)}")
        
        # Удаляем записи без цены или с нулевой ценой
        df_clean = df.filter(
            (pl.col("price").is_not_null()) & 
            (pl.col("price") > 0) &
            (pl.col("fuel_type").is_not_null()) &
            (pl.col("fuel_type") != "")
        )
        
        # Удаляем дубликаты
        df_clean = df_clean.unique(subset=["station_id", "fuel_type"])
        
        # Фильтруем аномальные цены (слишком высокие или низкие)
        df_clean = df_clean.filter(
            (pl.col("price") >= 30) &  # Минимальная разумная цена
            (pl.col("price") <= 200)   # Максимальная разумная цена
        )
        
        logger.info(f"После очистки записей: {len(df_clean)}")
        return df_clean
    
    @staticmethod
    def get_price_statistics(df: pl.DataFrame) -> Dict[str, Any]:
        """
        Вычисляет статистику по ценам
        
        Args:
            df: DataFrame с данными
            
        Returns:
            Словарь со статистикой
        """
        stats = {}
        
        # Общая статистика
        stats["total_records"] = len(df)
        stats["total_stations"] = df["station_id"].n_unique()
        stats["total_networks"] = df["network_name"].n_unique()
        stats["total_cities"] = df["city"].n_unique()
        
        # Статистика по типам топлива
        fuel_stats = df.group_by("fuel_type").agg([
            pl.count().alias("count"),
            pl.col("price").mean().alias("avg_price"),
            pl.col("price").min().alias("min_price"),
            pl.col("price").max().alias("max_price"),
            pl.col("price").std().alias("std_price")
        ]).sort("count", descending=True)
        
        stats["fuel_types"] = fuel_stats.to_dicts()
        
        # Статистика по сетям
        network_stats = df.group_by("network_name").agg([
            pl.count().alias("count"),
            pl.col("station_id").n_unique().alias("stations"),
            pl.col("price").mean().alias("avg_price")
        ]).sort("count", descending=True)
        
        stats["networks"] = network_stats.to_dicts()
        
        # Топ-10 самых дорогих городов
        city_stats = df.group_by("city").agg([
            pl.col("price").mean().alias("avg_price"),
            pl.count().alias("count")
        ]).filter(pl.col("count") >= 5).sort("avg_price", descending=True).head(10)
        
        stats["top_expensive_cities"] = city_stats.to_dicts()
        
        return stats
    
    @staticmethod
    def compare_networks(df: pl.DataFrame, fuel_type: str = "АИ-95") -> pl.DataFrame:
        """
        Сравнивает цены между сетями для конкретного типа топлива
        
        Args:
            df: DataFrame с данными
            fuel_type: Тип топлива для сравнения
            
        Returns:
            DataFrame со сравнением сетей
        """
        comparison = df.filter(pl.col("fuel_type") == fuel_type).group_by("network_name").agg([
            pl.count().alias("stations_count"),
            pl.col("price").mean().alias("avg_price"),
            pl.col("price").min().alias("min_price"),
            pl.col("price").max().alias("max_price"),
            pl.col("price").std().alias("price_std"),
            pl.col("city").n_unique().alias("cities_count")
        ]).sort("avg_price")
        
        return comparison
    
    @staticmethod
    def find_cheapest_stations(df: pl.DataFrame, 
                              fuel_type: str = "АИ-95", 
                              city: Optional[str] = None,
                              limit: int = 10) -> pl.DataFrame:
        """
        Находит самые дешевые заправки
        
        Args:
            df: DataFrame с данными
            fuel_type: Тип топлива
            city: Город (опционально)
            limit: Количество результатов
            
        Returns:
            DataFrame с самыми дешевыми заправками
        """
        filtered_df = df.filter(pl.col("fuel_type") == fuel_type)
        
        if city:
            filtered_df = filtered_df.filter(pl.col("city") == city)
        
        cheapest = filtered_df.sort("price").head(limit).select([
            "network_name", "station_name", "address", "city", 
            "fuel_type", "price", "last_updated"
        ])
        
        return cheapest
    
    @staticmethod
    def analyze_price_trends(data_dir: str = "data") -> Optional[pl.DataFrame]:
        """
        Анализирует тренды цен по историческим данным
        
        Args:
            data_dir: Директория с данными
            
        Returns:
            DataFrame с трендами или None
        """
        if not os.path.exists(data_dir):
            return None
        
        # Ищем все файлы с объединенными данными (поддерживает новую и старую схему именования)
        all_files = os.listdir(data_dir)
        combined_files = [f for f in all_files if 
                         (f.startswith("all_gas_stations_") or f.startswith("gas_stations_")) 
                         and f.endswith(".xlsx")]
        
        if len(combined_files) < 2:
            logger.warning("Недостаточно исторических данных для анализа трендов")
            return None
        
        # Функция для извлечения даты из имени файла
        def extract_timestamp(filename):
            try:
                # Извлекаем YYYYMMDD_HHMMSS из конца файла
                name_parts = filename.replace('.xlsx', '').split('_')
                if len(name_parts) >= 2:
                    date_part = name_parts[-2]  # YYYYMMDD
                    time_part = name_parts[-1]  # HHMMSS
                    if len(date_part) == 8 and len(time_part) == 6:
                        return datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
            except:
                pass
            return None
        
        # Сортируем файлы по дате
        file_dates = [(f, extract_timestamp(f)) for f in combined_files]
        file_dates = [(f, d) for f, d in file_dates if d is not None]
        file_dates.sort(key=lambda x: x[1])
        
        trends_data = []
        
        for file, file_date in file_dates:
            try:
                filepath = os.path.join(data_dir, file)
                df = pl.read_excel(filepath)
                
                # Вычисляем средние цены по типам топлива
                avg_prices = df.group_by("fuel_type").agg([
                    pl.col("price").mean().alias("avg_price")
                ])
                
                for row in avg_prices.iter_rows(named=True):
                    trends_data.append({
                        "date": file_date,
                        "fuel_type": row["fuel_type"],
                        "avg_price": row["avg_price"]
                    })
                    
            except Exception as e:
                logger.warning(f"Ошибка обработки файла {file}: {e}")
                continue
        
        if not trends_data:
            return None
        
        trends_df = pl.DataFrame(trends_data).sort(["fuel_type", "date"])
        return trends_df
    
    @staticmethod
    def export_summary_report(df: pl.DataFrame, output_file: str = "price_analysis_report.xlsx"):
        """
        Экспортирует сводный отчет в Excel
        
        Args:
            df: DataFrame с данными
            output_file: Имя выходного файла
        """
        logger.info(f"Создание сводного отчета: {output_file}")
        
        try:
            # Используем pandas ExcelWriter с движком xlsxwriter, т.к. в polars (v<=1.31)
            # отсутствует контекстный менеджер ExcelWriter, а метод write_excel поддерживает
            # только одну вкладку. Pandas позволяет удобно записывать несколько листов.
            with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
                # Лист 1: Общая статистика
                stats = DataProcessor.get_price_statistics(df)
                
                general_stats = pl.DataFrame([
                    {"Метрика": "Всего записей", "Значение": stats["total_records"]},
                    {"Метрика": "Всего станций", "Значение": stats["total_stations"]},
                    {"Метрика": "Всего сетей", "Значение": stats["total_networks"]},
                    {"Метрика": "Всего городов", "Значение": stats["total_cities"]}
                ])

                # Записываем каждый polars.DataFrame через конвертацию в pandas
                general_stats.to_pandas().to_excel(writer, sheet_name="Общая статистика", index=False)
                
                # Лист 2: Статистика по топливу
                fuel_df = pl.DataFrame(stats["fuel_types"])
                fuel_df.to_pandas().to_excel(writer, sheet_name="Статистика по топливу", index=False)
                
                # Лист 3: Статистика по сетям
                networks_df = pl.DataFrame(stats["networks"])
                networks_df.to_pandas().to_excel(writer, sheet_name="Статистика по сетям", index=False)
                
                # Лист 4: Самые дорогие города
                cities_df = pl.DataFrame(stats["top_expensive_cities"])
                cities_df.to_pandas().to_excel(writer, sheet_name="Дорогие города", index=False)
                
                # Лист 5: Сравнение сетей по АИ-95
                comparison_95 = DataProcessor.compare_networks(df, "АИ-95")
                comparison_95.to_pandas().to_excel(writer, sheet_name="Сравнение АИ-95", index=False)
                
                # Лист 6: Самые дешевые заправки АИ-95
                cheapest_95 = DataProcessor.find_cheapest_stations(df, "АИ-95", limit=20)
                cheapest_95.to_pandas().to_excel(writer, sheet_name="Дешевые АИ-95", index=False)
            
            logger.info(f"Отчет сохранен: {output_file}")
            
        except Exception as e:
            logger.error(f"Ошибка создания отчета: {e}")
    
    @staticmethod
    def export_summary_csv_report(df: pl.DataFrame, output_dir: str = "reports"):
        """
        Экспортирует сводный отчет в CSV файлы
        
        Args:
            df: DataFrame с данными
            output_dir: Директория для сохранения CSV файлов
        """
        # Создаем директорию если её нет
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Создание CSV отчетов в директории: {output_dir}")
        
        try:
            # Получаем статистику
            stats = DataProcessor.get_price_statistics(df)
            
            # 1. Общая статистика
            general_stats = pl.DataFrame([
                {"Метрика": "Всего записей", "Значение": stats["total_records"]},
                {"Метрика": "Всего станций", "Значение": stats["total_stations"]},
                {"Метрика": "Всего сетей", "Значение": stats["total_networks"]},
                {"Метрика": "Всего городов", "Значение": stats["total_cities"]}
            ])
            general_stats.write_csv(f"{output_dir}/general_stats_{timestamp}.csv", encoding="utf-8-sig")
            
            # 2. Статистика по топливу
            fuel_df = pl.DataFrame(stats["fuel_types"])
            fuel_df.write_csv(f"{output_dir}/fuel_stats_{timestamp}.csv", encoding="utf-8-sig")
            
            # 3. Статистика по сетям
            networks_df = pl.DataFrame(stats["networks"])
            networks_df.write_csv(f"{output_dir}/network_stats_{timestamp}.csv", encoding="utf-8-sig")
            
            # 4. Самые дорогие города
            cities_df = pl.DataFrame(stats["top_expensive_cities"])
            cities_df.write_csv(f"{output_dir}/expensive_cities_{timestamp}.csv", encoding="utf-8-sig")
            
            # 5. Сравнение сетей по АИ-95
            comparison_95 = DataProcessor.compare_networks(df, "АИ-95")
            comparison_95.write_csv(f"{output_dir}/ai95_network_comparison_{timestamp}.csv", encoding="utf-8-sig")
            
            # 6. Самые дешевые заправки АИ-95
            cheapest_95 = DataProcessor.find_cheapest_stations(df, "АИ-95", limit=20)
            cheapest_95.write_csv(f"{output_dir}/cheapest_ai95_stations_{timestamp}.csv", encoding="utf-8-sig")
            
            # 7. Основные данные (урезанная версия для CSV)
            main_data = df.select([
                "network_name", "station_name", "address", "city", 
                "fuel_type", "price", "last_updated"
            ])
            main_data.write_csv(f"{output_dir}/all_stations_data_{timestamp}.csv", encoding="utf-8-sig")
            
            logger.info(f"CSV отчеты сохранены в {output_dir}/ с меткой времени {timestamp}")
            
        except Exception as e:
            logger.error(f"Ошибка создания CSV отчетов: {e}")
    
    @staticmethod
    def export_combined_report(df: pl.DataFrame, output_base: str = "price_analysis_report"):
        """
        Экспортирует сводный отчет и в Excel, и в CSV
        
        Args:
            df: DataFrame с данными
            output_base: Базовое имя файлов (без расширения)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Экспорт в Excel
        excel_file = f"{output_base}_{timestamp}.xlsx"
        DataProcessor.export_summary_report(df, excel_file)
        
        # Экспорт в CSV
        csv_dir = f"{output_base}_csv_{timestamp}"
        DataProcessor.export_summary_csv_report(df, csv_dir)


class DataValidator:
    """Класс для валидации данных"""
    
    @staticmethod
    def validate_data_quality(df: pl.DataFrame) -> Dict[str, Any]:
        """
        Проверяет качество данных
        
        Args:
            df: DataFrame для проверки
            
        Returns:
            Отчет о качестве данных
        """
        report = {
            "total_records": len(df),
            "issues": [],
            "quality_score": 0.0
        }
        
        # Проверка на пропущенные значения
        null_counts = df.null_count()
        for col, null_count in zip(df.columns, null_counts.row(0)):
            if null_count > 0:
                percentage = (null_count / len(df)) * 100
                report["issues"].append({
                    "type": "missing_values",
                    "column": col,
                    "count": null_count,
                    "percentage": percentage
                })
        
        # Проверка цен
        if "price" in df.columns:
            invalid_prices = df.filter(
                (pl.col("price") <= 0) | 
                (pl.col("price") > 200) |
                (pl.col("price").is_null())
            )
            
            if len(invalid_prices) > 0:
                report["issues"].append({
                    "type": "invalid_prices",
                    "count": len(invalid_prices),
                    "percentage": (len(invalid_prices) / len(df)) * 100
                })
        
        # Проверка дубликатов
        duplicates = df.group_by(["station_id", "fuel_type"]).count().filter(pl.col("count") > 1)
        if len(duplicates) > 0:
            report["issues"].append({
                "type": "duplicates",
                "count": len(duplicates),
                "percentage": (len(duplicates) / len(df)) * 100
            })
        
        # Вычисляем оценку качества
        total_issues = sum(issue["count"] for issue in report["issues"])
        report["quality_score"] = max(0, 100 - (total_issues / len(df)) * 100)
        
        return report