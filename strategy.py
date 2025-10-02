
"""
Trading Strategy Module (v2 - Scoring System)

This module implements the core trading strategy logic for the Shadow Trader bot.
It uses a flexible scoring system to evaluate buy conditions, making it more
adaptable to various market conditions instead of a rigid all-or-nothing approach.

The strategy uses:
- EMA (12, 26, 50) for trend direction
- MACD for momentum confirmation
- RSI for overbought/oversold conditions
- ADX for trend strength
- Fibonacci retracements (0.5, 0.618) for entry levels

Author: Trading Bot
Created: 2025-10-01
Modified: 2025-10-02 (Implemented Scoring System)
"""
import pandas_ta_classic as ta
import logging
from typing import Tuple, Optional
# import config # Removed global import of config

# Configure logging (should be done once in main application, not here)
logger = logging.getLogger(__name__)


def find_recent_swing_high_low(df: pd.DataFrame, lookback_period: int) -> Tuple[Optional[float], Optional[float]]:
    """
    Find the recent swing high and swing low points for Fibonacci calculations.
    """
    try:
        if df is None or df.empty:
            logger.debug("DataFrame is empty or None for swing high/low calculation.")
            return None, None

        required_columns = ["high", "low"]
        if not all(col in df.columns for col in required_columns):
            logger.warning(f"Missing required columns for swing analysis: {required_columns}")
            return None, None

        if len(df) < lookback_period:
            actual_lookback = len(df)
        else:
            actual_lookback = lookback_period

        recent_data = df.tail(actual_lookback)
        swing_high = float(recent_data["high"].max())
        swing_low = float(recent_data["low"].min())

        if pd.isna(swing_high) or pd.isna(swing_low):
            logger.warning("Found NaN values in swing high/low calculation.")
            return None, None

        if swing_high <= swing_low:
            logger.warning(f"Invalid swing levels: high ({swing_high}) <= low ({swing_low}).")
            return None, None

        return swing_high, swing_low

    except Exception as e:
        logger.error(f"Unexpected error during swing high/low calculation: {str(e)}")
        return None, None


def check_buy_condition(df: pd.DataFrame, fibo_lookback_period: int, rsi_overbought: int, adx_trend_threshold: int, buy_score_threshold: int) -> bool:
    """
    Check if current market conditions meet the buy entry criteria using a SCORING SYSTEM.

    This function evaluates multiple technical indicators and assigns a score.
    A buy signal is generated if the total score meets or exceeds a defined threshold.

    Scoring:
    - EMA Trend Bullish: +2 points
    - MACD Bullish: +1 point
    - RSI Not Overbought: +1 point
    - ADX Strong Trend: +1 point
    - Fibonacci Support Zone: +2 points (High value entry)

    Args:
        df (pd.DataFrame): DataFrame with OHLCV data and calculated technical indicators
        fibo_lookback_period (int): Lookback period for Fibonacci calculation
        rsi_overbought (int): RSI overbought threshold
        adx_trend_threshold (int): ADX trend threshold
        buy_score_threshold (int): Minimum score for buy signal

    Returns:
        bool: True if the total score meets the threshold, False otherwise
    """
    try:
        if df is None or len(df) < 2:
            return False

        required_indicators = ["ema_12", "ema_26", "ema_50", "macd", "macd_signal", "rsi", "adx", "atr", "aroon_oscillator", "close"]
        if not all(col in df.columns for col in required_indicators):
            logger.warning(f"Missing required indicators for buy analysis. Skipping.")
            return False

        last_row = df.iloc[-1]
        critical_values = [last_row[col] for col in required_indicators]
        if any(pd.isna(value) for value in critical_values):
            return False

        # ================================================================
        # 1. EXTRACT INDICATOR VALUES
        # ================================================================
        current_close = last_row["close"]
        ema_12 = last_row["ema_12"]
        ema_26 = last_row["ema_26"]
        ema_50 = last_row["ema_50"]
        macd = last_row["macd"]
        macd_signal = last_row["macd_signal"]
        rsi = last_row["rsi"]
        adx = last_row["adx"]
        atr = last_row["atr"]
        aroon_oscillator = last_row["aroon_oscillator"]

        # ================================================================
        # 2. EVALUATE INDIVIDUAL CONDITIONS
        # ================================================================
        ema_trend_bullish = (ema_12 > ema_26) and (ema_26 > ema_50)
        macd_bullish = macd > macd_signal
        rsi_ok = rsi < rsi_overbought
        adx_strong = adx > adx_trend_threshold
        low_volatility = atr < df["atr"].mean() # Example: current ATR is below its average
        aroon_up_trending = aroon_oscillator > 0 # Aroon Oscillator above 0 indicates uptrend

        swing_high, swing_low = find_recent_swing_high_low(df, fibo_lookback_period)
        fibo_support = False
        if swing_high is not None and swing_low is not None:
            price_range = swing_high - swing_low
            fib_50_level = swing_high - (price_range * 0.5)
            fib_618_level = swing_high - (price_range * 0.618)
            fibo_support = fib_618_level <= current_close <= fib_50_level

        # ================================================================
        # 3. CALCULATE SCORE
        # ================================================================
        score = 0
        if ema_trend_bullish: score += 2
        if macd_bullish: score += 1
        if rsi_ok: score += 1
        if adx_strong: score += 1
        if fibo_support: score += 2
        if low_volatility: score += 1 # Add score for low volatility
        if aroon_up_trending: score += 1 # Add score for Aroon indicating uptrend

        # ================================================================
        # 4. FINAL DECISION
        # ================================================================
        buy_signal = score >= buy_score_threshold

        # ================================================================
        # 5. LOGGING (Only log if it's a potential signal or for debugging)
        # ================================================================
        if buy_signal or score > 2: # Log only when score is interesting or buy signal occurs
            logger.debug(f"--- Buy Check at Price ${current_close:.2f} ---")
            logger.debug(f"  - Score: {score}/{buy_score_threshold} -> {('BUY' if buy_signal else 'HOLD')}")
            logger.debug(f"  - Conditions: EMA={ema_trend_bullish}, MACD={macd_bullish}, RSI={rsi_ok}, ADX={adx_strong}, Fibo={fibo_support}, Volatility={low_volatility}, Aroon={aroon_up_trending}")

        return buy_signal

    except Exception as e:
        logger.error(f"Unexpected error during buy condition check: {str(e)}")
        return False


