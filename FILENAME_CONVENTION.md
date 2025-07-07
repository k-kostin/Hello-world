# Gas Station Data File Naming Convention

## Overview
The system now uses a more descriptive naming convention for combined gas station data files to clearly indicate the scope of data included.

## Naming Rules

### All Networks Requested
When **all available networks** are parsed (no specific networks specified):
```
all_gas_stations_YYYYMMDD_HHMMSS.xlsx
```
**Example:** `all_gas_stations_20250707_100055.xlsx`

This indicates the file contains data from **all 6 configured gas station networks**:
- Lukoil (Лукойл)
- Bashneft (Башнефть) 
- Gazprom (Газпром)
- Yandex Maps
- Tatneft (Татнефть)
- Neftmagistral (Нефтьмагистраль)

### Specific Networks Requested
When **only certain networks** are specified for parsing:

#### Few Networks (≤3):
```
gas_stations_network1_network2_YYYYMMDD_HHMMSS.xlsx
```
**Example:** `gas_stations_lukoil_gazprom_20250707_100055.xlsx`

#### Many Networks (>3):
```
gas_stations_YYYYMMDD_HHMMSS.xlsx
```
**Example:** `gas_stations_20250707_100055.xlsx`

## Benefits

✅ **Clear Scope Indication**: Filename immediately shows if all networks or subset was parsed  
✅ **Avoid Confusion**: No more "all_gas_stations" files that only contain partial data  
✅ **Network Identification**: For small subsets, specific networks are named in filename  
✅ **Backward Compatibility**: Loading functions support both old and new formats  

## Implementation Details

The naming logic is implemented in:
- `src/orchestrator.py` - Filename generation in `_save_combined_data()`
- `src/utils.py` - File loading functions updated for compatibility

## Migration
- Old files with `all_gas_stations_*` prefix continue to work
- New files use the improved naming convention
- Loading functions automatically detect and handle both formats