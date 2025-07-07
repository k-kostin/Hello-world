# RussiaBase Parser Improvements

## Problem
The russiabase parser was attempting to parse a hardcoded number of pages (e.g., 60 pages for Neftmagistral), which resulted in numerous 404 errors when trying to access non-existent pages. This led to:

- Wasted processing time
- Excessive error logging 
- Poor performance for networks with fewer actual pages than the configured maximum

## Solution
Implemented a dynamic page discovery mechanism with consecutive error tracking:

### Key Changes Made

#### 1. Modified `RussiaBaseParser.fetch_data()` method
- **Before**: Used hardcoded `max_pages` from configuration
- **After**: Dynamic pagination with consecutive error tracking

#### 2. Consecutive Error Detection
- Tracks consecutive HTTP 404 errors and empty pages
- Stops parsing after 3 consecutive errors
- Resets error counter when a successful page is found

#### 3. Configuration Cleanup
- Removed hardcoded `max_pages` values from all russiabase stations:
  - `lukoil`: removed `max_pages: 98`
  - `bashneft`: removed `max_pages: 24` 
  - `neftmagistral`: removed `max_pages: 60`

#### 4. Code Cleanup
- Removed unused `_build_urls()` method
- URLs are now built dynamically in the main loop

## Implementation Details

### New Logic Flow
```python
consecutive_errors = 0
max_consecutive_errors = 3
page = 1

while True:
    url = build_page_url(page)
    
    try:
        data = fetch_page(url)
        if data:
            consecutive_errors = 0  # Reset on success
        else:
            consecutive_errors += 1  # Empty page counts as error
    except HTTPError as e:
        if "404" in str(e):
            consecutive_errors += 1
        # Handle other errors...
    
    if consecutive_errors >= max_consecutive_errors:
        break  # Stop parsing
    
    page += 1
```

### Safety Measures
- Maximum page limit of 1000 to prevent infinite loops
- Proper error logging with context
- Graceful handling of different error types

## Benefits

1. **Efficiency**: No more wasted requests to non-existent pages
2. **Better Logging**: Clear indication when parsing stops and why
3. **Scalability**: Works for any number of actual pages without configuration changes
4. **Reliability**: Automatic adaptation to different network sizes

## Affected Networks
All networks using `type: "russiabase"`:
- Лукойл (Lukoil)
- Башнефть (Bashneft) 
- Нефтьмагистраль (Neftmagistral)

## Example Output
```
2025-07-07 09:52:43 | INFO | Обработка страницы 5: https://russiabase.ru/prices?brand=402&page=5
2025-07-07 09:52:44 | WARNING | Страница 6 не найдена (404), consecutive_errors: 1
2025-07-07 09:52:45 | WARNING | Страница 7 не найдена (404), consecutive_errors: 2  
2025-07-07 09:52:46 | WARNING | Страница 8 не найдена (404), consecutive_errors: 3
2025-07-07 09:52:46 | INFO | Остановка парсинга: 3 consecutive ошибок подряд. Всего обработано страниц: 8
2025-07-07 09:52:46 | INFO | Парсинг завершен. Обработано страниц: 7, получено записей: 150
```

This improvement significantly reduces the noise in logs and improves parsing efficiency for all russiabase.ru networks.