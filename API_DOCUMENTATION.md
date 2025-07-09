# API Documentation - Gas Station Price Parser

Comprehensive documentation for all public APIs, functions, and components in the Russian Gas Station Price Parsing System.

## Table of Contents

1. [Main Entry Points](#main-entry-points)
2. [Core Classes](#core-classes)
3. [Parser Classes](#parser-classes)
4. [Utility Classes](#utility-classes)
5. [Configuration](#configuration)
6. [Data Structures](#data-structures)
7. [Examples](#examples)

---

## Main Entry Points

### `main.py`

Main application entry point for gas station price parsing.

#### Functions

##### `main()`
Main entry point for the application.

**Usage:**
```bash
python main.py --all                           # Parse all networks
python main.py --networks lukoil gazprom       # Parse specific networks
python main.py --networks bashneft --parallel  # Parallel parsing
python main.py --list                         # List available networks
```

**Arguments:**
- `--all`: Parse all available gas station networks
- `--networks`: List of specific networks to parse
- `--parallel`: Enable parallel processing
- `--workers`: Number of parallel workers (default: 3)
- `--verbose`: Enable detailed logging
- `--list`: Show available networks

##### `setup_logging()`
Configures application logging with colored output.

**Returns:** None

##### `parse_arguments()`
Parses command line arguments.

**Returns:** `argparse.Namespace` - Parsed command line arguments

##### `list_networks()`
Displays all available gas station networks with their configurations.

**Returns:** None

**Output Example:**
```
Available Gas Station Networks:
======================================================================
  lukoil            - Лукойл                    (russiabase)
                       Pages: 1
  gazprom           - Газпром                   (api)
                       API: https://gpnbonus.ru/api
```

---

## Core Classes

### `GasStationOrchestrator`

Main orchestrator class for coordinating multiple gas station parsers.

**Location:** `src/orchestrator.py`

#### Constructor

```python
GasStationOrchestrator(
    networks: Optional[List[str]] = None,
    parallel: bool = False,
    max_workers: int = 3
)
```

**Parameters:**
- `networks`: List of network names to parse. If None, parses all available networks
- `parallel`: Whether to run parsers in parallel
- `max_workers`: Maximum number of parallel workers

#### Methods

##### `run() -> Dict[str, pl.DataFrame]`
Main method to execute the parsing process.

**Returns:** Dictionary mapping network names to their parsed DataFrames

**Example:**
```python
orchestrator = GasStationOrchestrator(
    networks=['lukoil', 'gazprom'],
    parallel=True,
    max_workers=2
)
results = orchestrator.run()
```

##### `get_summary() -> Dict[str, Any]`
Returns comprehensive summary of parsing results.

**Returns:** Summary dictionary with the following structure:
```python
{
    "total_records": int,
    "networks_parsed": int,
    "networks_failed": int,
    "networks_summary": {
        "network_name": {
            "records": int,
            "stations": int,
            "cities": int,
            "fuel_types": int,
            "avg_price": float
        }
    },
    "errors": Dict[str, str]
}
```

##### `run_parallel() -> Dict[str, pl.DataFrame]`
Executes parsers in parallel mode.

**Returns:** Dictionary of parsing results

##### `run_sequential() -> Dict[str, pl.DataFrame]`
Executes parsers sequentially.

**Returns:** Dictionary of parsing results

---

## Parser Classes

### `BaseParser`

Abstract base class for all gas station parsers.

**Location:** `src/parsers/base.py`

#### Constructor

```python
BaseParser(network_name: str, config: Dict[str, Any])
```

**Parameters:**
- `network_name`: Name of the gas station network
- `config`: Configuration dictionary for the parser

#### Abstract Methods

##### `fetch_data() -> List[Dict[str, Any]]`
**Abstract method** - Must be implemented by subclasses to fetch raw data from the source.

**Returns:** List of raw data dictionaries

##### `parse_station_data(raw_data: Any) -> List[Dict[str, Any]]`
**Abstract method** - Must be implemented to parse individual station data.

**Parameters:**
- `raw_data`: Raw data from the source

**Returns:** List of parsed station data

#### Implemented Methods

##### `run() -> pl.DataFrame`
Main execution method that orchestrates the parsing process.

**Returns:** `polars.DataFrame` with normalized gas station data

**Process:**
1. Fetch raw data using `fetch_data()`
2. Parse each station using `parse_station_data()`
3. Normalize data using `normalize_data()`
4. Return cleaned DataFrame

##### `normalize_data(parsed_data: List[Dict[str, Any]]) -> pl.DataFrame`
Normalizes parsed data to the standard schema.

**Parameters:**
- `parsed_data`: List of parsed station data dictionaries

**Returns:** `polars.DataFrame` with standardized columns

**Standard Schema:**
```python
{
    "station_id": str,
    "network_name": str,
    "station_name": str,
    "address": str,
    "city": str,
    "latitude": float,
    "longitude": float,
    "fuel_type": str,
    "price": float,
    "currency": str,
    "last_updated": str,
    "source": str
}
```

##### `clean_price(price_str: str) -> Optional[float]`
Cleans and normalizes price strings to float values.

**Parameters:**
- `price_str`: Raw price string

**Returns:** `float` price value or `None` if invalid

**Example:**
```python
parser.clean_price("45,50 руб") # Returns 45.5
parser.clean_price("–")         # Returns None
parser.clean_price("invalid")   # Returns None
```

##### `clean_address(address: str) -> str`
Cleans address strings by removing newlines and tabs.

**Parameters:**
- `address`: Raw address string

**Returns:** Cleaned address string

##### `extract_city_from_address(address: str) -> str`
Extracts city name from address string.

**Parameters:**
- `address`: Full address string

**Returns:** Extracted city name

**Example:**
```python
parser.extract_city_from_address("г. Москва, ул. Ленина, 1") # Returns "Москва"
```

##### `add_delay()`
Adds random delay between requests to avoid rate limiting.

**Returns:** None

##### `retry_on_failure(func, *args, **kwargs)`
Retries function execution on failure with exponential backoff.

**Parameters:**
- `func`: Function to retry
- `*args`: Function arguments
- `**kwargs`: Function keyword arguments

**Returns:** Function result

### `RussiaBaseParser`

Parser for russiabase.ru gas station data.

**Location:** `src/parsers/russiabase_parser.py`

#### Features
- Supports both standard and regional parsing
- Automatic region detection and mapping
- Multiple data extraction methods (JSON, HTML tables, regex)
- Handles pagination and regional filtering

#### Constructor

```python
RussiaBaseParser(network_name: str, config: Dict[str, Any])
```

#### Methods

##### `fetch_data() -> List[Dict[str, Any]]`
Fetches data from russiabase.ru with automatic pagination.

**Returns:** List of raw station data

##### `parse_station_data(raw_data: Any) -> List[Dict[str, Any]]`
Parses individual station data from HTML elements.

**Parameters:**
- `raw_data`: BeautifulSoup HTML element

**Returns:** List of parsed fuel price records

### `RussiaBaseRegionalParser`

Specialized parser for regional average prices from russiabase.ru.

**Location:** `src/parsers/russiabase_parser.py`

#### Features
- Extracts average fuel prices by region
- Automatic region mapping from JSON data
- Supports all 84 Russian regions
- Fast regional data aggregation

#### Methods

##### `get_all_regions() -> Dict[int, str]`
Extracts complete region mapping from russiabase.ru.

**Returns:** Dictionary mapping region IDs to region names

**Example:**
```python
parser = RussiaBaseRegionalParser()
regions = parser.get_all_regions()
print(regions[77])  # "Москва"
print(regions[78])  # "Санкт-Петербург"
```

##### `get_region_prices(region_id: int, region_name: str) -> RegionalPriceResult`
Gets average fuel prices for a specific region.

**Parameters:**
- `region_id`: Numeric region identifier
- `region_name`: Human-readable region name

**Returns:** `RegionalPriceResult` object with fuel prices

##### `parse_multiple_regions(regions: List[Dict]) -> List[RegionalPriceResult]`
Parses multiple regions with rate limiting and error handling.

**Parameters:**
- `regions`: List of region dictionaries with 'id' and 'name' keys

**Returns:** List of `RegionalPriceResult` objects

**Example:**
```python
regions = [
    {'id': 77, 'name': 'Москва'},
    {'id': 78, 'name': 'Санкт-Петербург'}
]
results = parser.parse_multiple_regions(regions)
```

### `GazpromParser`

Parser for Gazprom gas stations using their REST API.

**Location:** `src/parsers/gazprom_parser.py`

#### Features
- REST API integration with gpnbonus.ru
- Automatic station discovery
- Detailed fuel type information

#### Methods

##### `fetch_stations() -> List[Dict]`
Fetches list of all Gazprom gas stations.

**Returns:** List of station information dictionaries

##### `fetch_station_details(station_id: str) -> Dict`
Fetches detailed information for a specific station.

**Parameters:**
- `station_id`: Unique station identifier

**Returns:** Detailed station information

### `TatneftParser`

Parser for Tatneft gas stations using their API.

**Location:** `src/parsers/tatneft_parser.py`

#### Features
- Tatneft API integration
- Fuel type mapping and validation
- Filtering for Russian stations only

#### Methods

##### `fetch_fuel_types() -> List[Dict]`
Fetches available fuel types from Tatneft API.

**Returns:** List of fuel type definitions

##### `filter_russian_stations(stations: List[Dict]) -> List[Dict]`
Filters stations to include only Russian locations.

**Parameters:**
- `stations`: List of station data

**Returns:** Filtered list of Russian stations

### `YandexParser`

Parser for gas station data from Yandex Maps using Selenium.

**Location:** `src/parsers/yandex_parser.py`

#### Features
- Selenium WebDriver automation
- Dynamic content loading
- Scroll-based data collection

#### Methods

##### `setup_driver() -> webdriver.Chrome`
Sets up Chrome WebDriver with optimal configuration.

**Returns:** Configured Chrome WebDriver instance

##### `scroll_and_collect(driver: webdriver.Chrome) -> List[Dict]`
Scrolls through Yandex Maps and collects gas station data.

**Parameters:**
- `driver`: Chrome WebDriver instance

**Returns:** List of collected station data

---

## Utility Classes

### `DataProcessor`

Comprehensive data processing and analysis utilities.

**Location:** `src/utils.py`

#### Static Methods

##### `load_latest_data(data_dir: str = "data") -> Optional[pl.DataFrame]`
Loads the most recent combined gas station data file.

**Parameters:**
- `data_dir`: Directory containing data files

**Returns:** `polars.DataFrame` with latest data or `None` if not found

**Example:**
```python
df = DataProcessor.load_latest_data()
if df:
    print(f"Loaded {len(df)} records")
```

##### `clean_data(df: pl.DataFrame) -> pl.DataFrame`
Cleans and validates gas station data.

**Parameters:**
- `df`: Raw DataFrame to clean

**Returns:** Cleaned DataFrame

**Cleaning Process:**
- Removes records with null or zero prices
- Eliminates duplicate station/fuel combinations
- Filters out unrealistic prices (< 30 or > 200 RUB)

##### `get_price_statistics(df: pl.DataFrame) -> Dict[str, Any]`
Computes comprehensive price statistics.

**Parameters:**
- `df`: DataFrame with gas station data

**Returns:** Statistics dictionary with structure:
```python
{
    "total_records": int,
    "total_stations": int,
    "total_networks": int,
    "total_cities": int,
    "fuel_types": List[Dict],    # Per fuel type stats
    "networks": List[Dict],      # Per network stats
    "top_expensive_cities": List[Dict]
}
```

##### `compare_networks(df: pl.DataFrame, fuel_type: str = "АИ-95") -> pl.DataFrame`
Compares average prices between gas station networks.

**Parameters:**
- `df`: DataFrame with gas station data
- `fuel_type`: Fuel type to compare (default: "АИ-95")

**Returns:** DataFrame with network comparison

##### `find_cheapest_stations(df: pl.DataFrame, fuel_type: str = "АИ-95", city: Optional[str] = None, limit: int = 10) -> pl.DataFrame`
Finds cheapest gas stations for specified criteria.

**Parameters:**
- `df`: DataFrame with gas station data
- `fuel_type`: Fuel type to search
- `city`: Optional city filter
- `limit`: Maximum number of results

**Returns:** DataFrame with cheapest stations

**Example:**
```python
cheapest = DataProcessor.find_cheapest_stations(
    df, 
    fuel_type="АИ-95", 
    city="Москва", 
    limit=5
)
print(cheapest)
```

##### `analyze_price_trends(data_dir: str = "data") -> Optional[pl.DataFrame]`
Analyzes price trends from historical data files.

**Parameters:**
- `data_dir`: Directory containing historical data

**Returns:** DataFrame with price trends over time

##### `export_summary_report(df: pl.DataFrame, output_file: str = "price_analysis_report.xlsx")`
Exports comprehensive analysis report to Excel.

**Parameters:**
- `df`: DataFrame with gas station data
- `output_file`: Output Excel file name

**Creates Excel file with sheets:**
- General Statistics
- Fuel Type Statistics
- Network Statistics
- Expensive Cities
- AI-95 Network Comparison
- Cheapest AI-95 Stations

##### `export_summary_csv_report(df: pl.DataFrame, output_dir: str = "reports")`
Exports analysis report as multiple CSV files.

**Parameters:**
- `df`: DataFrame with gas station data
- `output_dir`: Output directory for CSV files

##### `export_combined_report(df: pl.DataFrame, output_base: str = "price_analysis_report")`
Exports both Excel and CSV reports.

**Parameters:**
- `df`: DataFrame with gas station data
- `output_base`: Base filename (without extension)

### `DataValidator`

Data quality validation utilities.

**Location:** `src/utils.py`

#### Static Methods

##### `validate_data_quality(df: pl.DataFrame) -> Dict[str, Any]`
Validates data quality and generates quality report.

**Parameters:**
- `df`: DataFrame to validate

**Returns:** Quality report dictionary:
```python
{
    "total_records": int,
    "issues": List[Dict],        # List of data quality issues
    "quality_score": float       # Overall quality score (0-100)
}
```

**Quality Checks:**
- Missing values detection
- Invalid price validation (≤ 0, > 200, null)
- Duplicate detection
- Data consistency verification

**Example:**
```python
report = DataValidator.validate_data_quality(df)
print(f"Quality Score: {report['quality_score']:.1f}%")
for issue in report['issues']:
    print(f"Issue: {issue['type']} - {issue['count']} records")
```

---

## Configuration

### `config.py`

Central configuration for all gas station networks and parsing parameters.

#### Network Configuration

##### `GAS_STATION_NETWORKS`
Main configuration dictionary for all supported networks.

**Structure:**
```python
{
    "network_key": {
        "name": str,              # Display name
        "type": str,              # Parser type
        "base_url": str,          # Primary URL
        "supports_regions": bool, # Regional support flag
        # Network-specific parameters
    }
}
```

**Supported Network Types:**
- `"russiabase"`: HTML parsing from russiabase.ru
- `"russiabase_regional"`: Regional average price parsing
- `"api"`: REST API integration
- `"selenium"`: Browser automation
- `"tatneft_api"`: Tatneft-specific API

**Example Configuration:**
```python
"lukoil": {
    "name": "Лукойл",
    "type": "russiabase",
    "brand_id": 119,
    "base_url": "https://russiabase.ru/prices?brand=119",
    "supports_regions": True
}
```

#### Global Settings

##### `OUTPUT_DIR`
Directory for output data files (default: "data")

##### `LOGS_DIR`  
Directory for log files (default: "logs")

##### `REQUEST_DELAY`
Tuple defining min/max delay between requests (default: (1, 3) seconds)

##### `RETRY_COUNT`
Number of retry attempts for failed requests (default: 3)

##### `TIMEOUT`
HTTP request timeout in seconds (default: 30)

##### `DEFAULT_HEADERS`
Standard HTTP headers for web requests

##### `OUTPUT_SCHEMA`
Standard data schema for all parsers

##### `REGIONS_CONFIG`
Regional parsing configuration:
```python
{
    "default_regions": List[int],      # Popular region IDs
    "enable_region_filtering": bool,
    "enable_multi_region_parsing": bool,
    "max_regions_per_network": int
}
```

---

## Data Structures

### `RegionalPriceResult`

Data class for regional price parsing results.

**Location:** `src/parsers/russiabase_parser.py`

```python
@dataclass
class RegionalPriceResult:
    region_id: int                    # Region identifier
    region_name: str                  # Human-readable region name
    fuel_prices: Dict[str, float]     # Fuel type to price mapping
    url: str                          # Source URL
    timestamp: str                    # ISO timestamp
    status: str                       # 'success' or 'error'
    error_message: str = None         # Error details if applicable
```

**Example:**
```python
result = RegionalPriceResult(
    region_id=77,
    region_name="Москва",
    fuel_prices={
        "АИ-92": 45.50,
        "АИ-95": 48.20,
        "АИ-98": 52.10,
        "ДТ": 49.80
    },
    url="https://russiabase.ru/prices?region=77",
    timestamp="2024-01-15T14:30:00",
    status="success"
)
```

### Standard DataFrame Schema

All parsers normalize data to this schema:

| Column | Type | Description |
|--------|------|-------------|
| `station_id` | str | Unique station identifier |
| `network_name` | str | Gas station network name |
| `station_name` | str | Individual station name |
| `address` | str | Full street address |
| `city` | str | City name |
| `region` | str | Region/state name |
| `region_id` | int | Numeric region identifier |
| `latitude` | float | GPS latitude coordinate |
| `longitude` | float | GPS longitude coordinate |
| `fuel_type` | str | Fuel type (АИ-92, АИ-95, ДТ, etc.) |
| `price` | float | Price per liter in RUB |
| `currency` | str | Currency code (RUB) |
| `last_updated` | str | ISO timestamp of data collection |
| `source` | str | Source URL or identifier |

---

## Examples

### Basic Usage

#### Parse All Networks
```python
from src.orchestrator import GasStationOrchestrator

orchestrator = GasStationOrchestrator()
results = orchestrator.run()

summary = orchestrator.get_summary()
print(f"Total records: {summary['total_records']}")
print(f"Networks parsed: {summary['networks_parsed']}")
```

#### Parse Specific Networks in Parallel
```python
orchestrator = GasStationOrchestrator(
    networks=['lukoil', 'gazprom', 'bashneft'],
    parallel=True,
    max_workers=3
)
results = orchestrator.run()
```

### Regional Price Analysis

#### Get All Russian Regions
```python
from src.parsers.russiabase_parser import RussiaBaseRegionalParser

parser = RussiaBaseRegionalParser()
regions = parser.get_all_regions()

print(f"Total regions: {len(regions)}")
for region_id, name in list(regions.items())[:5]:
    print(f"{region_id}: {name}")
```

#### Parse Popular Regions
```python
popular_regions = [
    {'id': 77, 'name': 'Москва'},
    {'id': 78, 'name': 'Санкт-Петербург'},
    {'id': 50, 'name': 'Московская область'}
]

results = parser.parse_multiple_regions(popular_regions)
for result in results:
    if result.status == 'success':
        print(f"\n{result.region_name}:")
        for fuel, price in result.fuel_prices.items():
            print(f"  {fuel}: {price:.2f} руб/л")
```

### Data Analysis

#### Load and Analyze Data
```python
from src.utils import DataProcessor
import polars as pl

# Load latest data
df = DataProcessor.load_latest_data()

# Clean data
df_clean = DataProcessor.clean_data(df)

# Get statistics
stats = DataProcessor.get_price_statistics(df_clean)
print(f"Total stations: {stats['total_stations']}")
print(f"Average price: {stats['networks'][0]['avg_price']:.2f}")

# Find cheapest stations in Moscow
cheapest = DataProcessor.find_cheapest_stations(
    df_clean, 
    fuel_type="АИ-95", 
    city="Москва", 
    limit=10
)
print(cheapest.select(['network_name', 'station_name', 'price']))
```

#### Export Analysis Reports
```python
# Export comprehensive Excel report
DataProcessor.export_summary_report(df_clean, "analysis_report.xlsx")

# Export CSV reports
DataProcessor.export_summary_csv_report(df_clean, "csv_reports")

# Export both formats
DataProcessor.export_combined_report(df_clean, "complete_analysis")
```

#### Compare Networks
```python
# Compare AI-95 prices between networks
comparison = DataProcessor.compare_networks(df_clean, "АИ-95")
print(comparison.select(['network_name', 'avg_price', 'stations_count'])
              .sort('avg_price'))
```

### Data Quality Validation

```python
from src.utils import DataValidator

# Validate data quality
quality_report = DataValidator.validate_data_quality(df)

print(f"Quality Score: {quality_report['quality_score']:.1f}%")
print(f"Total Issues: {len(quality_report['issues'])}")

for issue in quality_report['issues']:
    print(f"- {issue['type']}: {issue['count']} records ({issue['percentage']:.1f}%)")
```

### Custom Parser Implementation

```python
from src.parsers.base import BaseParser
import requests
from bs4 import BeautifulSoup

class CustomParser(BaseParser):
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch raw data from custom source"""
        response = requests.get(self.config['base_url'])
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.find_all('div', class_='station')
    
    def parse_station_data(self, raw_data) -> List[Dict[str, Any]]:
        """Parse individual station element"""
        station_data = []
        
        station_name = raw_data.find('h3').text.strip()
        address = raw_data.find('p', class_='address').text.strip()
        
        # Parse fuel prices
        fuel_elements = raw_data.find_all('span', class_='fuel-price')
        for fuel_elem in fuel_elements:
            fuel_type = fuel_elem.get('data-fuel-type')
            price = self.clean_price(fuel_elem.text)
            
            if price:
                station_data.append({
                    'station_id': f"{self.network_name}_{station_name}",
                    'station_name': station_name,
                    'address': address,
                    'city': self.extract_city_from_address(address),
                    'fuel_type': fuel_type,
                    'price': price
                })
        
        return station_data

# Usage
config = {
    'name': 'Custom Network',
    'base_url': 'https://example.com/stations'
}
parser = CustomParser('custom_network', config)
results = parser.run()
```

### Error Handling and Logging

```python
import logging
from loguru import logger

# Configure custom logging
logger.add(
    "gas_station_parser.log",
    rotation="10 MB",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
)

try:
    orchestrator = GasStationOrchestrator(
        networks=['lukoil', 'invalid_network'],
        parallel=True
    )
    results = orchestrator.run()
    
    # Check for errors
    summary = orchestrator.get_summary()
    if summary['networks_failed'] > 0:
        logger.warning(f"Failed networks: {summary['errors']}")
        
except Exception as e:
    logger.error(f"Critical error: {e}")
    raise
```

This comprehensive API documentation covers all public interfaces, provides detailed usage examples, and explains the data structures used throughout the gas station price parsing system.