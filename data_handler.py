import pandas as pd
import pandas_ta_classic as ta
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_historical_data_from_csv(file_path: str, chunksize: int = 100000) -> Optional[pd.DataFrame]:
    """
    Load historical OHLCV data from a CSV file in chunks to reduce memory usage.

    Args:
        file_path (str): Path to the CSV file.
        chunksize (int): Number of rows to read at a time.

    Returns:
        pd.DataFrame: DataFrame with columns ["timestamp", "open", "high", "low", "close", "volume"]
        None: If error occurs during data loading or file not found.
    """
    try:
        logger.info(f"Loading historical data from CSV: {file_path} in chunks of {chunksize}")
        
        chunks = []
        for chunk in pd.read_csv(file_path, header=None, names=["timestamp", "open", "high", "low", "close", "volume"], chunksize=chunksize):
            # Convert timestamp to datetime and set as index
            # Convert timestamp to datetime, assuming Unix timestamp in seconds
            # Use errors='coerce' to turn unparseable dates into NaT (Not a Time)
            chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], unit="s", errors="coerce")
            chunk.set_index("timestamp", inplace=True)

            # Ensure numeric data types and handle missing values
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                if col not in chunk.columns:
                    logger.error(f"Missing required column in CSV chunk: {col}")
                    return None
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

            chunk.dropna(subset=numeric_columns, inplace=True)
            chunks.append(chunk)
        
        if not chunks:
            logger.error("No data loaded from CSV chunks.")
            return None

        df = pd.concat(chunks)

        # Sort by timestamp to ensure chronological order
        df.sort_index(inplace=True)

        logger.info(f"Successfully loaded {len(df)} candles from CSV.")
        logger.info(f"Data range: {df.index[0]} to {df.index[-1]}")

        return df

    except FileNotFoundError:
        logger.error(f"CSV file not found at {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading data from CSV: {str(e)}")
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
        df (pd.DataFrame): DataFrame with OHLCV data (must have "open", "high", "low", "close", "volume")

    Returns:
        pd.DataFrame: Original DataFrame with additional indicator columns
        None: If error occurs during indicator calculation.

    Raises:
        Exception: If DataFrame is invalid or indicator calculation fails.
    """
    try:
        # Validate input DataFrame
        if df is None or df.empty:
            logger.error("DataFrame is empty or None")
            return None

        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Check if we have enough data for calculations
        if len(df) < 50:  # Need at least 50 periods for EMA 50
            logger.warning(f"Insufficient data for reliable indicators. Got {len(df)} rows, recommend at least 50")

        # Create a copy to avoid modifying original DataFrame
        df_with_indicators = df.copy()

        logger.info("Calculating technical indicators...")

        # 1. Calculate EMAs (Exponential Moving Average)
        logger.info("Calculating EMA indicators...")
        df_with_indicators["ema_12"] = ta.ema(df_with_indicators["close"], length=12)
        df_with_indicators["ema_26"] = ta.ema(df_with_indicators["close"], length=26)
        df_with_indicators["ema_50"] = ta.ema(df_with_indicators["close"], length=50)

        # 2. Calculate MACD (Moving Average Convergence Divergence)
        logger.info("Calculating MACD indicator...")
        macd_data = ta.macd(df_with_indicators["close"], fast=12, slow=26, signal=9)
        if macd_data is not None:
            df_with_indicators["macd"] = macd_data["MACD_12_26_9"]
            df_with_indicators["macd_signal"] = macd_data["MACDs_12_26_9"]
            df_with_indicators["macd_histogram"] = macd_data["MACDh_12_26_9"]
        else:
            logger.warning("MACD calculation failed")

        # 3. Calculate RSI (Relative Strength Index)
        logger.info("Calculating RSI indicator...")
        df_with_indicators["rsi"] = ta.rsi(df_with_indicators["close"], length=14)

        # 4. Calculate ADX (Average Directional Index)
        logger.info("Calculating ADX indicator...")
        adx_data = ta.adx(
            high=df_with_indicators["high"],
            low=df_with_indicators["low"],
            close=df_with_indicators["close"],
            length=14
        )
        if adx_data is not None:
            df_with_indicators["adx"] = adx_data["ADX_14"]
            df_with_indicators["di_plus"] = adx_data["DMP_14"]  # Directional Movement Plus
            df_with_indicators["di_minus"] = adx_data["DMN_14"]  # Directional Movement Minus
        else:
            logger.warning("ADX calculation failed")

        # 5. Volatility Analysis (e.g., Average True Range - ATR)
        logger.info("Calculating ATR indicator...")
        atr_data = ta.atr(
            high=df_with_indicators["high"],
            low=df_with_indicators["low"],
            close=df_with_indicators["close"],
            length=14
        )
        if atr_data is not None:
            df_with_indicators["atr"] = atr_data
        else:
            logger.warning("ATR calculation failed")

        # 6. Trend Strength (e.g., Aroon Oscillator)
        logger.info("Calculating Aroon Oscillator indicator...")
        aroon_data = ta.aroon(high=df_with_indicators["high"], low=df_with_indicators["low"], length=14)
        if aroon_data is not None:
            df_with_indicators["aroon_down"] = aroon_data["AROOND_14"]
            df_with_indicators["aroon_up"] = aroon_data["AROONU_14"]
            df_with_indicators["aroon_oscillator"] = aroon_data["AROONOSC_14"]
        else:
            logger.warning("Aroon Oscillator calculation failed")

        # Add some additional useful columns for analysis
        df_with_indicators["price_change"] = df_with_indicators["close"].pct_change()
        df_with_indicators["volume_sma_20"] = ta.sma(df_with_indicators["volume"], length=20)
        df_with_indicators["volume_ratio"] = df_with_indicators["volume"] / df_with_indicators["volume_sma_20"]

        # Log indicator summary
        indicator_columns = [
            "ema_12", "ema_26", "ema_50",
            "macd", "macd_signal", "macd_histogram",
            "rsi", "adx", "di_plus", "di_minus",
            "atr", "aroon_down", "aroon_up", "aroon_oscillator"
        ]

        calculated_indicators = [col for col in indicator_columns if col in df_with_indicators.columns]
        logger.info(f"Successfully calculated indicators: {calculated_indicators}")

        # Check for any indicators with all NaN values
        for indicator in calculated_indicators:
            if df_with_indicators[indicator].isna().all():
                logger.warning(f"Indicator \'{indicator}\' contains only NaN values")

        logger.info(f"DataFrame shape after adding indicators: {df_with_indicators.shape}")

        return df_with_indicators

    except ValueError as e:
        logger.error(f"Invalid DataFrame structure: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during indicator calculation: {str(e)}")
        return None


def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the quality of market data and indicators.

    Args:
        df (pd.DataFrame): DataFrame with market data and indicators.

    Returns:
        dict: Dictionary containing data quality metrics and warnings.
    """
    try:
        quality_report = {
            "total_rows": len(df),
            "date_range": {
                "start": str(df.index[0]) if not df.empty else None,
                "end": str(df.index[-1]) if not df.empty else None
            },
            "missing_data": {},
            "warnings": []
        }

        # Check for missing data in each column
        for column in df.columns:
            nan_count = df[column].isna().sum()
            if nan_count > 0:
                quality_report["missing_data"][column] = {
                    "count": int(nan_count),
                    "percentage": round((nan_count / len(df)) * 100, 2)
                }

        # Add warnings for data quality issues
        if len(df) < 100:
            quality_report["warnings"].append(f"Limited data: only {len(df)} rows available")

        if quality_report["missing_data"]:
            quality_report["warnings"].append("Missing data detected in some indicators")

        return quality_report

    except Exception as e:
        logger.error(f"Error during data quality validation: {str(e)}")
        return {"error": str(e)}