def check_sell_condition(df: pd.DataFrame, entry_price: float, stop_loss_percent: float) -> bool:
    """
    Check if current market conditions meet the sell exit criteria.
    """
    try:
        if df is None or df.empty or entry_price <= 0:
            return False

        required_indicators = ["ema_12", "ema_26", "macd", "macd_signal", "atr", "aroon_oscillator", "close"]
        if not all(col in df.columns for col in required_indicators):
            logger.warning("Missing required indicators for sell analysis. Skipping.")
            return False

        last_row = df.iloc[-1]
        critical_values = [last_row[col] for col in required_indicators]
        if any(pd.isna(value) for value in critical_values):
            return False

        current_close = last_row["close"]
        ema_12 = last_row["ema_12"]
        ema_26 = last_row["ema_26"]
        macd = last_row["macd"]
        macd_signal = last_row["macd_signal"]
        atr = last_row["atr"]
        aroon_oscillator = last_row["aroon_oscillator"]

        # Condition 1: Trend Reversal (EMA_12 < EMA_26)
        trend_reversal = ema_12 < ema_26

        # Condition 2: Momentum Loss (MACD < Signal)
        momentum_loss = macd < macd_signal

        # Condition 3: Stop Loss
        stop_loss_price = entry_price * (1 - stop_loss_percent)
        stop_loss_triggered = current_close <= stop_loss_price

        # Condition 4: High Volatility (ATR above its mean, indicating potential reversal or increased risk)
        high_volatility = atr > df["atr"].mean()

        # Condition 5: Aroon Oscillator indicating downtrend
        aroon_down_trending = aroon_oscillator < 0

        sell_signal = any([trend_reversal, momentum_loss, stop_loss_triggered, high_volatility, aroon_down_trending])

        if sell_signal:
            reasons = []
            if trend_reversal: reasons.append("Trend Reversal")
            if momentum_loss: reasons.append("Momentum Loss")
            if stop_loss_triggered: reasons.append(f"Stop Loss at ${stop_loss_price:.2f}")
            if high_volatility: reasons.append("High Volatility")
            if aroon_down_trending: reasons.append("Aroon Downtrend")
            logger.debug(f"--- Sell Signal at Price ${current_close:.2f} ---")
            logger.debug(f"  - Reasons: {", ".join(reasons)}}"))

        return sell_signal

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
            "0.0": swing_high,  # 100% (no retracement)
            "0.236": swing_high - (price_range * 0.236),  # 23.6% retracement
            "0.382": swing_high - (price_range * 0.382),  # 38.2% retracement
            "0.5": swing_high - (price_range * 0.5),      # 50% retracement
            "0.618": swing_high - (price_range * 0.618),  # 61.8% retracement
            "0.786": swing_high - (price_range * 0.786),  # 78.6% retracement
            "1.0": swing_low    # 0% (full retracement)
        }

        logger.debug(f"Calculated Fibonacci levels from {swing_low:.6f} to {swing_high:.6f}")
        for level, price in fibonacci_levels.items():
            logger.debug(f"  {level}: {price:.6f}")

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
            "timestamp": str(df.index[-1]) if not df.empty else None,
            "current_data": {},
            "signals": {},
            "fibonacci_levels": {},
            "position_info": {}
        }

        if df.empty:
            summary["error"] = "No data available"
            return summary

        # Get latest market data
        last_row = df.iloc[-1]

        # Current market data
        summary["current_data"] = {
            "close": float(last_row["close"]) if not pd.isna(last_row["close"]) else None,
            "ema_12": float(last_row["ema_12"]) if not pd.isna(last_row["ema_12"]) else None,
            "ema_26": float(last_row["ema_26"]) if not pd.isna(last_row["ema_26"]) else None,
            "ema_50": float(last_row["ema_50"]) if not pd.isna(last_row["ema_50"]) else None,
            "macd": float(last_row["macd"]) if not pd.isna(last_row["macd"]) else None,
            "macd_signal": float(last_row["macd_signal"]) if not pd.isna(last_row["macd_signal"]) else None,
            "rsi": float(last_row["rsi"]) if not pd.isna(last_row["rsi"]) else None,
            "adx": float(last_row["adx"]) if not pd.isna(last_row["adx"]) else None,
        }

        # Calculate current signals (using dummy values for strategy parameters for summary)
        # This function is primarily for display, not for actual trading decisions in main loop
        summary["signals"] = {
            "buy_signal": check_buy_condition(df, 100, 68, 25, 4),
            "sell_signal": check_sell_condition(df, entry_price, 0.03) if entry_price else False
        }

        # Calculate Fibonacci levels
        swing_high, swing_low = find_recent_swing_high_low(df, 100)
        if swing_high and swing_low:
            summary["fibonacci_levels"] = calculate_fibonacci_levels(swing_high, swing_low)

        # Position information
        if entry_price and summary["current_data"]["close"]:
            current_price = summary["current_data"]["close"]
            pnl_absolute = current_price - entry_price
            pnl_percent = (pnl_absolute / entry_price) * 100

            summary["position_info"] = {
                "entry_price": entry_price,
                "current_price": current_price,
                "pnl_absolute": pnl_absolute,
                "pnl_percent": pnl_percent,
                "stop_loss_price": entry_price * 0.97
            }

        return summary

    except Exception as e:
        logger.error(f"Error generating strategy summary: {str(e)}")
        return {"error": str(e)}


