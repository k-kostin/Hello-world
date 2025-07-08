#!/usr/bin/env python3
"""
Менеджер истории региональных цен
Организует хранение и управление историческими данными по датам
"""

import json
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger


class RegionalHistoryManager:
    """Менеджер для работы с историей региональных цен"""
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = Path(base_data_dir)
        self.history_dir = self.base_data_dir / "regional_history"
        self.metadata_file = self.history_dir / "history_index.json"
        self.latest_dir = self.history_dir / "latest"
        
        # Создаем необходимые папки
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Создает необходимые директории"""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.latest_dir.mkdir(parents=True, exist_ok=True)
    
    def get_date_directory(self, target_date: Optional[date] = None) -> Path:
        """Получает папку для определенной даты"""
        if target_date is None:
            target_date = date.today()
        
        year_month_day_dir = (
            self.history_dir / 
            str(target_date.year) / 
            f"{target_date.month:02d}" / 
            f"{target_date.day:02d}"
        )
        year_month_day_dir.mkdir(parents=True, exist_ok=True)
        return year_month_day_dir
    
    def save_regional_data_with_history(self, results: List[Any], 
                                      additional_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Сохраняет региональные данные с поддержкой истории
        
        Args:
            results: Результаты парсинга региональных цен
            additional_metadata: Дополнительные метаданные
        
        Returns:
            Dict с путями к сохраненным файлам
        """
        if not results:
            logger.warning("Нет данных для сохранения")
            return {}
        
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")
        full_timestamp = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Определяем полноту выгрузки
        successful_count = len([r for r in results if r.status == 'success'])
        total_expected_regions = 85
        
        # Создаем префикс файла
        if successful_count >= 80:
            prefix = "all_regions"
            completeness = "ПОЛНАЯ"
        elif successful_count >= 60:
            prefix = f"regions_{successful_count}of{total_expected_regions}"
            completeness = "КРУПНАЯ"
        else:
            prefix = f"regions_partial_{successful_count}reg"
            completeness = "ЧАСТИЧНАЯ"
        
        # Получаем папку для текущей даты
        date_dir = self.get_date_directory()
        
        # Формируем имена файлов
        base_filename = f"{prefix}_{full_timestamp}"
        json_filename = f"{base_filename}.json"
        excel_filename = f"{base_filename}.xlsx"
        csv_filename = f"{base_filename}.csv"
        
        # Пути к файлам в истории
        history_json_path = date_dir / json_filename
        history_excel_path = date_dir / excel_filename
        history_csv_path = date_dir / csv_filename
        
        # Пути к файлам в latest
        latest_json_path = self.latest_dir / f"latest_regions_{date_str}.json"
        latest_excel_path = self.latest_dir / f"latest_regions_{date_str}.xlsx"
        latest_csv_path = self.latest_dir / f"latest_regions_{date_str}.csv"
        
        # Подготавливаем данные для JSON
        json_data = []
        for result in results:
            json_data.append({
                'region_id': result.region_id,
                'region_name': result.region_name,
                'fuel_prices': result.fuel_prices,
                'url': result.url,
                'timestamp': result.timestamp,
                'status': result.status
            })
        
        # Сохраняем JSON в историю
        with open(history_json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # Копируем JSON в latest
        shutil.copy2(history_json_path, latest_json_path)
        
        # Сохраняем Excel и CSV (импортируем функции из основного парсера)
        try:
            self._save_excel_report(results, history_excel_path)
            shutil.copy2(history_excel_path, latest_excel_path)
        except Exception as e:
            logger.error(f"Ошибка сохранения Excel: {e}")
        
        try:
            self._save_csv_report(results, history_csv_path)
            shutil.copy2(history_csv_path, latest_csv_path)
        except Exception as e:
            logger.error(f"Ошибка сохранения CSV: {e}")
        
        # Создаем метаданные для этой выгрузки
        metadata = {
            'timestamp': timestamp.isoformat(),
            'date': date_str,
            'time': time_str,
            'completeness': completeness,
            'total_regions': len(results),
            'successful_regions': successful_count,
            'failed_regions': len(results) - successful_count,
            'prefix': prefix,
            'files': {
                'json': str(history_json_path.relative_to(self.history_dir)),
                'excel': str(history_excel_path.relative_to(self.history_dir)),
                'csv': str(history_csv_path.relative_to(self.history_dir))
            },
            'fuel_types': self._extract_fuel_types(results),
            'price_statistics': self._calculate_price_statistics(results)
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Обновляем индекс истории
        self._update_history_index(metadata)
        
        # Логируем результаты
        logger.info(f"[HISTORY] Данные сохранены в историю: {date_dir}")
        logger.info(f"[HISTORY] JSON: {history_json_path.name}")
        logger.info(f"[HISTORY] Тип выгрузки: {completeness} ({successful_count} регионов)")
        logger.info(f"[LATEST] Актуальная копия: {latest_json_path.name}")
        
        return {
            'history_json': str(history_json_path),
            'history_excel': str(history_excel_path),
            'history_csv': str(history_csv_path),
            'latest_json': str(latest_json_path),
            'latest_excel': str(latest_excel_path),
            'latest_csv': str(latest_csv_path),
            'metadata': metadata
        }
    
    def _extract_fuel_types(self, results: List[Any]) -> List[str]:
        """Извлекает типы топлива из результатов"""
        fuel_types = set()
        for result in results:
            if result.status == 'success' and result.fuel_prices:
                fuel_types.update(result.fuel_prices.keys())
        return sorted(list(fuel_types))
    
    def _calculate_price_statistics(self, results: List[Any]) -> Dict[str, Dict[str, float]]:
        """Вычисляет статистику цен по типам топлива"""
        fuel_stats = {}
        
        for result in results:
            if result.status == 'success' and result.fuel_prices:
                for fuel_type, price in result.fuel_prices.items():
                    if fuel_type not in fuel_stats:
                        fuel_stats[fuel_type] = []
                    fuel_stats[fuel_type].append(price)
        
        statistics = {}
        for fuel_type, prices in fuel_stats.items():
            if prices:
                statistics[fuel_type] = {
                    'avg': round(sum(prices) / len(prices), 2),
                    'min': round(min(prices), 2),
                    'max': round(max(prices), 2),
                    'count': len(prices)
                }
        
        return statistics
    
    def _save_excel_report(self, results: List[Any], filename: Path):
        """Сохраняет Excel отчет"""
        try:
            import pandas as pd
            
            # Подготавливаем данные
            main_data = []
            for result in results:
                if result.status == 'success' and result.fuel_prices:
                    base_row = {
                        'region_id': result.region_id,
                        'region_name': result.region_name,
                        'timestamp': result.timestamp,
                        'url': result.url,
                        'status': result.status
                    }
                    
                    for fuel_type, price in result.fuel_prices.items():
                        if fuel_type != 'АИ-80':  # Исключаем АИ-80
                            base_row[f'{fuel_type}'] = price
                    
                    main_data.append(base_row)
            
            if main_data:
                df = pd.DataFrame(main_data)
                df.to_excel(filename, index=False)
                
        except ImportError:
            logger.warning("Pandas не установлен, Excel файл не создан")
        except Exception as e:
            logger.error(f"Ошибка создания Excel: {e}")
    
    def _save_csv_report(self, results: List[Any], filename: Path):
        """Сохраняет CSV отчет"""
        try:
            import pandas as pd
            
            # Подготавливаем данные
            csv_data = []
            for result in results:
                if result.status == 'success' and result.fuel_prices:
                    base_row = {
                        'region_id': result.region_id,
                        'region_name': result.region_name,
                        'timestamp': result.timestamp,
                        'url': result.url,
                        'status': result.status
                    }
                    
                    for fuel_type, price in result.fuel_prices.items():
                        if fuel_type != 'АИ-80':  # Исключаем АИ-80
                            base_row[f'{fuel_type}'] = price
                    
                    csv_data.append(base_row)
            
            if csv_data:
                df = pd.DataFrame(csv_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
        except ImportError:
            logger.warning("Pandas не установлен, CSV файл не создан")
        except Exception as e:
            logger.error(f"Ошибка создания CSV: {e}")
    
    def _update_history_index(self, metadata: Dict):
        """Обновляет индекс истории"""
        try:
            # Читаем существующий индекс
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            else:
                index_data = {
                    'created': datetime.now().isoformat(),
                    'entries': []
                }
            
            # Добавляем новую запись
            index_data['entries'].append(metadata)
            index_data['last_updated'] = datetime.now().isoformat()
            index_data['total_entries'] = len(index_data['entries'])
            
            # Ограничиваем размер индекса (оставляем последние 1000 записей)
            if len(index_data['entries']) > 1000:
                index_data['entries'] = index_data['entries'][-1000:]
                index_data['total_entries'] = 1000
                logger.info("[HISTORY] Индекс урезан до 1000 последних записей")
            
            # Сохраняем обновленный индекс
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Ошибка обновления индекса истории: {e}")
    
    def find_by_date(self, target_date: date) -> List[Dict]:
        """Находит все выгрузки за определенную дату"""
        if not self.metadata_file.exists():
            return []
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            date_str = target_date.strftime("%Y%m%d")
            matching_entries = [
                entry for entry in index_data['entries']
                if entry['date'] == date_str
            ]
            
            return matching_entries
            
        except Exception as e:
            logger.error(f"Ошибка поиска по дате: {e}")
            return []
    
    def get_latest_by_date(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """Получает последнюю выгрузку за дату"""
        if target_date is None:
            target_date = date.today()
        
        entries = self.find_by_date(target_date)
        if entries:
            # Сортируем по времени и возвращаем последнюю
            return max(entries, key=lambda x: x['timestamp'])
        return None
    
    def get_history_summary(self, days: int = 30) -> Dict:
        """Получает сводку истории за последние N дней"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Фильтруем записи за последние N дней
            cutoff_date = (datetime.now() - timedelta(days=days)).date()
            recent_entries = [
                entry for entry in index_data['entries']
                if datetime.fromisoformat(entry['timestamp']).date() >= cutoff_date
            ]
            
            if not recent_entries:
                return {}
            
            # Группируем по датам
            by_date = {}
            for entry in recent_entries:
                date_key = entry['date']
                if date_key not in by_date:
                    by_date[date_key] = []
                by_date[date_key].append(entry)
            
            # Создаем сводку
            summary = {
                'period_days': days,
                'total_entries': len(recent_entries),
                'dates_with_data': len(by_date),
                'avg_entries_per_day': round(len(recent_entries) / len(by_date), 1),
                'by_date': {
                    date_key: {
                        'entries_count': len(entries),
                        'latest_completeness': entries[-1]['completeness'],
                        'latest_regions': entries[-1]['successful_regions']
                    }
                    for date_key, entries in sorted(by_date.items())
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка создания сводки истории: {e}")
            return {}
    
    def cleanup_old_data(self, keep_days: int = 90):
        """Очищает старые данные (старше keep_days дней)"""
        cutoff_date = date.today() - timedelta(days=keep_days)
        removed_count = 0
        
        try:
            # Проходим по всем годам и месяцам
            for year_dir in self.history_dir.iterdir():
                if not year_dir.is_dir() or not year_dir.name.isdigit():
                    continue
                
                year = int(year_dir.name)
                if year < cutoff_date.year:
                    # Удаляем весь год
                    shutil.rmtree(year_dir)
                    removed_count += len(list(year_dir.rglob("*.json")))
                    logger.info(f"[CLEANUP] Удален год: {year}")
                    continue
                
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir() or not month_dir.name.isdigit():
                        continue
                    
                    month = int(month_dir.name)
                    for day_dir in month_dir.iterdir():
                        if not day_dir.is_dir() or not day_dir.name.isdigit():
                            continue
                        
                        day = int(day_dir.name)
                        dir_date = date(year, month, day)
                        
                        if dir_date < cutoff_date:
                            # Удаляем папку дня
                            files_count = len(list(day_dir.glob("*.json")))
                            shutil.rmtree(day_dir)
                            removed_count += files_count
                            logger.info(f"[CLEANUP] Удалена дата: {dir_date}")
            
            logger.info(f"[CLEANUP] Очистка завершена. Удалено {removed_count} файлов")
            
        except Exception as e:
            logger.error(f"Ошибка очистки старых данных: {e}")