# Example usage and testing function
def main():
    """
    Example usage of the data handler functions.
    This function demonstrates how to use the module.
    """
    try:
        # Example: Load Bitcoin data from CSV
        csv_file_path = "/home/ubuntu/in-shadow-trader/data/data/btcusd_1-min_data.csv"

        print(f"Loading data from {csv_file_path}...")
        df = get_historical_data_from_csv(csv_file_path)

        if df is not None:
            print(f"Successfully loaded {len(df)} candles")
            print("\nData sample:")
            print(df.head())

            print("\nCalculating indicators...")
            df_with_indicators = calculate_indicators(df)

            if df_with_indicators is not None:
                print(f"Successfully calculated indicators")
                print("\nData with indicators sample:")
                print(df_with_indicators[["close", "ema_12", "ema_26", "rsi", "macd"]].tail())

                # Validate data quality
                quality_report = validate_data_quality(df_with_indicators)
                print(f"\nData quality report:")
                print(f'Total rows: {quality_report.get("total_rows", 0)}')
                print(f'Missing data columns: {list(quality_report.get("missing_data", {}).keys())}')
                print(f'Warnings: {quality_report.get("warnings", [])}')

            else:
                print("Failed to calculate indicators")
        else:
            print("Failed to load data from CSV")

    except Exception as e:
        print(f"Error in main function: {str(e)}")


if __name__ == "__main__":
    main()

