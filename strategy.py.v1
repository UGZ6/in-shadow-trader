"""
Trading Strategy Module

This module implements the core trading strategy logic for the Shadow Trader bot.
Contains functions for identifying swing highs/lows, calculating Fibonacci levels,
and determining buy/sell conditions based on technical analysis.

The strategy uses:
- EMA (12, 26, 50) for trend direction
- MACD for momentum confirmation
- RSI for overbought/oversold conditions
- ADX for trend strength
- Fibonacci retracements (0.5, 0.618) for entry levels

Required dependencies:
    pip install pandas

Author: Trading Bot
Created: 2025-10-01
"""

import pandas as pd
import logging
from typing import Tuple, Optional
from data_handler import calculate_indicators

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_recent_swing_high_low(df: pd.DataFrame, lookback_period: int = 100) -> Tuple[Optional[float], Optional[float]]:
    """
    Find the recent swing high and swing low points for Fibonacci calculations.

    This function analyzes the historical price data within a specified lookback period
    to identify the highest and lowest price points, which are used as reference levels
    for calculating Fibonacci retracement levels.

    Args:
        df (pd.DataFrame): DataFrame with OHLCV data containing 'high' and 'low' columns
        lookback_period (int, optional): Number of candles to look back. Defaults to 100.

    Returns:
        Tuple[Optional[float], Optional[float]]: A tuple containing (swing_high, swing_low)
            - swing_high (float): The highest 'high' price in the lookback period
            - swing_low (float): The lowest 'low' price in the lookback period
            - Returns (None, None) if insufficient data or error occurs

    Raises:
        ValueError: If DataFrame is invalid or missing required columns
        Exception: If unexpected error occurs during calculation
    """
    try:
        # Validate input DataFrame
        if df is None or df.empty:
            logger.error("DataFrame is empty or None")
            return None, None

        # Check for required columns
        required_columns = ['high', 'low']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns for swing analysis: {missing_columns}")

        # Check if we have enough data
        if len(df) < lookback_period:
            logger.warning(f"Insufficient data for swing analysis. Got {len(df)} rows, requested {lookback_period}")
            # Use all available data if we have less than requested
            actual_lookback = len(df)
        else:
            actual_lookback = lookback_period

        # Get the most recent data for the lookback period
        recent_data = df.tail(actual_lookback)

        # Find swing high (maximum high price) and swing low (minimum low price)
        swing_high = float(recent_data['high'].max())
        swing_low = float(recent_data['low'].min())

        # Validate that we found valid swing levels
        if pd.isna(swing_high) or pd.isna(swing_low):
            logger.error("Found NaN values in swing high/low calculation")
            return None, None

        # Ensure swing high is actually higher than swing low
        if swing_high <= swing_low:
            logger.error(f"Invalid swing levels: high ({swing_high}) <= low ({swing_low})")
            return None, None

        logger.info(f"Found swing levels over {actual_lookback} periods: High={swing_high:.6f}, Low={swing_low:.6f}")
        logger.info(f"Swing range: {swing_high - swing_low:.6f} ({((swing_high - swing_low) / swing_low * 100):.2f}%)")

        return swing_high, swing_low

    except ValueError as e:
        logger.error(f"Invalid DataFrame for swing analysis: {str(e)}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error during swing high/low calculation: {str(e)}")
        return None, None


