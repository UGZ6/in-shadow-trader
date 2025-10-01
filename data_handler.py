"""
Data Handler Module for Trading Bot

This module provides functions to fetch historical market data from Binance
and calculate technical indicators for trading analysis.

Required dependencies:
    pip install ccxt pandas pandas-ta

Author: Trading Bot
Created: 2025-10-01
"""

import ccxt
import pandas as pd
import pandas_ta as ta
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_historical_data(symbol: str, timeframe: str, limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Fetch historical OHLCV data from Binance exchange.

    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USDT')
        timeframe (str): Timeframe for data (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        limit (int): Number of candles to fetch (default: 100, max: 1000)

    Returns:
        pd.DataFrame: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        None: If error occurs during data fetching

    Raises:
        Exception: If connection to exchange fails or invalid parameters provided
    """
    try:
        # Initialize Binance exchange (using public endpoints, no API keys needed for OHLCV data)
        exchange = ccxt.binance({
            'sandbox': False,  # Set to True for testnet
            'rateLimit': 1200,
            'enableRateLimit': True,
        })

        # Validate inputs
        if not symbol or not timeframe:
            raise ValueError("Symbol and timeframe must be provided")

        if limit <= 0 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")

        logger.info(f"Fetching {limit} candles for {symbol} on {timeframe} timeframe")

        # Fetch OHLCV data
        # Returns: [[timestamp, open, high, low, close, volume], ...]
        ohlcv_data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

        if not ohlcv_data:
            logger.warning(f"No data received for {symbol}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Ensure numeric data types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_columns] = df[numeric_columns].astype(float)

        # Set timestamp as index for technical analysis
        df.set_index('timestamp', inplace=True)

        # Sort by timestamp to ensure chronological order
        df.sort_index(inplace=True)

        logger.info(f"Successfully fetched {len(df)} candles for {symbol}")
        logger.info(f"Data range: {df.index[0]} to {df.index[-1]}")

        return df

    except ccxt.NetworkError as e:
        logger.error(f"Network error while fetching data for {symbol}: {str(e)}")
        return None
    except ccxt.ExchangeError as e:
        logger.error(f"Exchange error while fetching data for {symbol}: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"Invalid parameters: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching data for {symbol}: {str(e)}")
        return None


def calculate_indicators(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Calculate technical indicators using pandas_ta library.

    This function adds the following technical indicators as new columns:
    - EMA (Exponential Moving Average): 12, 26, 50 periods
    - MACD (Moving Average Convergence Divergence): 12, 26, 9 parameters
    - RSI (Relative Strength Index): 14 periods
    - ADX (Average Directional Index): 14 periods

    Args:
        df (pd.DataFrame): DataFrame with OHLCV data (must have 'open', 'high', 'low', 'close', 'volume')

    Returns:
        pd.DataFrame: Original DataFrame with additional indicator columns
        None: If error occurs during indicator calculation

    Raises:
        Exception: If DataFrame is invalid or indicator calculation fails
    """
    try:
        # Validate input DataFrame
        if df is None or df.empty:
            logger.error("DataFrame is empty or None")
            return None

        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Check if we have enough data for calculations
        if len(df) < 50:  # Need at least 50 periods for EMA 50
            logger.warning(f"Insufficient data for reliable indicators. Got {len(df)} rows, recommend at least 50")

        # Create a copy to avoid modifying original DataFrame
        df_with_indicators = df.copy()

        logger.info("Calculating technical indicators...")

        # 1. Calculate EMAs (Exponential Moving Averages)
        logger.info("Calculating EMA indicators...")
        df_with_indicators['ema_12'] = ta.ema(df_with_indicators['close'], length=12)
        df_with_indicators['ema_26'] = ta.ema(df_with_indicators['close'], length=26)
        df_with_indicators['ema_50'] = ta.ema(df_with_indicators['close'], length=50)

        # 2. Calculate MACD (Moving Average Convergence Divergence)
        logger.info("Calculating MACD indicator...")
        macd_data = ta.macd(df_with_indicators['close'], fast=12, slow=26, signal=9)
        if macd_data is not None:
            df_with_indicators['macd'] = macd_data['MACD_12_26_9']
            df_with_indicators['macd_signal'] = macd_data['MACDs_12_26_9']
            df_with_indicators['macd_histogram'] = macd_data['MACDh_12_26_9']
        else:
            logger.warning("MACD calculation failed")

        # 3. Calculate RSI (Relative Strength Index)
        logger.info("Calculating RSI indicator...")
        df_with_indicators['rsi'] = ta.rsi(df_with_indicators['close'], length=14)

        # 4. Calculate ADX (Average Directional Index)
        logger.info("Calculating ADX indicator...")
        adx_data = ta.adx(
            high=df_with_indicators['high'],
            low=df_with_indicators['low'],
            close=df_with_indicators['close'],
            length=14
        )
        if adx_data is not None:
            df_with_indicators['adx'] = adx_data['ADX_14']
            df_with_indicators['di_plus'] = adx_data['DMP_14']  # Directional Movement Plus
            df_with_indicators['di_minus'] = adx_data['DMN_14']  # Directional Movement Minus
        else:
            logger.warning("ADX calculation failed")

        # Add some additional useful columns for analysis
        df_with_indicators['price_change'] = df_with_indicators['close'].pct_change()
        df_with_indicators['volume_sma_20'] = ta.sma(df_with_indicators['volume'], length=20)
        df_with_indicators['volume_ratio'] = df_with_indicators['volume'] / df_with_indicators['volume_sma_20']

        # Log indicator summary
        indicator_columns = [
            'ema_12', 'ema_26', 'ema_50',
            'macd', 'macd_signal', 'macd_histogram',
            'rsi', 'adx', 'di_plus', 'di_minus'
        ]

        calculated_indicators = [col for col in indicator_columns if col in df_with_indicators.columns]
        logger.info(f"Successfully calculated indicators: {calculated_indicators}")

        # Check for any indicators with all NaN values
        for indicator in calculated_indicators:
            if df_with_indicators[indicator].isna().all():
                logger.warning(f"Indicator '{indicator}' contains only NaN values")

        logger.info(f"DataFrame shape after adding indicators: {df_with_indicators.shape}")

        return df_with_indicators

    except ValueError as e:
        logger.error(f"Invalid DataFrame structure: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during indicator calculation: {str(e)}")
        return None


def get_latest_price(symbol: str) -> Optional[float]:
    """
    Get the latest/current price for a trading pair.

    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC/USDT')

    Returns:
        float: Current price of the symbol
        None: If error occurs during price fetching
    """
    try:
        exchange = ccxt.binance({
            'sandbox': False,
            'rateLimit': 1200,
            'enableRateLimit': True,
        })

        ticker = exchange.fetch_ticker(symbol)
        current_price = float(ticker['last'])

        logger.info(f"Current price for {symbol}: {current_price}")
        return current_price

    except Exception as e:
        logger.error(f"Error fetching current price for {symbol}: {str(e)}")
        return None


def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the quality of market data and indicators.

    Args:
        df (pd.DataFrame): DataFrame with market data and indicators

    Returns:
        dict: Dictionary containing data quality metrics and warnings
    """
    try:
        quality_report = {
            'total_rows': len(df),
            'date_range': {
                'start': str(df.index[0]) if not df.empty else None,
                'end': str(df.index[-1]) if not df.empty else None
            },
            'missing_data': {},
            'warnings': []
        }

        # Check for missing data in each column
        for column in df.columns:
            nan_count = df[column].isna().sum()
            if nan_count > 0:
                quality_report['missing_data'][column] = {
                    'count': int(nan_count),
                    'percentage': round((nan_count / len(df)) * 100, 2)
                }

        # Add warnings for data quality issues
        if len(df) < 100:
            quality_report['warnings'].append(f"Limited data: only {len(df)} rows available")

        if quality_report['missing_data']:
            quality_report['warnings'].append("Missing data detected in some indicators")

        return quality_report

    except Exception as e:
        logger.error(f"Error during data quality validation: {str(e)}")
        return {'error': str(e)}


# Example usage and testing function
def main():
    """
    Example usage of the data handler functions.
    This function demonstrates how to use the module.
    """
    try:
        # Example: Fetch Bitcoin data
        symbol = 'BTC/USDT'
        timeframe = '1h'
        limit = 200

        print(f"Fetching data for {symbol}...")
        df = get_historical_data(symbol, timeframe, limit)

        if df is not None:
            print(f"Successfully fetched {len(df)} candles")
            print("\nData sample:")
            print(df.head())

            print("\nCalculating indicators...")
            df_with_indicators = calculate_indicators(df)

            if df_with_indicators is not None:
                print(f"Successfully calculated indicators")
                print("\nData with indicators sample:")
                print(df_with_indicators[['close', 'ema_12', 'ema_26', 'rsi', 'macd']].tail())

                # Validate data quality
                quality_report = validate_data_quality(df_with_indicators)
                print(f"\nData quality report:")
                print(f"Total rows: {quality_report.get('total_rows', 0)}")
                print(f"Missing data columns: {list(quality_report.get('missing_data', {}).keys())}")
                print(f"Warnings: {quality_report.get('warnings', [])}")

                # Get current price
                current_price = get_latest_price(symbol)
                if current_price:
                    print(f"\nCurrent {symbol} price: ${current_price:,.2f}")

            else:
                print("Failed to calculate indicators")
        else:
            print("Failed to fetch data")

    except Exception as e:
        print(f"Error in main function: {str(e)}")


if __name__ == "__main__":
    main()