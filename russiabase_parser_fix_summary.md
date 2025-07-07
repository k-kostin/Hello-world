# Russian Fuel Price Parser Fix Summary

## Problem Description

The `RussiaBaseRegionalParser` was returning identical fixed values (92.0, 95.0, 98.0, 100.0) for all regions instead of actual fuel prices from russiabase.ru. Despite correctly identifying and parsing the HTML table structure, the parser was extracting fuel type numbers rather than actual price data.

## Root Cause Analysis

### Investigation Process

1. **Initial Symptoms**: Parser returned fixed values:
   - АИ-92: 92.0
   - АИ-95: 95.0  
   - АИ-98: 98.0
   - АИ-100: 100.0

2. **Debug Findings**: Through detailed debugging, we discovered:
   - Parser was correctly finding the main table with class `Table_tableInnerWrapper__AGg3H`
   - Table contained 2 rows in tbody section
   - **Row 0**: Contained fuel type headers (Аи-92, Аи-92+, Аи-95, Аи-95+, Аи-98, Аи-100, ДТ, ДТ+, Газ)
   - **Row 1**: Contained actual prices (66.43, 58, 63.3, 66.12, 85.3, 82.02, 80.37, 73.52, 27.93)

### Core Issue

The parser was incorrectly selecting **Row 0** (header row with fuel type names) instead of **Row 1** (actual price data). The `_extract_price_from_text` method was correctly extracting numbers from fuel type names like "Аи-92" → 92.0, but this was not the intended behavior.

The faulty logic in `_extract_from_russiabase_table` method was:
```python
# Old logic that caused the issue
if self._extract_price_from_text(first_cell_text):
    prices_row = row
    break
```

This condition was satisfied by Row 0 because "Аи-92" was parsed as price 92.0.

## Solution Implementation

### Fix Applied

Modified the row selection logic in `/workspace/src/parsers/russiabase_parser.py` lines 677-720 to properly distinguish between header rows (containing fuel type names) and price rows (containing actual numerical prices).

### Key Changes

1. **Enhanced Row Detection Logic**:
   ```python
   # New logic with proper validation
   extracted_price = self._extract_price_from_text(first_cell_text)
   if extracted_price and not self._normalize_fuel_name(first_cell_text):
       # This looks like a price, not a fuel type name
       is_price_row = True
   ```

2. **Multi-Cell Validation**:
   ```python
   # Count cells that look like prices vs fuel names
   price_like_cells = 0
   fuel_name_cells = 0
   for cell in cells[:6]:
       cell_text = cell.get_text().strip()
       if self._extract_price_from_text(cell_text) and not self._normalize_fuel_name(cell_text):
           price_like_cells += 1
       elif self._normalize_fuel_name(cell_text):
           fuel_name_cells += 1
   
   if price_like_cells >= 3 and fuel_name_cells <= 2:
       is_price_row = True
   ```

3. **Fallback Strategy**:
   ```python
   # If no clear price row found, use last row (prices often in last row)
   if not prices_row and rows:
       prices_row = rows[-1]
   ```

## Results After Fix

### Before Fix
```
АИ-92: 92.0 (fixed value from fuel type name)
АИ-95: 95.0 (fixed value from fuel type name)
АИ-98: 98.0 (fixed value from fuel type name)
АИ-100: 100.0 (fixed value from fuel type name)
```

### After Fix
**Moscow (ID: 77)**:
```
АИ-92: 58.0 (actual price)
АИ-95: 63.3 (actual price)
АИ-98: 85.3 (actual price)
АИ-100: 82.02 (actual price)
ДТ: 73.52 (diesel price now extracted)
Пропан: 27.93 (gas price now extracted)
```

**Saint Petersburg (ID: 78)**:
```
АИ-92: 65.19
АИ-95: 70.04
АИ-98: 81.54
ДТ: 83.12
```

**Moscow Region (ID: 50)**:
```
АИ-92: 56.44
АИ-95: 61.51
АИ-98: 76.77
АИ-100: 81.1
ДТ: 64.87
Пропан: 27.18
```

**Krasnodar Region (ID: 23)**:
```
АИ-92: 57.07
АИ-95: 62.04
АИ-98: 83.06
АИ-100: 86.41
ДТ: 71.4
Пропан: 24.71
```

## Technical Improvements

1. **Robust Row Selection**: Parser now correctly identifies data rows vs header rows
2. **Multiple Fuel Types**: Now extracts diesel (ДТ) and gas (Пропан) prices in addition to gasoline
3. **Duplicate Handling**: Properly handles АИ-92+ vs АИ-92, selecting lower prices
4. **Variable Table Structures**: Works with different regions having 4-10 columns
5. **Debug Logging**: Added extensive debug logging to track row selection process

## Testing Verification

The fix was tested across multiple regions with different table structures and consistently returned realistic, varying fuel prices instead of fixed values. All regions now pass the "realistic prices" validation (prices not equal to 92.0, 95.0, 98.0, 100.0).

## Impact

- **Fixed**: Extraction of actual fuel prices from russiabase.ru
- **Enhanced**: Support for more fuel types (diesel, gas)
- **Improved**: Regional price variation accuracy
- **Resolved**: Fixed value issue affecting all regions
- **Added**: Better error handling and debugging capabilities

The parser now correctly provides real-time regional fuel price data as intended.