def check_buy_condition(df: pd.DataFrame) -> bool:
    """
    Check if current market conditions meet the buy entry criteria.

    This function evaluates multiple technical indicators to determine if it's
    an appropriate time to enter a long position. The strategy requires:

    1. Trend Alignment: EMA_12 > EMA_26 > EMA_50 (bullish trend)
    2. Momentum: MACD line > Signal line (bullish momentum)
    3. Momentum Room: RSI < 68 (not overbought, room to move up)
    4. Trend Strength: ADX > 25 (strong trend present)
    5. Entry Level: Price between Fibonacci 0.5 and 0.618 support levels

    Args:
        df (pd.DataFrame): DataFrame with OHLCV data and calculated technical indicators

    Returns:
        bool: True if all buy conditions are met, False otherwise

    Raises:
        ValueError: If DataFrame is invalid or missing required indicators
        Exception: If unexpected error occurs during condition checking
    """
    try:
        # Validate input DataFrame
        if df is None or df.empty:
            logger.error("DataFrame is empty or None for buy condition check")
            return False

        # Check for required indicator columns
        required_indicators = ['ema_12', 'ema_26', 'ema_50', 'macd', 'macd_signal', 'rsi', 'adx', 'close']
        missing_indicators = [col for col in required_indicators if col not in df.columns]

        if missing_indicators:
            raise ValueError(f"Missing required indicators for buy analysis: {missing_indicators}")

        # Get the latest market data (most recent candle)
        last_row = df.iloc[-1]

        # Extract current values for all indicators
        current_close = last_row['close']
        ema_12 = last_row['ema_12']
        ema_26 = last_row['ema_26']
        ema_50 = last_row['ema_50']
        macd = last_row['macd']
        macd_signal = last_row['macd_signal']
        rsi = last_row['rsi']
        adx = last_row['adx']

        # Check for NaN values in critical indicators
        critical_values = [current_close, ema_12, ema_26, ema_50, macd, macd_signal, rsi, adx]
        if any(pd.isna(value) for value in critical_values):
            logger.warning("Found NaN values in critical indicators, cannot evaluate buy condition")
            return False

        logger.info(f"Evaluating buy conditions for price: {current_close:.6f}")
        logger.info(f"EMA values - 12: {ema_12:.6f}, 26: {ema_26:.6f}, 50: {ema_50:.6f}")
        logger.info(f"MACD: {macd:.6f}, Signal: {macd_signal:.6f}, RSI: {rsi:.2f}, ADX: {adx:.2f}")

        # Condition 1: EMA Trend Alignment (EMA_12 > EMA_26 > EMA_50)
        ema_trend_bullish = (ema_12 > ema_26) and (ema_26 > ema_50)
        logger.info(f"EMA trend bullish: {ema_trend_bullish}")

        # Condition 2: MACD Momentum (MACD line > Signal line)
        macd_bullish = macd > macd_signal
        logger.info(f"MACD bullish: {macd_bullish}")

        # Condition 3: RSI room to move up (RSI < 68)
        rsi_condition = rsi < 68
        logger.info(f"RSI has room to move up (< 68): {rsi_condition}")

        # Condition 4: Strong trend (ADX > 25)
        adx_strong = adx > 25
        logger.info(f"ADX shows strong trend (> 25): {adx_strong}")

        # Condition 5: Price within Fibonacci support levels (0.5 to 0.618)
        swing_high, swing_low = find_recent_swing_high_low(df)

        fibonacci_condition = False
        if swing_high is not None and swing_low is not None:
            # Calculate Fibonacci retracement levels
            price_range = swing_high - swing_low
            fib_50_level = swing_high - (price_range * 0.5)    # 50% retracement
            fib_618_level = swing_high - (price_range * 0.618) # 61.8% retracement

            logger.info(f"Fibonacci levels - 50%: {fib_50_level:.6f}, 61.8%: {fib_618_level:.6f}")

            # Price should be between 61.8% (lower) and 50% (higher) retracement levels
            # This indicates price is in a support zone after a retracement
            fibonacci_condition = fib_618_level <= current_close <= fib_50_level
            logger.info(f"Price in Fibonacci support zone (61.8% to 50%): {fibonacci_condition}")
        else:
            logger.warning("Could not calculate Fibonacci levels, skipping this condition")

        # Combine all conditions
        all_conditions = [
            ema_trend_bullish,
            macd_bullish,
            rsi_condition,
            adx_strong,
            fibonacci_condition
        ]

        buy_signal = all(all_conditions)

        logger.info(f"Buy condition summary:")
        logger.info(f"  EMA Trend Bullish: {ema_trend_bullish}")
        logger.info(f"  MACD Bullish: {macd_bullish}")
        logger.info(f"  RSI Room to Move: {rsi_condition}")
        logger.info(f"  ADX Strong Trend: {adx_strong}")
        logger.info(f"  Fibonacci Support: {fibonacci_condition}")
        logger.info(f"  FINAL BUY SIGNAL: {buy_signal}")

        return buy_signal

    except ValueError as e:
        logger.error(f"Invalid DataFrame for buy condition analysis: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during buy condition check: {str(e)}")
        return False


