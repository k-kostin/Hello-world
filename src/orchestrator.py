"""
Оркестратор для управления всеми парсерами
"""
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import polars as pl
from loguru import logger

from config import GAS_STATION_NETWORKS, OUTPUT_DIR
from .parsers.parser_factory import ParserFactory


class GasStationOrchestrator:
    """Оркестратор для координации парсеров цен АЗС"""
    
    def __init__(self, networks: Optional[List[str]] = None, parallel: bool = False, max_workers: int = 3):
        """
        Инициализация оркестратора
        
        Args:
            networks: Список сетей для парсинга. Если None, парсятся все доступные
            parallel: Запускать ли парсеры параллельно
            max_workers: Максимальное количество параллельных воркеров
        """
        self.networks = networks or list(GAS_STATION_NETWORKS.keys())
        self.parallel = parallel
        self.max_workers = max_workers
        self.results = {}
        self.errors = {}
        
        # Создаем директорию для выходных данных
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    def _setup_logging(self):
        """Настройка логирования"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/gas_stations_parsing_{timestamp}.log"
        os.makedirs("logs", exist_ok=True)
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
            level="INFO",
            rotation="100 MB"
        )
    
    def _parse_single_network(self, network_name: str) -> Optional[pl.DataFrame]:
        """
        Парсит одну сеть АЗС
        
        Args:
            network_name: Название сети
            
        Returns:
            DataFrame с данными или None в случае ошибки
        """
        try:
            if network_name not in GAS_STATION_NETWORKS:
                raise ValueError(f"Неизвестная сеть: {network_name}")
            
            config = GAS_STATION_NETWORKS[network_name]
            logger.info(f"Начинаем парсинг сети: {config['name']}")
            
            # Создаем парсер
            parser = ParserFactory.create_parser(network_name, config)
            
            # Запускаем парсинг
            df = parser.run()
            
            # Сохраняем результат
            if len(df) > 0:
                self._save_network_data(network_name, df)
                logger.info(f"Парсинг сети {config['name']} завершен успешно. Записей: {len(df)}")
                return df
            else:
                logger.warning(f"Для сети {config['name']} не получено данных")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка парсинга сети {network_name}: {e}")
            self.errors[network_name] = str(e)
            return None
    
    def _save_network_data(self, network_name: str, df: pl.DataFrame):
        """Сохраняет данные сети в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Очищаем название сети для использования в имени файла
        clean_network_name = "".join(c for c in network_name if c.isalnum() or c in "-_")
        filename = f"{clean_network_name}_{timestamp}.xlsx"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        try:
            # Убираем ненужные колонки и сохраняем
            df_clean = df.drop_nulls(subset=["price"]).filter(pl.col("price") > 0)
            df_clean.write_excel(filepath)
            logger.info(f"Данные сети {network_name} сохранены в {filepath}")
        except Exception as e:
            logger.error(f"Ошибка сохранения данных {network_name}: {e}")
    
    def _save_combined_data(self, combined_df: pl.DataFrame):
        """Сохраняет объединенные данные всех сетей"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Определяем, включены ли все доступные сети
        all_available_networks = set(GAS_STATION_NETWORKS.keys())
        requested_networks = set(self.networks)
        is_all_networks = requested_networks == all_available_networks
        
        # Генерируем подходящее имя файла
        if is_all_networks:
            filename = f"all_gas_stations_{timestamp}.xlsx"
        elif len(requested_networks) <= 3:
            # Для небольшого количества сетей включаем их названия в имя файла
            # Очищаем названия сетей от символов, не подходящих для имен файлов
            clean_networks = []
            for network in sorted(requested_networks):
                clean_name = "".join(c for c in network if c.isalnum() or c in "-_")
                clean_networks.append(clean_name)
            network_names = "_".join(clean_networks)
            filename = f"gas_stations_{network_names}_{timestamp}.xlsx"
        else:
            # Для многих сетей используем общее название
            filename = f"gas_stations_{timestamp}.xlsx"
        
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        try:
            # Очищаем и сортируем данные
            df_clean = (combined_df
                       .drop_nulls(subset=["price"])
                       .filter(pl.col("price") > 0)
                       .sort(["network_name", "city", "station_name", "fuel_type"]))
            
            df_clean.write_excel(filepath)
            
            # Логируем информацию о сохраненном файле
            if is_all_networks:
                logger.info(f"Объединенные данные ВСЕХ сетей сохранены в {filepath}")
            else:
                included_networks = list(self.results.keys())
                logger.info(f"Объединенные данные выбранных сетей сохранены в {filepath}")
                logger.info(f"Включенные сети: {', '.join(included_networks)}")
            
            # Статистика
            stats = (df_clean
                    .group_by("network_name")
                    .agg([
                        pl.count().alias("stations_count"),
                        pl.col("price").mean().alias("avg_price"),
                        pl.col("city").n_unique().alias("cities_count")
                    ]))
            
            logger.info("Статистика по сетям:")
            for row in stats.iter_rows(named=True):
                logger.info(f"  {row['network_name']}: {row['stations_count']} записей, "
                          f"средняя цена: {row['avg_price']:.2f}, городов: {row['cities_count']}")
                          
        except Exception as e:
            logger.error(f"Ошибка сохранения объединенных данных: {e}")
    
    def run_sequential(self) -> Dict[str, pl.DataFrame]:
        """Запускает парсеры последовательно"""
        logger.info("Запуск парсеров в последовательном режиме")
        
        for network_name in self.networks:
            logger.info(f"Обработка сети: {network_name}")
            df = self._parse_single_network(network_name)
            if df is not None:
                self.results[network_name] = df
        
        return self.results
    
    def run_parallel(self) -> Dict[str, pl.DataFrame]:
        """Запускает парсеры параллельно"""
        logger.info(f"Запуск парсеров в параллельном режиме (воркеров: {self.max_workers})")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Отправляем задачи
            future_to_network = {
                executor.submit(self._parse_single_network, network): network 
                for network in self.networks
            }
            
            # Собираем результаты
            for future in as_completed(future_to_network):
                network_name = future_to_network[future]
                try:
                    df = future.result()
                    if df is not None:
                        self.results[network_name] = df
                except Exception as e:
                    logger.error(f"Ошибка в параллельном выполнении для {network_name}: {e}")
                    self.errors[network_name] = str(e)
        
        return self.results
    
    def run(self) -> Dict[str, pl.DataFrame]:
        """
        Основной метод запуска парсинга
        
        Returns:
            Словарь с результатами парсинга по сетям
        """
        self._setup_logging()
        
        logger.info(f"Начинаем парсинг {len(self.networks)} сетей АЗС")
        logger.info(f"Сети для парсинга: {', '.join(self.networks)}")
        
        start_time = datetime.now()
        
        # Выбираем режим выполнения
        if self.parallel:
            self.run_parallel()
        else:
            self.run_sequential()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Объединяем все результаты
        combined_df = None
        total_records = 0
        
        if self.results:
            try:
                combined_df = pl.concat(list(self.results.values()), how="vertical")
                self._save_combined_data(combined_df)
                total_records = len(combined_df)
            except Exception as e:
                logger.warning(f"Ошибка при объединении данных: {e}")
                logger.info("Сохраняем данные каждой сети отдельно")
                # В случае ошибки объединения, вычисляем общее количество записей
                total_records = sum(len(df) for df in self.results.values())
            
            logger.info(f"Парсинг завершен за {duration}")
            logger.info(f"Успешно обработано сетей: {len(self.results)}")
            logger.info(f"Ошибок: {len(self.errors)}")
            logger.info(f"Общее количество записей: {total_records}")
            
            if self.errors:
                logger.warning(f"Ошибки по сетям: {self.errors}")
        else:
            logger.error("Не удалось получить данные ни от одной сети")
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по результатам парсинга"""
        if not self.results:
            return {"status": "no_data"}
        
        try:
            combined_df = pl.concat(list(self.results.values()), how="vertical")
            total_records = len(combined_df)
        except Exception as e:
            logger.warning(f"Ошибка при объединении данных в сводке: {e}")
            total_records = sum(len(df) for df in self.results.values())
        
        summary = {
            "total_records": total_records,
            "networks_parsed": len(self.results),
            "networks_failed": len(self.errors),
            "networks_summary": {},
            "errors": self.errors
        }
        
        for network_name, df in self.results.items():
            try:
                summary["networks_summary"][network_name] = {
                    "records": len(df),
                    "stations": df["station_id"].n_unique(),
                    "cities": df["city"].n_unique(),
                    "fuel_types": df["fuel_type"].n_unique(),
                    "avg_price": df["price"].mean() if len(df) > 0 else 0
                }
            except Exception as e:
                logger.warning(f"Ошибка при создании сводки для {network_name}: {e}")
                summary["networks_summary"][network_name] = {
                    "records": len(df),
                    "stations": 0,
                    "cities": 0,
                    "fuel_types": 0,
                    "avg_price": 0
                }
        
        return summary