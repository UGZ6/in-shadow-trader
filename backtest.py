#!/usr/bin/env python3
"""
Backtesting Engine for Trading Bot

This module provides comprehensive backtesting capabilities for the trading strategy.
It simulates trading performance over historical data, calculating key metrics like
total return, win rate, maximum drawdown, Sharpe ratio, and more.

Features:
- Historical data fetching with date range support
- Realistic trade simulation with entry/exit prices
- Comprehensive performance metrics
- Detailed trade logging and analysis
- Risk management calculations

Required dependencies:
    pip install pandas pandas-ta

Author: Trading Bot System
Created: 2025-10-01
"""
import pandas as pd
import pandas_ta_classic as ta
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import time
from data_handler import get_historical_data_from_csv, calculate_indicators as calculate_indicators_data_handler

# Configure logging (should be done once in main application, not here)
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Comprehensive backtesting engine for trading strategies.

    This class handles the entire backtesting process from data fetching
    to performance analysis and reporting.
    """

    def __init__(self, symbol: str, timeframe: str,
                 initial_capital: float, commission: float,
                 fibo_lookback_period: int, rsi_overbought: int, adx_trend_threshold: int, buy_score_threshold: int, stop_loss_percent: float):
        """
        Initialize the backtesting engine.

        Args:
            symbol (str): Trading pair symbol
            timeframe (str): Chart timeframe
            initial_capital (float): Starting capital in USD
            commission (float): Trading commission per trade (0.001 = 0.1%)
            fibo_lookback_period (int): Lookback period for Fibonacci calculation
            rsi_overbought (int): RSI overbought threshold
            adx_trend_threshold (int): ADX trend threshold
            buy_score_threshold (int): Minimum score for buy signal
            stop_loss_percent (float): Stop loss percentage
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_capital = initial_capital
        self.commission = commission

        # Strategy parameters from config
        self.fibo_lookback_period = fibo_lookback_period
        self.rsi_overbought = rsi_overbought
        self.adx_trend_threshold = adx_trend_threshold
        self.buy_score_threshold = buy_score_threshold
        self.stop_loss_percent = stop_loss_percent

        # Trading state
        self.capital = initial_capital
        self.position = 0  # Number of units held
        self.entry_price = 0.0
        self.trades = []  # List of completed trades
        self.portfolio_values = []  # Portfolio value over time

        # Performance tracking
        self.peak_capital = initial_capital
        self.max_drawdown = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

        logger.info(f"Initialized backtest engine for {symbol} on {timeframe}")
        logger.info(f"Initial capital: ${initial_capital:.2f}, Commission: {commission*100:.1f}%")


def _get_timeframe_minutes(timeframe: str) -> int:
    """
    Helper to convert timeframe string to minutes.
    """
    timeframe_map = {
        '1m': 1, '5m': 5, '15m': 15, '30m': 30,
        '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
        '1d': 1440, '3d': 4320, '1w': 10080
    }
    return timeframe_map.get(timeframe, 60)




def _calculate_pnl_and_commission(entry_price: float, exit_price: float, position_size: float, commission_rate: float) -> Tuple[float, float]:
    """
    Helper function to calculate net P&L and total commission for a trade.
    """
    entry_value = position_size * entry_price
    exit_value = position_size * exit_price

    commission_cost_buy = entry_value * commission_rate
    commission_cost_sell = exit_value * commission_rate

    gross_pnl = exit_value - entry_value
    net_pnl = gross_pnl - commission_cost_buy - commission_cost_sell
    total_commission = commission_cost_buy + commission_cost_sell

    return net_pnl, total_commission