def check_sell_condition(df: pd.DataFrame, entry_price: float) -> bool:
    """
    Check if current market conditions meet the sell exit criteria.

    This function evaluates sell conditions to determine when to exit a long position.
    The strategy will sell if ANY of the following conditions are met:

    1. Trend Reversal: EMA_12 < EMA_26 (short-term trend turns bearish)
    2. Momentum Loss: MACD line < Signal line (momentum turns bearish)
    3. Stop Loss: Current price <= entry_price * 0.97 (3% stop loss)

    Args:
        df (pd.DataFrame): DataFrame with OHLCV data and calculated technical indicators
        entry_price (float): The price at which the position was entered

    Returns:
        bool: True if any sell condition is met, False otherwise

    Raises:
        ValueError: If DataFrame is invalid, missing indicators, or invalid entry_price
        Exception: If unexpected error occurs during condition checking
    """
    try:
        # Validate inputs
        if df is None or df.empty:
            logger.error("DataFrame is empty or None for sell condition check")
            return False

        if entry_price <= 0:
            raise ValueError(f"Invalid entry price: {entry_price}")

        # Check for required indicator columns
        required_indicators = ['ema_12', 'ema_26', 'macd', 'macd_signal', 'close']
        missing_indicators = [col for col in required_indicators if col not in df.columns]

        if missing_indicators:
            raise ValueError(f"Missing required indicators for sell analysis: {missing_indicators}")

        # Get the latest market data (most recent candle)
        last_row = df.iloc[-1]

        # Extract current values for all indicators
        current_close = last_row['close']
        ema_12 = last_row['ema_12']
        ema_26 = last_row['ema_26']
        macd = last_row['macd']
        macd_signal = last_row['macd_signal']

        # Check for NaN values in critical indicators
        critical_values = [current_close, ema_12, ema_26, macd, macd_signal]
        if any(pd.isna(value) for value in critical_values):
            logger.warning("Found NaN values in critical indicators, cannot evaluate sell condition")
            return False

        logger.info(f"Evaluating sell conditions for current price: {current_close:.6f}")
        logger.info(f"Entry price: {entry_price:.6f}")
        logger.info(f"EMA values - 12: {ema_12:.6f}, 26: {ema_26:.6f}")
        logger.info(f"MACD: {macd:.6f}, Signal: {macd_signal:.6f}")

        # Condition 1: Trend Reversal (EMA_12 < EMA_26)
        trend_reversal = ema_12 < ema_26
        logger.info(f"Trend reversal detected (EMA_12 < EMA_26): {trend_reversal}")

        # Condition 2: Momentum Loss (MACD < Signal)
        momentum_loss = macd < macd_signal
        logger.info(f"Momentum loss detected (MACD < Signal): {momentum_loss}")

        # Condition 3: Stop Loss (3% below entry price)
        stop_loss_price = entry_price * 0.97
        stop_loss_triggered = current_close <= stop_loss_price

        current_pnl_percent = ((current_close - entry_price) / entry_price) * 100
        logger.info(f"Stop loss price: {stop_loss_price:.6f}")
        logger.info(f"Current P&L: {current_pnl_percent:.2f}%")
        logger.info(f"Stop loss triggered: {stop_loss_triggered}")

        # Check if any sell condition is met (OR logic)
        sell_conditions = [trend_reversal, momentum_loss, stop_loss_triggered]
        sell_signal = any(sell_conditions)

        logger.info(f"Sell condition summary:")
        logger.info(f"  Trend Reversal: {trend_reversal}")
        logger.info(f"  Momentum Loss: {momentum_loss}")
        logger.info(f"  Stop Loss Triggered: {stop_loss_triggered}")
        logger.info(f"  FINAL SELL SIGNAL: {sell_signal}")

        # Log the reason for selling if signal is True
        if sell_signal:
            reasons = []
            if trend_reversal:
                reasons.append("Trend Reversal")
            if momentum_loss:
                reasons.append("Momentum Loss")
            if stop_loss_triggered:
                reasons.append("Stop Loss")
            logger.info(f"Sell signal triggered due to: {', '.join(reasons)}")

        return sell_signal

    except ValueError as e:
        logger.error(f"Invalid input for sell condition analysis: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during sell condition check: {str(e)}")
        return False


