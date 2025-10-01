# In-Shadow Trader Bot

## Setup Instructions

### Prerequisites
- Python 3.x installed
- Virtual environment created

### Installation
1. Activate virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Project Structure
- `data_handler.py` - Main data fetching and technical analysis module
- `requirements.txt` - Project dependencies
- `venv/` - Virtual environment directory

### Usage
```python
from data_handler import get_historical_data, calculate_indicators

# Fetch OHLCV data from Binance
df = get_historical_data('BTC/USDT', '1h', 100)

# Calculate technical indicators
df_with_indicators = calculate_indicators(df)
```

### Dependencies
- ccxt: Cryptocurrency exchange connectivity
- pandas: Data manipulation and analysis
- pandas-ta: Technical analysis indicators