def _calculate_sharpe_ratio(portfolio_values: List[Dict[str, Any]], timeframe_minutes: int) -> float:
    """
    Calculate Sharpe Ratio based on portfolio values.
    Adjusts for different timeframes to annualize returns.
    """
    if not portfolio_values or len(portfolio_values) < 2:
        return 0.0

    returns_df = pd.DataFrame(portfolio_values)
    returns_df['timestamp'] = pd.to_datetime(returns_df['timestamp'])
    returns_df.set_index('timestamp', inplace=True)
    returns_df['return'] = returns_df['value'].pct_change()
    returns_df.dropna(inplace=True)

    if returns_df.empty:
        return 0.0

    # Convert timeframe to annualization factor
    # 24 hours * 60 minutes = 1440 minutes in a day
    # 365 days in a year
    annualization_factor = (1440 / timeframe_minutes) * 365

    avg_return = returns_df['return'].mean()
    std_return = returns_df['return'].std()

    if std_return == 0:
        return 0.0 # Avoid division by zero

    # Assuming risk-free rate is 0 for simplicity in backtesting
    sharpe_ratio = (avg_return / std_return) * (annualization_factor ** 0.5)
    return sharpe_ratio


def serialize_results_to_json(results: Dict) -> Dict:
    """
    Converts datetime objects in results to string for JSON serialization.
    """
    results_copy = results.copy()
    if 'trades' in results_copy:
        for trade in results_copy['trades']:
            if 'entry_time' in trade and trade['entry_time']:
                trade['entry_time'] = str(trade['entry_time'])
            if 'exit_time' in trade and trade['exit_time']:
                trade['exit_time'] = str(trade['exit_time'])

    if 'portfolio_values' in results_copy:
        for pv in results_copy['portfolio_values']:
            pv['timestamp'] = str(pv['timestamp'])
    return results_copy