def calculate_fibonacci_levels(swing_high: float, swing_low: float) -> dict:
    """
    Calculate Fibonacci retracement levels from swing high and low points.

    This helper function calculates commonly used Fibonacci retracement levels
    that can be used for support/resistance analysis and entry/exit points.

    Args:
        swing_high (float): The highest price point in the swing
        swing_low (float): The lowest price point in the swing

    Returns:
        dict: Dictionary containing Fibonacci levels with keys:
            - '0.0': swing_high (100% retracement)
            - '0.236': 23.6% retracement level
            - '0.382': 38.2% retracement level
            - '0.5': 50% retracement level
            - '0.618': 61.8% retracement level
            - '0.786': 78.6% retracement level
            - '1.0': swing_low (0% retracement)

    Raises:
        ValueError: If swing_high <= swing_low or invalid values provided
    """
    try:
        # Validate inputs
        if swing_high <= swing_low:
            raise ValueError(f"Swing high ({swing_high}) must be greater than swing low ({swing_low})")

        if swing_high <= 0 or swing_low <= 0:
            raise ValueError("Swing high and low must be positive values")

        # Calculate price range
        price_range = swing_high - swing_low

        # Calculate Fibonacci retracement levels
        fibonacci_levels = {
            '0.0': swing_high,  # 100% (no retracement)
            '0.236': swing_high - (price_range * 0.236),  # 23.6% retracement
            '0.382': swing_high - (price_range * 0.382),  # 38.2% retracement
            '0.5': swing_high - (price_range * 0.5),      # 50% retracement
            '0.618': swing_high - (price_range * 0.618),  # 61.8% retracement
            '0.786': swing_high - (price_range * 0.786),  # 78.6% retracement
            '1.0': swing_low    # 0% (full retracement)
        }

        logger.info(f"Calculated Fibonacci levels from {swing_low:.6f} to {swing_high:.6f}")
        for level, price in fibonacci_levels.items():
            logger.info(f"  {level}: {price:.6f}")

        return fibonacci_levels

    except ValueError as e:
        logger.error(f"Invalid swing values for Fibonacci calculation: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error calculating Fibonacci levels: {str(e)}")
        raise