# Example usage and testing function
def main():
    """
    Example usage of the strategy functions.
    This function demonstrates how to use the strategy module with sample data.
    """
    try:
        from data_handler import get_historical_data, calculate_indicators
        import config # Import config for example usage

        # Example: Test strategy with Bitcoin data
        symbol = config.SYMBOL
        timeframe = config.TIMEFRAME
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
        swing_high, swing_low = find_recent_swing_high_low(df_with_indicators, config.FIBO_LOOKBACK_PERIOD)
        if swing_high and swing_low:
            print(f"Swing High: {swing_high:.2f}")
            print(f"Swing Low: {swing_low:.2f}")
            print(f"Range: {swing_high - swing_low:.2f} ({((swing_high - swing_low) / swing_low * 100):.2f}%)")

        # Test buy condition
        print("\nTesting buy condition...")
        buy_signal = check_buy_condition(df_with_indicators, config.FIBO_LOOKBACK_PERIOD, config.RSI_OVERBOUGHT, config.ADX_TREND_THRESHOLD, config.BUY_SCORE_THRESHOLD)
        print(f"Buy Signal: {buy_signal}")

        # Test sell condition (with example entry price)
        current_price = df_with_indicators["close"].iloc[-1]
        example_entry_price = current_price * 0.98  # Simulate entry 2% below current
        print(f"\nTesting sell condition (entry at {example_entry_price:.2f})...")
        sell_signal = check_sell_condition(df_with_indicators, example_entry_price, config.STOP_LOSS_PERCENT)
        print(f"Sell Signal: {sell_signal}")

        # Generate strategy summary
        print("\nGenerating strategy summary...")
        summary = get_strategy_summary(df_with_indicators, example_entry_price)
        if "error" not in summary:
            print("Strategy Summary:")
            print(f'  Current Close: {summary["current_data"]["close"]:.2f}')
            print(f'  Buy Signal: {summary["signals"]["buy_signal"]}')
            print(f'  Sell Signal: {summary["signals"]["sell_signal"]}')
            if summary["position_info"]:
                print(f'  P&L Percent: {summary["position_info"]["pnl_percent"]:.2f}%')
        else:
            print(f'Failed to generate strategy summary: {summary["error"]}')

    except Exception as e:
        print(f"Error in main function: {str(e)}")


if __name__ == "__main__":
    main()