def run_backtest(csv_file_path: str, symbol: str, timeframe: str, start_date: str, end_date: str,
                initial_capital: float = 10000.0, commission: float = 0.001,
                fibo_lookback_period: int = 100, rsi_overbought: int = 68, adx_trend_threshold: int = 25, buy_score_threshold: int = 4, stop_loss_percent: float = 0.03) -> Dict:
    """
    Run comprehensive backtest of the trading strategy.

    Args:
        csv_file_path (str): Path to the CSV file containing historical data.
        symbol (str): Trading pair symbol
        timeframe (str): Chart timeframe
        start_date (str): Start date 'YYYY-MM-DD' or 'X years ago UTC'
        end_date (str): End date 'YYYY-MM-DD' or 'now UTC'
        initial_capital (float): Starting capital
        commission (float): Commission per trade
        fibo_lookback_period (int): Lookback period for Fibonacci calculation
        rsi_overbought (int): RSI overbought threshold
        adx_trend_threshold (int): ADX trend threshold
        buy_score_threshold (int): Minimum score for buy signal
        stop_loss_percent (float): Stop loss percentage

    Returns:
        dict: Comprehensive backtest results
    """
    try:
        logger.info("="*60)
        logger.info("STARTING BACKTEST")
        logger.info("="*60)
        logger.info(f"Symbol: {symbol}")
        logger.info(f"Timeframe: {timeframe}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Initial Capital: ${initial_capital:.2f}")
        logger.info(f"Commission: {commission*100:.1f}%")
        logger.info("="*60)

        # Initialize backtest engine with strategy parameters
        engine = BacktestEngine(symbol, timeframe, initial_capital, commission,
                                fibo_lookback_period, rsi_overbought, adx_trend_threshold, buy_score_threshold, stop_loss_percent)
        logger.info("Loading historical data from CSV in chunks...")

        # Handle 'X years ago UTC' format for start_date
        if "ago UTC" in start_date:
            num, unit = start_date.split(" ")[:2]
            num = int(num)
            if "year" in unit:
                start_dt = datetime.utcnow() - timedelta(days=num*365)
            elif "month" in unit:
                start_dt = datetime.utcnow() - timedelta(days=num*30)
            elif "day" in unit:
                start_dt = datetime.utcnow() - timedelta(days=num)
            else:
                raise ValueError(f"Unsupported time unit in start_date: {unit}")
            start_date_dt = start_dt
        else:
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')

        # Handle 'now UTC' for end_date
        if "now UTC" in end_date:
            end_date_dt = datetime.utcnow()
        else:
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

        # Import strategy functions locally to pass config parameters
        from strategy import check_buy_condition, check_sell_condition, find_recent_swing_high_low

        # Initialize variables for backtesting
        in_position = False
        entry_price = 0.0
        position_size = 0.0
        trades = []
        entry_timestamp = None
        processed_candles_count = 0

        # Placeholder for data to be used by strategy (e.g., for lookback periods)
        # This will store a rolling window of data
        strategy_df = pd.DataFrame()

        for chunk_df in get_historical_data_from_csv(csv_file_path, chunksize=10000):
            if chunk_df is None or chunk_df.empty:
                continue

            # Filter chunk by date range
            chunk_df = chunk_df[(chunk_df.index >= start_date_dt) & (chunk_df.index <= end_date_dt)]

            if chunk_df.empty:
                continue

            # Concatenate with previous data for strategy context
            strategy_df = pd.concat([strategy_df, chunk_df])

            # Ensure strategy_df does not grow indefinitely, keep only what's needed for indicators and strategy
            # A reasonable lookback period for most indicators is around 200-300 candles
            max_lookback_needed = max(fibo_lookback_period, 200) # Assuming 200 is a safe upper bound for other indicators
            if len(strategy_df) > max_lookback_needed * 2: # Keep a buffer
                strategy_df = strategy_df.iloc[-max_lookback_needed * 2:]

            # Calculate indicators for the current strategy_df
            df_with_indicators = calculate_indicators_data_handler(strategy_df.copy()) # Pass a copy to avoid modifying original

            if df_with_indicators is None or df_with_indicators.empty:
                logger.warning("DataFrame is empty after indicator calculation for chunk. Skipping.")
                continue

            # ================================================================
            # STEP 2: SIMULATE TRADING FOR THE CURRENT CHUNK
            # ================================================================
            # Iterate only over the new candles in the current chunk
            # Find the index where the chunk_df starts within df_with_indicators
            # This ensures we only process each candle once and with full indicator context
            start_index_for_chunk = df_with_indicators.index.get_loc(chunk_df.index[0]) if chunk_df.index[0] in df_with_indicators.index else 0

            for i, (timestamp, row) in enumerate(df_with_indicators.iloc[start_index_for_chunk:].iterrows()):
                processed_candles_count += 1
                current_price = row['close']

                # Update portfolio value at each step
                current_portfolio_value = engine.capital + (engine.position * current_price)
                engine.portfolio_values.append({'timestamp': timestamp, 'value': current_portfolio_value})

                # Calculate drawdown
                engine.peak_capital = max(engine.peak_capital, current_portfolio_value)
                drawdown = (engine.peak_capital - current_portfolio_value) / engine.peak_capital
                engine.max_drawdown = max(engine.max_drawdown, drawdown)

                # Ensure enough data for strategy to run (this check is now more robust due to strategy_df management)
                if len(df_with_indicators.loc[:timestamp]) < fibo_lookback_period + 50: # Need enough data for indicators and fibo
                    continue

                # Extract relevant data for strategy (lookback period up to current candle)
                lookback_df = df_with_indicators.loc[:timestamp].copy()

                # Check for buy/sell conditions
                if not in_position:
                    buy_signal, buy_score = check_buy_condition(lookback_df, fibo_lookback_period, rsi_overbought, adx_trend_threshold, buy_score_threshold)
                    if buy_signal:
                        # Execute buy order
                        entry_price = current_price
                        position_size = (engine.capital * 0.99) / entry_price # Use 99% of capital
                        engine.capital -= (position_size * entry_price) * (1 + engine.commission)
                        in_position = True
                        entry_timestamp = timestamp
                        engine.total_trades += 1
                        logger.info(f"BUY: {timestamp} - Price: {entry_price:.2f}, Capital: {engine.capital:.2f}, Position: {position_size:.4f}")
                else:
                    # Check for stop loss
                    if current_price <= entry_price * (1 - stop_loss_percent):
                        # Execute sell order (stop loss)
                        exit_price = current_price
                        pnl, commission_cost = _calculate_pnl_and_commission(entry_price, exit_price, position_size, engine.commission)
                        engine.capital += (position_size * exit_price) - commission_cost
                        trades.append({
                            'entry_time': entry_timestamp,
                            'exit_time': timestamp,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position_size': position_size,
                            'pnl': pnl,
                            'commission': commission_cost,
                            'type': 'STOP_LOSS',
                            'result': 'LOSS'
                        })
                        in_position = False
                        engine.losing_trades += 1
                        logger.info(f"STOP LOSS: {timestamp} - Price: {exit_price:.2f}, P&L: {pnl:.2f}, Capital: {engine.capital:.2f}")
                    else:
                        sell_signal, sell_score = check_sell_condition(lookback_df, fibo_lookback_period, rsi_overbought, adx_trend_threshold, buy_score_threshold)
                        if sell_signal:
                            # Execute sell order
                            exit_price = current_price
                            pnl, commission_cost = _calculate_pnl_and_commission(entry_price, exit_price, position_size, engine.commission)
                            engine.capital += (position_size * exit_price) - commission_cost
                            trades.append({
                                'entry_time': entry_timestamp,
                                'exit_time': timestamp,
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'position_size': position_size,
                                'pnl': pnl,
                                'commission': commission_cost,
                                'type': 'SELL',
                                'result': 'WIN' if pnl > 0 else 'LOSS'
                            })
                            in_position = False
                            if pnl > 0:
                                engine.winning_trades += 1
                            else:
                                engine.losing_trades += 1
                            logger.info(f"SELL: {timestamp} - Price: {exit_price:.2f}, P&L: {pnl:.2f}, Capital: {engine.capital:.2f}")

                # Log progress
                if processed_candles_count % 10000 == 0:
                    logger.info(f"Processed {processed_candles_count} candles...")

        logger.info(f"Finished processing {processed_candles_count} candles.")
        engine.trades.extend(trades)

        # Finalize any open positions
        if in_position:
            exit_price = df_with_indicators['close'].iloc[-1] # Exit at the last available price
            pnl, commission_cost = _calculate_pnl_and_commission(entry_price, exit_price, position_size, engine.commission)
            engine.capital += (position_size * exit_price) - commission_cost
            engine.trades.append({
                'entry_time': entry_timestamp,
                'exit_time': df_with_indicators.index[-1],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position_size': position_size,
                'pnl': pnl,
                'commission': commission_cost,
                'type': 'CLOSE_POSITION',
                'result': 'WIN' if pnl > 0 else 'LOSS'
            })
            if pnl > 0:
                engine.winning_trades += 1
            else:
                engine.losing_trades += 1
            logger.info(f"CLOSED OPEN POSITION: {df_with_indicators.index[-1]} - Price: {exit_price:.2f}, P&L: {pnl:.2f}, Capital: {engine.capital:.2f}")

        # ================================================================
        # STEP 3: ANALYZE RESULTS
        # ================================================================
        final_capital = engine.capital
        total_return = ((final_capital - initial_capital) / initial_capital) * 100
        win_rate = (engine.winning_trades / engine.total_trades) * 100 if engine.total_trades > 0 else 0
        sharpe_ratio = _calculate_sharpe_ratio(engine.portfolio_values, _get_timeframe_minutes(timeframe))

        logger.info("="*60)
        logger.info("BACKTEST RESULTS")
        logger.info("="*60)
        logger.info(f"Final Capital: ${final_capital:.2f}")
        logger.info(f"Total Return: {total_return:.2f}%")
        logger.info(f"Total Trades: {engine.total_trades}")
        logger.info(f"Winning Trades: {engine.winning_trades}")
        logger.info(f"Losing Trades: {engine.losing_trades}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Max Drawdown: {engine.max_drawdown:.2f}%")
        logger.info(f"Sharpe Ratio: {sharpe_ratio:.4f}")
        logger.info("="*60)

        results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_capital": final_capital,
            "total_return_percent": total_return,
            "total_trades": engine.total_trades,
            "winning_trades": engine.winning_trades,
            "losing_trades": engine.losing_trades,
            "win_rate_percent": win_rate,
            "max_drawdown_percent": engine.max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "trades": engine.trades,
            "portfolio_values": engine.portfolio_values
        }

        return serialize_results_to_json(results)

    except Exception as e:
        logger.error(f"An error occurred during backtest: {str(e)}")
        return {"error": str(e)}

            current_price = row['close']

            # Update portfolio value at each step
            current_portfolio_value = engine.capital + (engine.position * current_price)
            engine.portfolio_values.append({'timestamp': timestamp, 'value': current_portfolio_value})

            # Calculate drawdown
            engine.peak_capital = max(engine.peak_capital, current_portfolio_value)
            drawdown = (engine.peak_capital - current_portfolio_value) / engine.peak_capital
            engine.max_drawdown = max(engine.max_drawdown, drawdown)

            # Ensure enough data for strategy to run
            if i < fibo_lookback_period + 50: # Need enough data for indicators and fibo
                continue

            # Extract relevant data for strategy (lookback period)
            lookback_df = df_full.iloc[:i+1].copy() # Pass all data up to current candle

            # Check for buy/sell conditions
            if not in_position:
                buy_signal, buy_score = check_buy_condition(lookback_df, fibo_lookback_period, rsi_overbought, adx_trend_threshold, buy_score_threshold)
                if buy_signal:
                    # Execute buy order
                    entry_price = current_price
                    position_size = (engine.capital * 0.99) / entry_price # Use 99% of capital
                    engine.capital -= (position_size * entry_price) * (1 + engine.commission)
                    in_position = True
                    entry_timestamp = timestamp
                    engine.total_trades += 1
                    logger.info(f"BUY: {timestamp} - Price: {entry_price:.2f}, Capital: {engine.capital:.2f}, Position: {position_size:.4f}")
            else:
                # Check for stop loss
                if current_price <= entry_price * (1 - stop_loss_percent):
                    # Execute sell order (stop loss)
                    exit_price = current_price
                    pnl, commission_cost = _calculate_pnl_and_commission(entry_price, exit_price, position_size, engine.commission)
                    engine.capital += (position_size * exit_price) - commission_cost
                    trades.append({
                        'entry_time': entry_timestamp,
                        'exit_time': timestamp,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position_size': position_size,
                        'pnl': pnl,
                        'commission': commission_cost,
                        'type': 'STOP_LOSS'
                    })
                    if pnl > 0: engine.winning_trades += 1
                    else: engine.losing_trades += 1
                    in_position = False
                    logger.info(f"STOP LOSS: {timestamp} - Price: {exit_price:.2f}, PnL: {pnl:.2f}, Capital: {engine.capital:.2f}")
                else:
                    sell_signal, sell_score = check_sell_condition(lookback_df, fibo_lookback_period, rsi_overbought, adx_trend_threshold, buy_score_threshold) # Re-using buy_score_threshold for simplicity, adjust as needed
                    if sell_signal:
                        # Execute sell order
                        exit_price = current_price
                        pnl, commission_cost = _calculate_pnl_and_commission(entry_price, exit_price, position_size, engine.commission)
                        engine.capital += (position_size * exit_price) - commission_cost
                        trades.append({
                            'entry_time': entry_timestamp,
                            'exit_time': timestamp,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position_size': position_size,
                            'pnl': pnl,
                            'commission': commission_cost,
                            'type': 'SELL'
                        })
                        if pnl > 0: engine.winning_trades += 1
                        else: engine.losing_trades += 1
                        in_position = False
                        logger.info(f"SELL: {timestamp} - Price: {exit_price:.2f}, PnL: {pnl:.2f}, Capital: {engine.capital:.2f}")

            # Log progress
            if i % progress_interval == 0:
                logger.info(f"Progress: {i}/{total_candles} processed. Current Capital: {engine.capital:.2f}")

        # ================================================================
        # STEP 3: FINAL CALCULATIONS AND REPORTING
        # ================================================================
        logger.info("="*60)
        logger.info("BACKTEST COMPLETED")
        logger.info("="*60)

        final_capital = engine.capital + (engine.position * current_price if in_position else 0)
        total_return = ((final_capital - initial_capital) / initial_capital) * 100
        win_rate = (engine.winning_trades / engine.total_trades) * 100 if engine.total_trades > 0 else 0

        # Calculate Sharpe Ratio
        timeframe_minutes = _get_timeframe_minutes(timeframe)
        sharpe_ratio = _calculate_sharpe_ratio(engine.portfolio_values, timeframe_minutes)

        results = {
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'total_return_percent': total_return,
            'total_trades': engine.total_trades,
            'winning_trades': engine.winning_trades,
            'losing_trades': engine.losing_trades,
            'win_rate_percent': win_rate,
            'max_drawdown_percent': engine.max_drawdown * 100,
            'sharpe_ratio': sharpe_ratio,
            'trades': trades,
            'portfolio_values': engine.portfolio_values
        }

        logger.info(f"Final Capital: ${final_capital:.2f}")
        logger.info(f"Total Return: {total_return:.2f}%")
        logger.info(f"Total Trades: {engine.total_trades}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Max Drawdown: {engine.max_drawdown*100:.2f}%")
        logger.info(f"Sharpe Ratio: {sharpe_ratio:.2f}")

        return results

    except Exception as e:
        logger.error(f"Backtest Error: {str(e)}")
        return {'error': str(e)}