def get_strategy_summary(df: pd.DataFrame, entry_price: Optional[float] = None) -> dict:
    """
    Get a comprehensive summary of current strategy conditions and signals.

    This function provides a complete overview of the current market state
    according to the trading strategy, including all technical indicators,
    buy/sell signals, and Fibonacci levels.

    Args:
        df (pd.DataFrame): DataFrame with OHLCV data and calculated indicators
        entry_price (float, optional): Current position entry price for P&L calculation

    Returns:
        dict: Comprehensive strategy summary containing:
            - current_data: Latest OHLCV and indicator values
            - signals: Current buy and sell signals
            - fibonacci_levels: Current Fibonacci retracement levels
            - position_info: P&L and position details if entry_price provided

    Raises:
        Exception: If error occurs during summary generation
    """
    try:
        summary = {
            'timestamp': str(df.index[-1]) if not df.empty else None,
            'current_data': {},
            'signals': {},
            'fibonacci_levels': {},
            'position_info': {}
        }

        if df.empty:
            summary['error'] = "No data available"
            return summary

        # Get latest market data
        last_row = df.iloc[-1]

        # Current market data
        summary['current_data'] = {
            'close': float(last_row['close']) if not pd.isna(last_row['close']) else None,
            'ema_12': float(last_row['ema_12']) if not pd.isna(last_row['ema_12']) else None,
            'ema_26': float(last_row['ema_26']) if not pd.isna(last_row['ema_26']) else None,
            'ema_50': float(last_row['ema_50']) if not pd.isna(last_row['ema_50']) else None,
            'macd': float(last_row['macd']) if not pd.isna(last_row['macd']) else None,
            'macd_signal': float(last_row['macd_signal']) if not pd.isna(last_row['macd_signal']) else None,
            'rsi': float(last_row['rsi']) if not pd.isna(last_row['rsi']) else None,
            'adx': float(last_row['adx']) if not pd.isna(last_row['adx']) else None,
        }

        # Calculate current signals
        summary['signals'] = {
            'buy_signal': check_buy_condition(df),
            'sell_signal': check_sell_condition(df, entry_price) if entry_price else False
        }

        # Calculate Fibonacci levels
        swing_high, swing_low = find_recent_swing_high_low(df)
        if swing_high and swing_low:
            summary['fibonacci_levels'] = calculate_fibonacci_levels(swing_high, swing_low)

        # Position information
        if entry_price and summary['current_data']['close']:
            current_price = summary['current_data']['close']
            pnl_absolute = current_price - entry_price
            pnl_percent = (pnl_absolute / entry_price) * 100

            summary['position_info'] = {
                'entry_price': entry_price,
                'current_price': current_price,
                'pnl_absolute': pnl_absolute,
                'pnl_percent': pnl_percent,
                'stop_loss_price': entry_price * 0.97
            }

        return summary

    except Exception as e:
        logger.error(f"Error generating strategy summary: {str(e)}")
        return {'error': str(e)}


# Example usage and testing function
def main():
    """
    Example usage of the strategy functions.
    This function demonstrates how to use the strategy module with sample data.
    """
    try:
        from data_handler import get_historical_data

        # Example: Test strategy with Bitcoin data
        symbol = 'BTC/USDT'
        timeframe = '1h'
        limit = 200

        print(f"Testing strategy with {symbol} data...")

        # Fetch market data
        df = get_historical_data(symbol, timeframe, limit)
        if df is None:
            print("Failed to fetch market data")
            return

        # Calculate technical indicators
        df_with_indicators = calculate_indicators(df)
        if df_with_indicators is None:
            print("Failed to calculate indicators")
            return

        print(f"Successfully prepared data with {len(df_with_indicators)} candles")

        # Test swing high/low detection
        print("\nTesting swing high/low detection...")
        swing_high, swing_low = find_recent_swing_high_low(df_with_indicators)
        if swing_high and swing_low:
            print(f"Swing High: {swing_high:.2f}")
            print(f"Swing Low: {swing_low:.2f}")
            print(f"Range: {swing_high - swing_low:.2f} ({((swing_high - swing_low) / swing_low * 100):.2f}%)")

        # Test buy condition
        print("\nTesting buy condition...")
        buy_signal = check_buy_condition(df_with_indicators)
        print(f"Buy Signal: {buy_signal}")

        # Test sell condition (with example entry price)
        current_price = df_with_indicators['close'].iloc[-1]
        example_entry_price = current_price * 0.98  # Simulate entry 2% below current
        print(f"\nTesting sell condition (entry at {example_entry_price:.2f})...")
        sell_signal = check_sell_condition(df_with_indicators, example_entry_price)
        print(f"Sell Signal: {sell_signal}")

        # Generate strategy summary
        print("\nGenerating strategy summary...")
        summary = get_strategy_summary(df_with_indicators, example_entry_price)

        print(f"Current Price: {summary['current_data']['close']:.2f}")
        print(f"RSI: {summary['current_data']['rsi']:.2f}")
        print(f"MACD: {summary['current_data']['macd']:.6f}")
        print(f"ADX: {summary['current_data']['adx']:.2f}")
        print(f"Buy Signal: {summary['signals']['buy_signal']}")
        print(f"Sell Signal: {summary['signals']['sell_signal']}")

        if summary['position_info']:
            print(f"P&L: {summary['position_info']['pnl_percent']:.2f}%")

        print("\nStrategy testing completed successfully!")

    except Exception as e:
        print(f"Error in strategy testing: {str(e)}")


if __name__ == "__main__":
    main()