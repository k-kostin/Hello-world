# User Guide - Gas Station Price Parser

Complete user guide for the Russian Gas Station Price Parsing System. This guide covers installation, configuration, and all usage scenarios.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Regional Price Parsing](#regional-price-parsing)
6. [Data Analysis](#data-analysis)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Examples](#examples)

---

## Quick Start

### Prerequisites
- Python 3.8+
- Internet connection
- Google Chrome (for Selenium-based parsers)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd gas-station-parser

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# Parse all gas station networks
python main.py --all

# Parse specific networks
python main.py --networks lukoil gazprom

# Parse regional average prices for all Russia
python regional_parser.py --all-regions

# List available networks
python main.py --list
```

---

## Installation

### System Requirements

- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM (recommended 4GB for parallel processing)
- **Storage**: At least 500MB free space for data files
- **Internet**: Stable connection for web scraping

### Dependencies Installation

#### Method 1: Using pip (Recommended)
```bash
pip install -r requirements.txt
```

#### Method 2: Manual installation
```bash
pip install requests beautifulsoup4 polars selenium webdriver-manager
pip install lxml openpyxl xlsxwriter pandas pyarrow python-dotenv
pip install schedule loguru leafmap geopandas numpy folium matplotlib
```

### Browser Setup (for Selenium)

The system automatically downloads and manages Chrome WebDriver through `webdriver-manager`. No manual driver installation required.

### Verification
```bash
# Test the installation
python main.py --list

# Should display available gas station networks
```

---

## Basic Usage

### Command Line Interface

#### Main Parser (`main.py`)

**Parse all networks:**
```bash
python main.py --all
```

**Parse specific networks:**
```bash
python main.py --networks lukoil bashneft gazprom
```

**Parallel processing:**
```bash
python main.py --networks lukoil bashneft --parallel --workers 3
```

**Verbose logging:**
```bash
python main.py --all --verbose
```

**List available networks:**
```bash
python main.py --list
```

#### Regional Parser (`regional_parser.py`)

**Parse all Russian regions:**
```bash
python regional_parser.py --all-regions
```

**Parse popular regions only:**
```bash
python regional_parser.py --popular-regions
```

**Parse specific regions:**
```bash
python regional_parser.py --regions 77 78 50  # Moscow, SPb, Moscow region
```

**List available regions:**
```bash
python regional_parser.py --list-regions
```

### Available Gas Station Networks

| Network | Code | Type | Coverage |
|---------|------|------|----------|
| **Лукойл** | `lukoil` | russiabase | 84 regions |
| **Башнефть** | `bashneft` | russiabase | 84 regions |
| **Газпром** | `gazprom` | api | Dynamic |
| **Яндекс Карты** | `yandex_maps` | selenium | On-demand |
| **Татнефть** | `tatneft` | api | Russia only |
| **Нефтьмагистраль** | `neftmagistral` | russiabase | 84 regions |
| **Региональные цены** | `regional_prices` | russiabase_regional | ALL 84 regions |

---

## Advanced Features

### Parallel Processing

Run multiple parsers simultaneously to speed up data collection:

```bash
# 2 parallel workers
python main.py --networks lukoil bashneft gazprom --parallel --workers 2

# Maximum parallelization (default: 3 workers)
python main.py --all --parallel
```

**Benefits:**
- 3-5x faster processing
- Efficient resource utilization
- Automatic error handling per network

**Considerations:**
- Higher memory usage
- May trigger rate limiting on some sources
- Use fewer workers for slower internet connections

### Regional Price Analysis

#### Complete Regional Coverage
```bash
# Get average prices for ALL 84 Russian regions
python regional_parser.py --all-regions

# Limit to first 20 regions (for testing)
python regional_parser.py --all-regions --max-regions 20
```

#### Popular Regions
```bash
# Parse major cities and regions
python regional_parser.py --popular-regions
```

Popular regions include:
- Moscow (77)
- Saint Petersburg (78)  
- Moscow Region (50)
- Kursk Region (40)
- Krasnodar (23)
- Sverdlovsk Region (66)
- Sevastopol (96)

#### Custom Region Selection
```bash
# Specific regions by ID
python regional_parser.py --regions 77 78 50 23

# With custom delay between requests
python regional_parser.py --regions 77 78 --delay 2.0
```

### Data Export Formats

The system automatically saves data in multiple formats:

#### Individual Network Files
- `{network}_{timestamp}.xlsx` - Single network data
- Format: Excel with formatted columns

#### Combined Files
- `all_gas_stations_{timestamp}.xlsx` - All networks combined
- `gas_stations_{networks}_{timestamp}.xlsx` - Specific networks

#### Regional Data Files
- `all_regions_{timestamp}.json` - Complete regional data (JSON)
- `all_regions_{timestamp}.xlsx` - Complete regional data (Excel)
- `regions_partial_{count}reg_{timestamp}.json` - Partial regional data

### Orchestrated vs Standalone Modes

#### Orchestrated Mode (Default)
```bash
python regional_parser.py --all-regions --use-orchestrator
```
- Integrates with main parsing system
- Saves to `data/` directory
- Includes history tracking
- Better for production use

#### Standalone Mode
```bash
python regional_parser.py --all-regions
```
- Independent operation
- Saves to current directory
- Faster for testing
- Simpler file structure

---

## Regional Price Parsing

### Understanding Regional Data

Regional parsing extracts **average fuel prices by region** rather than individual gas stations. This provides:

- **Statistical Overview**: Average prices across entire regions
- **Faster Collection**: One request per region vs hundreds per network
- **Complete Coverage**: All 84 Russian federal subjects
- **Trend Analysis**: Perfect for price monitoring and research

### Regional Data Structure

```json
{
  "region_id": 77,
  "region_name": "Москва",
  "fuel_prices": {
    "АИ-92": 45.50,
    "АИ-95": 48.20,
    "АИ-98": 52.10,
    "ДТ": 49.80,
    "Газ": 26.30,
    "Пропан": 28.40
  },
  "timestamp": "2024-01-15T14:30:00",
  "status": "success"
}
```

### Regional Commands Reference

#### List All Regions
```bash
python regional_parser.py --list-regions
```

Output shows:
- Popular regions (marked with *)
- All other regions with IDs
- Total count of available regions

#### Complete Regional Parsing
```bash
# All regions (recommended for production)
python regional_parser.py --all-regions

# With verbose logging
python regional_parser.py --all-regions --verbose

# With custom settings
python regional_parser.py --all-regions --delay 1.5 --max-regions 50
```

#### Quick Regional Tests
```bash
# Major cities only (fast)
python regional_parser.py --popular-regions

# Single region test
python regional_parser.py --regions 77  # Moscow only

# Regional subset
python regional_parser.py --regions 77 78 50 23 66  # Top 5 regions
```

### Regional File Output

After successful regional parsing:

#### JSON Files (Primary)
- `all_regions_YYYYMMDD_HHMMSS.json` - Complete data
- `regions_partial_Nreg_YYYYMMDD_HHMMSS.json` - Partial data

#### Excel Files (Analysis)
- Multiple sheets: prices, statistics, metadata
- Formatted for easy viewing and analysis

#### History Integration
- `data/regional_history/YYYY/MM/DD/` - Historical tracking
- Automatic version management
- Trend analysis support

---

## Data Analysis

### Built-in Analysis Tools

#### Using DataProcessor Class

```python
from src.utils import DataProcessor

# Load latest data
df = DataProcessor.load_latest_data()

# Clean and validate
df_clean = DataProcessor.clean_data(df)

# Get comprehensive statistics
stats = DataProcessor.get_price_statistics(df_clean)
print(f"Total stations: {stats['total_stations']}")
print(f"Networks: {stats['total_networks']}")
```

#### Price Comparison
```python
# Compare AI-95 prices between networks
comparison = DataProcessor.compare_networks(df_clean, "АИ-95")
print(comparison)

# Find cheapest stations in Moscow
cheapest = DataProcessor.find_cheapest_stations(
    df_clean, 
    fuel_type="АИ-95", 
    city="Москва", 
    limit=10
)
```

#### Export Analysis Reports
```python
# Comprehensive Excel report
DataProcessor.export_summary_report(df_clean, "analysis.xlsx")

# CSV reports
DataProcessor.export_summary_csv_report(df_clean, "reports/")

# Both formats
DataProcessor.export_combined_report(df_clean, "complete_analysis")
```

### Data Quality Validation

```python
from src.utils import DataValidator

# Validate data quality
report = DataValidator.validate_data_quality(df)

print(f"Quality Score: {report['quality_score']:.1f}%")
for issue in report['issues']:
    print(f"- {issue['type']}: {issue['count']} records")
```

### Historical Price Trends

```python
# Analyze price trends over time
trends = DataProcessor.analyze_price_trends("data/")
if trends:
    print("Price trends analysis available")
```

---

## Configuration

### Main Configuration (`config.py`)

#### Network Configuration
```python
GAS_STATION_NETWORKS = {
    "custom_network": {
        "name": "Custom Gas Network",
        "type": "api",  # or "russiabase", "selenium"
        "base_url": "https://api.example.com",
        "api_key": "your_api_key",  # if required
        "supports_regions": True
    }
}
```

#### Global Settings
```python
# Output directories
OUTPUT_DIR = "data"
LOGS_DIR = "logs"

# Request settings
REQUEST_DELAY = (1, 3)  # Min/max delay in seconds
RETRY_COUNT = 3
TIMEOUT = 30

# Regional settings
REGIONS_CONFIG = {
    "default_regions": [77, 78, 50, 40, 23, 66, 96],
    "enable_region_filtering": True,
    "max_regions_per_network": 10
}
```

### Environment Variables

Create `.env` file for sensitive configuration:
```bash
# API Keys (if needed)
GAZPROM_API_KEY=your_api_key
TATNEFT_API_KEY=your_api_key

# Custom settings
OUTPUT_DIR=custom_data_folder
DELAY_BETWEEN_REQUESTS=2.0
```

### Selenium Configuration
```python
SELENIUM_CONFIG = {
    "headless": True,  # Run without browser window
    "window_size": (1920, 1080),
    "user_agent": "Mozilla/5.0 (...)"
}
```

---

## Troubleshooting

### Common Issues

#### 1. Installation Problems

**Problem**: `pip install` fails with dependency conflicts
```bash
# Solution: Use virtual environment
python -m venv gas_parser_env
source gas_parser_env/bin/activate  # Linux/Mac
# or
gas_parser_env\Scripts\activate  # Windows

pip install -r requirements.txt
```

**Problem**: Chrome WebDriver issues
```bash
# Solution: Update Chrome and restart
pip install --upgrade webdriver-manager selenium
```

#### 2. Parsing Errors

**Problem**: "No data returned" from network
```bash
# Check network availability
python main.py --networks lukoil --verbose

# Try single region
python regional_parser.py --regions 77 --verbose
```

**Problem**: Rate limiting or blocked requests
```bash
# Increase delays
python main.py --networks lukoil
# Edit config.py: REQUEST_DELAY = (3, 5)

# Use sequential mode instead of parallel
python main.py --networks lukoil bashneft  # No --parallel flag
```

#### 3. Memory Issues

**Problem**: Out of memory during large parsing
```bash
# Reduce parallel workers
python main.py --all --parallel --workers 1

# Parse networks separately
python main.py --networks lukoil
python main.py --networks bashneft
```

#### 4. File Access Issues

**Problem**: Cannot save files
```bash
# Check permissions
chmod 755 data/
mkdir -p data logs

# Check disk space
df -h
```

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
# Detailed logging
python main.py --all --verbose
python regional_parser.py --all-regions --verbose

# Check log files
tail -f logs/gas_stations_parsing_*.log
```

### Network-Specific Issues

#### Gazprom API
- Check API endpoint availability
- Verify JSON response format
- Monitor for API changes

#### RussiaBase parsers
- Website structure may change
- CSS selectors might need updates
- Check for CAPTCHA or blocking

#### Selenium parsers
- Chrome version compatibility
- Page loading timeouts
- Element selector changes

---

## Examples

### Example 1: Complete Data Collection

```bash
#!/bin/bash
# collect_all_data.sh

echo "Starting complete gas station data collection..."

# Parse all individual networks
echo "Phase 1: Individual networks"
python main.py --all --parallel --workers 3

# Parse regional averages
echo "Phase 2: Regional averages"
python regional_parser.py --all-regions

# Generate analysis reports
echo "Phase 3: Analysis"
python -c "
from src.utils import DataProcessor
df = DataProcessor.load_latest_data()
if df:
    df_clean = DataProcessor.clean_data(df)
    DataProcessor.export_combined_report(df_clean, 'daily_analysis')
    print('Analysis complete')
"

echo "Data collection complete!"
```

### Example 2: Quick Price Check

```bash
#!/bin/bash
# quick_check.sh

# Quick check of major networks and regions
python main.py --networks lukoil gazprom --parallel
python regional_parser.py --popular-regions

echo "Quick price check complete. Files saved to current directory."
```

### Example 3: Custom Analysis Script

```python
#!/usr/bin/env python3
# custom_analysis.py

from src.utils import DataProcessor, DataValidator
from src.orchestrator import GasStationOrchestrator
import polars as pl

def main():
    print("Running custom gas station analysis...")
    
    # 1. Collect fresh data
    orchestrator = GasStationOrchestrator(
        networks=['lukoil', 'gazprom', 'bashneft'],
        parallel=True,
        max_workers=2
    )
    results = orchestrator.run()
    
    if not results:
        print("No data collected!")
        return
    
    # 2. Load and clean data
    df = DataProcessor.load_latest_data()
    df_clean = DataProcessor.clean_data(df)
    
    # 3. Data quality check
    quality = DataValidator.validate_data_quality(df_clean)
    print(f"Data quality score: {quality['quality_score']:.1f}%")
    
    # 4. Price analysis
    stats = DataProcessor.get_price_statistics(df_clean)
    print(f"Total stations analyzed: {stats['total_stations']}")
    
    # 5. Find best prices in major cities
    cities = ['Москва', 'Санкт-Петербург', 'Новосибирск']
    for city in cities:
        cheapest = DataProcessor.find_cheapest_stations(
            df_clean, 
            fuel_type="АИ-95", 
            city=city, 
            limit=3
        )
        if len(cheapest) > 0:
            print(f"\nCheapest AI-95 in {city}:")
            for row in cheapest.iter_rows(named=True):
                print(f"  {row['station_name']}: {row['price']:.2f} RUB")
    
    # 6. Export comprehensive report
    DataProcessor.export_combined_report(df_clean, "custom_analysis")
    print("Analysis complete! Reports saved.")

if __name__ == "__main__":
    main()
```

### Example 4: Monitoring Script

```python
#!/usr/bin/env python3
# monitor_prices.py

import schedule
import time
from datetime import datetime
from src.orchestrator import GasStationOrchestrator
from src.parsers.russiabase_parser import RussiaBaseRegionalParser

def daily_collection():
    """Daily data collection job"""
    print(f"Starting daily collection at {datetime.now()}")
    
    # Collect station data
    orchestrator = GasStationOrchestrator(
        networks=['lukoil', 'gazprom'],
        parallel=True
    )
    orchestrator.run()
    
    # Collect regional data
    parser = RussiaBaseRegionalParser("regional_prices", {})
    regions = list(parser.get_all_regions().items())[:10]  # Top 10 regions
    region_list = [{'id': rid, 'name': rname} for rid, rname in regions]
    parser.parse_multiple_regions(region_list)
    
    print("Daily collection complete")

def main():
    print("Starting price monitoring service...")
    
    # Schedule daily collection at 6 AM
    schedule.every().day.at("06:00").do(daily_collection)
    
    # Schedule weekly full collection on Sundays at 2 AM  
    schedule.every().sunday.at("02:00").do(lambda: GasStationOrchestrator().run())
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
```

### Example 5: Regional Price Mapping

```python
#!/usr/bin/env python3
# regional_mapping.py

from src.parsers.russiabase_parser import RussiaBaseRegionalParser
import json

def create_price_map():
    """Create a complete price map of Russia"""
    
    parser = RussiaBaseRegionalParser("regional_prices", {
        'delay': 2.0,  # Slower for politeness
        'max_regions': None
    })
    
    # Get all regions
    all_regions = parser.get_all_regions()
    print(f"Found {len(all_regions)} regions")
    
    # Prepare region list
    regions_list = [
        {'id': region_id, 'name': region_name}
        for region_id, region_name in all_regions.items()
    ]
    
    # Parse all regions
    print("Parsing all regions (this may take a while)...")
    results = parser.parse_multiple_regions(regions_list)
    
    # Create map data
    price_map = {}
    for result in results:
        if result.status == 'success' and result.fuel_prices:
            price_map[result.region_id] = {
                'name': result.region_name,
                'prices': result.fuel_prices,
                'timestamp': result.timestamp
            }
    
    # Save map
    with open('russia_fuel_price_map.json', 'w', encoding='utf-8') as f:
        json.dump(price_map, f, ensure_ascii=False, indent=2)
    
    print(f"Price map saved! {len(price_map)} regions included.")
    
    # Print summary
    if price_map:
        ai95_prices = [data['prices'].get('АИ-95', 0) for data in price_map.values()]
        ai95_prices = [p for p in ai95_prices if p > 0]
        
        if ai95_prices:
            avg_price = sum(ai95_prices) / len(ai95_prices)
            min_price = min(ai95_prices)
            max_price = max(ai95_prices)
            
            print(f"\nAI-95 Price Summary across Russia:")
            print(f"  Average: {avg_price:.2f} RUB/L")
            print(f"  Range: {min_price:.2f} - {max_price:.2f} RUB/L")
            print(f"  Regions with data: {len(ai95_prices)}")

if __name__ == "__main__":
    create_price_map()
```

---

## Support and Contributing

### Getting Help

1. **Check the logs**: Look in `logs/` directory for detailed error messages
2. **Enable verbose mode**: Use `--verbose` flag for detailed output
3. **Check configuration**: Verify `config.py` settings
4. **Test individual components**: Parse single networks or regions first

### Performance Tips

1. **Use parallel processing** for multiple networks
2. **Sequential processing** for single network with many regions
3. **Adjust delays** in `config.py` for rate limiting
4. **Monitor memory usage** during large operations
5. **Use regional parsing** for statistical analysis instead of individual stations

### Best Practices

1. **Regular updates**: Keep dependencies updated
2. **Monitor changes**: Websites may change structure
3. **Respect rate limits**: Don't overwhelm source servers
4. **Validate data**: Always check data quality after parsing
5. **Backup configurations**: Save working configurations

This user guide provides comprehensive coverage of the gas station price parsing system. For API details, see `API_DOCUMENTATION.md`.