if __name__ == "__main__":
    import config
    import json
    import os

    # Ensure the logs directory exists
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure logging for the main execution
    logging.basicConfig(
        level=logging.INFO,
        format='%Y-%m-%d %H:%M:%S - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'backtest.log')),
            logging.StreamHandler()
        ]
    )

    # Load backtest configuration
    # config values are directly accessible from the imported config module

    # Example usage with CSV file
    csv_file = os.path.join(os.path.dirname(__file__), 'data', 'data', 'btcusd_1-min_data.csv')

    backtest_results = run_backtest(
        csv_file_path=csv_file,
        symbol=config.SYMBOL,
        timeframe=config.TIMEFRAME,
        start_date="1 year ago UTC", # config.START_DATE is not defined in config.py
        end_date="now UTC", # config.END_DATE is not defined in config.py
        initial_capital=config.INITIAL_CAPITAL,
        commission=config.COMMISSION,
        fibo_lookback_period=config.FIBO_LOOKBACK_PERIOD,
        rsi_overbought=config.RSI_OVERBOUGHT,
        adx_trend_threshold=config.ADX_TREND_THRESHOLD,
        buy_score_threshold=config.BUY_SCORE_THRESHOLD,
        stop_loss_percent=config.STOP_LOSS_PERCENT
    )

    if 'error' not in backtest_results:
        # Save results to JSON file
        results_file = os.path.join(os.path.dirname(__file__), 'backtest_results.json')
        with open(results_file, 'w') as f:
            json.dump(serialize_results_to_json(backtest_results), f, indent=4)
        logging.info(f"Backtest results saved to {results_file}")
    else:
        logging.error(f"Backtest failed: {backtest_results['error']}")

