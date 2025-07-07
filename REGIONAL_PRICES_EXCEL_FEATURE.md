# Regional Prices Excel Export Feature

## Overview

The gas station parser now includes **regional prices in Excel output**! When you generate Excel reports, they will automatically include regional pricing data in addition to the regular gas station network data.

## What's New

### Enhanced Excel Reports

The `export_summary_report()` function now generates Excel files with **additional sheets** for regional data:

1. **Общая статистика** - General statistics
2. **Статистика по топливу** - Fuel statistics
3. **Статистика по сетям** - Network statistics  
4. **Дорогие города** - Most expensive cities
5. **Сравнение АИ-95** - AI-95 network comparison
6. **Дешевые АИ-95** - Cheapest AI-95 stations
7. **🆕 Региональные цены** - Regional prices by fuel type
8. **🆕 Статистика по регионам** - Regional statistics
9. **🆕 Регионы vs Сети** - Regional vs Network price comparison

### New Features

#### 1. Automatic Regional Data Loading
- Automatically finds and loads the latest `regional_prices_*.json` files
- Converts JSON data to structured DataFrame format
- Includes all major Russian regions (Moscow, St. Petersburg, etc.)

#### 2. Regional Price Analysis
- Average, min, max prices by region
- Number of fuel types available per region
- Regional price rankings

#### 3. Regional vs Network Comparison
- Side-by-side comparison of regional averages vs network prices
- Price differences and percentage variations
- Identifies where networks are cheaper/more expensive than regional averages

## How to Use

### Method 1: Enhanced Example Usage

Use the existing example with regional data included:

```python
from src.utils import DataProcessor

# Load your gas station data
df = DataProcessor.load_latest_data()
df_clean = DataProcessor.clean_data(df)

# Generate enhanced report with regional prices
DataProcessor.export_summary_report(
    df_clean, 
    "comprehensive_price_report.xlsx",
    include_regional=True  # This is the new parameter
)
```

### Method 2: Using the Main Parser

When running the main parser, regional data will be automatically included:

```bash
# Parse regional data first
python3 main.py --networks regional_prices

# Then run example with regional export
python3 example_usage.py
```

### Method 3: Test Script

Run the test script to see the functionality:

```bash
python3 test_regional_excel.py
```

## Data Sources

### Regional Data Format
The system looks for JSON files matching `regional_prices_*.json` with this structure:

```json
[
  {
    "region_id": 77,
    "region_name": "Москва",
    "fuel_prices": {
      "АИ-92": 56.20,
      "АИ-95": 59.80,
      "АИ-98": 67.40,
      "ДТ": 58.90,
      "Пропан": 32.50
    },
    "timestamp": "2025-07-07T14:07:13.771983",
    "status": "success"
  }
]
```

### Supported Regions
- Москва (Region ID: 77)
- Санкт-Петербург (Region ID: 78)  
- Московская область (Region ID: 50)
- Краснодарский край (Region ID: 23)
- Свердловская область (Region ID: 66)
- And many more...

## Excel Sheet Descriptions

### Региональные цены (Regional Prices)
| Column | Description |
|--------|-------------|
| region_id | Numeric region identifier |
| region_name | Human-readable region name |
| fuel_type | Type of fuel (АИ-92, АИ-95, ДТ, etc.) |
| price | Price per liter in rubles |
| timestamp | When data was collected |
| source | Always "regional_parser" |

### Статистика по регионам (Regional Statistics)
| Column | Description |
|--------|-------------|
| region_name | Region name |
| fuel_types_count | Number of fuel types available |
| avg_price | Average price across all fuels |
| min_price | Lowest price in region |
| max_price | Highest price in region |
| records_count | Total price records |

### Регионы vs Сети (Regional vs Network Comparison)
| Column | Description |
|--------|-------------|
| fuel_type | Type of fuel |
| network_avg_price | Average price from gas station networks |
| network_records | Number of network records |
| regional_avg_price | Average regional price |
| regional_records | Number of regional records |
| price_difference | Absolute difference (network - regional) |
| percentage_difference | Percentage difference |

## Technical Implementation

### New Methods Added

1. **`DataProcessor.load_regional_data()`**
   - Searches for regional JSON files
   - Converts to Polars DataFrame
   - Handles missing or invalid data gracefully

2. **`DataProcessor.get_regional_statistics()`**
   - Calculates regional price statistics
   - Groups by region and fuel type
   - Returns ranking by average price

3. **`DataProcessor.compare_regional_vs_network_prices()`**
   - Joins regional and network data
   - Calculates price differences
   - Identifies pricing gaps

### Error Handling
- Gracefully handles missing regional data
- Continues with normal report if regional data unavailable
- Logs all operations for debugging

## Benefits

1. **Comprehensive Price Analysis**: Compare network prices against regional averages
2. **Market Intelligence**: Identify regions with higher/lower fuel costs
3. **Pricing Strategy**: Understand competitive landscape by region
4. **Data Integration**: Single Excel file with all pricing information
5. **Automatic Updates**: Always uses latest available regional data

## Example Output

The generated Excel file (`test_regional_report_*.xlsx`) contains:
- ✅ 30 regional price records across 6 regions
- ✅ 5 fuel types (АИ-92, АИ-95, АИ-98, ДТ, Пропан)
- ✅ Regional statistics and comparisons
- ✅ Network vs regional price analysis

## Future Enhancements

Potential improvements for future versions:
- Historical regional price trends
- Geographic price mapping
- Seasonal price variations
- Real-time regional data updates
- Interactive price dashboards

---

## Quick Start

1. Run the test script to see the feature in action:
   ```bash
   python3 test_regional_excel.py
   ```

2. Check the generated Excel file with regional prices included!

3. Use in your own scripts:
   ```python
   DataProcessor.export_summary_report(your_data, include_regional=True)
   ```

**Result**: Excel reports now automatically include regional pricing data! 🎉