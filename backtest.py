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
    pip install ccxt pandas pandas-ta

Author: Trading Bot System
Created: 2025-10-01
"""

import ccxt
import pandas as pd
import pandas_ta as ta
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Comprehensive backtesting engine for trading strategies.

    This class handles the entire backtesting process from data fetching
    to performance analysis and reporting.
    """

    def __init__(self, symbol: str = 'BTC/USDT', timeframe: str = '1h',
                 initial_capital: float = 10000.0, commission: float = 0.001):
        """
        Initialize the backtesting engine.

        Args:
            symbol (str): Trading pair symbol
            timeframe (str): Chart timeframe
            initial_capital (float): Starting capital in USD
            commission (float): Trading commission per trade (0.001 = 0.1%)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_capital = initial_capital
        self.commission = commission

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


def get_historical_data_extended(symbol: str, timeframe: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    Fetch extended historical OHLCV data for backtesting.

    This function fetches historical data in chunks to cover the entire date range,
    as ccxt has limitations on the amount of data that can be fetched in a single request.

    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
        timeframe (str): Timeframe (e.g., '1h', '4h', '1d')
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        pd.DataFrame: DataFrame with OHLCV data for the entire period
        None: If error occurs during data fetching
    """
    try:
        # Initialize exchange
        exchange = ccxt.binance({
            'sandbox': False,
            'rateLimit': 1200,
            'enableRateLimit': True,
        })

        # Convert dates to timestamps
        start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
        end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)

        # Determine chunk size based on timeframe
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
            '1d': 1440, '3d': 4320, '1w': 10080
        }

        chunk_minutes = timeframe_minutes.get(timeframe, 60)
        chunk_ms = chunk_minutes * 60 * 1000
        max_candles = 1000  # ccxt limit

        # Calculate number of chunks needed
        total_ms = end_ts - start_ts
        chunks_needed = int(total_ms / (chunk_ms * max_candles)) + 1

        logger.info(f"Fetching data from {start_date} to {end_date} ({chunks_needed} chunks)")

        all_data = []

        for i in range(chunks_needed):
            chunk_start = start_ts + (i * chunk_ms * max_candles)

            if chunk_start >= end_ts:
                break

            try:
                # Fetch chunk of data
                ohlcv_data = exchange.fetch_ohlcv(symbol, timeframe, since=chunk_start, limit=max_candles)

                if ohlcv_data:
                    all_data.extend(ohlcv_data)
                    logger.info(f"Fetched chunk {i+1}/{chunks_needed}: {len(ohlcv_data)} candles")

                    # Small delay to respect rate limits
                    time.sleep(0.1)

                # Stop if we have data beyond end date
                if ohlcv_data and ohlcv_data[-1][0] >= end_ts:
                    break

            except Exception as chunk_error:
                logger.warning(f"Error fetching chunk {i+1}: {str(chunk_error)}")
                continue

        if not all_data:
            logger.error("No data fetched")
            return None

        # Convert to DataFrame and remove duplicates
        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.drop_duplicates(subset='timestamp').sort_values('timestamp')

        # Filter to date range
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

        # Ensure numeric types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_columns] = df[numeric_columns].astype(float)

        # Set timestamp as index
        df.set_index('timestamp', inplace=True)

        logger.info(f"Successfully fetched {len(df)} candles from {df.index[0]} to {df.index[-1]}")
        return df

    except Exception as e:
        logger.error(f"Error fetching extended historical data: {str(e)}")
        return None


def run_backtest(symbol: str, timeframe: str, start_date: str, end_date: str,
                initial_capital: float = 10000.0, commission: float = 0.001) -> Dict:
    """
    Run comprehensive backtest of the trading strategy.

    Args:
        symbol (str): Trading pair symbol
        timeframe (str): Chart timeframe
        start_date (str): Start date 'YYYY-MM-DD'
        end_date (str): End date 'YYYY-MM-DD'
        initial_capital (float): Starting capital
        commission (float): Commission per trade

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

        # Initialize backtest engine
        engine = BacktestEngine(symbol, timeframe, initial_capital, commission)

        # ================================================================
        # STEP 1: FETCH AND PREPARE ALL DATA AT ONCE (OPTIMIZATION)
        # ================================================================
        logger.info("Fetching historical data...")
        df_full = get_historical_data_extended(symbol, timeframe, start_date, end_date)

        if df_full is None or df_full.empty:
            return {'error': 'Failed to fetch historical data'}

        logger.info(f"Fetched {len(df_full)} candles. Calculating all indicators now...")

        # *** การปรับปรุงประสิทธิภาพอยู่ตรงนี้ ***
        # คำนวณ Indicator ทั้งหมดสำหรับข้อมูลทั้งชุด เพียงครั้งเดียว!
        df_full = calculate_indicators(df_full)

        if df_full is None:
            return {'error': 'Failed to calculate indicators for the dataset'}

        logger.info("All indicators calculated. Starting backtest simulation...")

        # Import strategy functions
        from strategy import check_buy_condition, check_sell_condition

        # Initialize variables for backtesting
        in_position = False
        entry_price = 0.0
        position_size = 0.0
        trades = []
        entry_timestamp = None # เพิ่มตัวแปรสำหรับเก็บเวลาที่เข้าซื้อ

        # Progress tracking
        total_candles = len(df_full)
        progress_interval = max(1, total_candles // 20)

        # ================================================================
        # STEP 2: SIMULATE TRADING (LOOP AND READ)
        # ================================================================
        for i in range(1, len(df_full)): # เริ่มที่ 1 เพื่อให้มีข้อมูลก่อนหน้า

            # *** การปรับปรุงประสิทธิภาพอยู่ตรงนี้ ***
            # สร้าง DataFrame แค่ส่วนที่ strategy ต้องการ (เช่น 100-200 แท่งล่าสุด)
            # ไม่ใช่ทั้งหมดตั้งแต่ต้น
            lookback = config.FIBO_LOOKBACK_PERIOD + 50 # ให้มีข้อมูลเผื่อๆ
            start_index = max(0, i - lookback)
            df_current = df_full.iloc[start_index:i+1] # ส่งข้อมูลเฉพาะส่วนล่าสุดไปให้ strategy

            # ดึงข้อมูลจากแถวปัจจุบัน (ไม่ต้องคำนวณใหม่)
            timestamp = df_full.index[i]
            row = df_full.iloc[i]
            current_price = row['close']

            # Update portfolio value
            if in_position:
                current_value = position_size * current_price
                total_value = current_value + (engine.capital - (position_size * entry_price))
            else:
                total_value = engine.capital

            engine.portfolio_values.append({
                'timestamp': timestamp,
                'value': total_value,
                'price': current_price
            })

            # Update max drawdown
            if total_value > engine.peak_capital:
                engine.peak_capital = total_value
            else:
                drawdown = (engine.peak_capital - total_value) / engine.peak_capital
                engine.max_drawdown = max(engine.max_drawdown, drawdown)

            # Check trading signals
            if not in_position:
                if check_buy_condition(df_current): # ส่ง df_current ที่มี Indicator ครบแล้วไป
                    position_size = engine.capital / current_price
                    entry_price = current_price
                    in_position = True
                    entry_timestamp = timestamp # บันทึกเวลาเข้า

                    logger.info(f"BUY at {timestamp}: {position_size:.6f} units @ ${current_price:.2f}")

            else:
                if check_sell_condition(df_current, entry_price):
                    # Calculate exit value
                    exit_value = position_size * current_price

                    # Calculate P&L
                    entry_value = position_size * entry_price
                    gross_pnl = exit_value - entry_value

                    # คำนวณค่าคอมตอนขาย
                    commission_cost_sell = exit_value * commission

                    # คำนวณค่าคอมตอนซื้อ (ย้ายมาคำนวณที่นี่เพื่อให้ถูกต้อง)
                    commission_cost_buy = entry_value * commission

                    # P&L สุทธิ
                    net_pnl = gross_pnl - commission_cost_buy - commission_cost_sell

                    # อัปเดตเงินทุน
                    engine.capital += net_pnl

                    # Record trade
                    trade = {
                        'entry_time': entry_timestamp, # ใช้เวลาที่บันทึกไว้
                        'exit_time': timestamp,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position_size': position_size,
                        'pnl_percent': (net_pnl / entry_value) * 100,
                        'net_pnl': net_pnl,
                        'commission': commission_cost_buy + commission_cost_sell,
                        'winner': net_pnl > 0
                    }
                    trades.append(trade)

                    # Update statistics
                    engine.total_trades += 1
                    if net_pnl > 0:
                        engine.winning_trades += 1
                    else:
                        engine.losing_trades += 1

                    logger.info(f"SELL at {timestamp}: ${exit_value:.2f} (P&L: ${net_pnl:.2f}, {trade['pnl_percent']:.2f}%)")

                    # Reset position
                    in_position = False
                    entry_price = 0.0
                    position_size = 0.0
                    entry_timestamp = None

            # Progress reporting
            if (i + 1) % progress_interval == 0:
                progress = (i + 1) / total_candles * 100
                logger.info(f"Backtest progress: {progress:.1f}% ({i+1}/{total_candles})")

        # Calculate final results
        final_value = engine.capital
        total_return = (final_value - initial_capital) / initial_capital * 100
        win_rate = (engine.winning_trades / engine.total_trades * 100) if engine.total_trades > 0 else 0

        # Calculate additional metrics
        if trades:
            total_win = sum(t['net_pnl'] for t in trades if t['winner'])
            total_loss = abs(sum(t['net_pnl'] for t in trades if not t['winner']))
            avg_win = total_win / engine.winning_trades if engine.winning_trades > 0 else 0
            avg_loss = total_loss / engine.losing_trades if engine.losing_trades > 0 else 0
            profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
        else:
            avg_win = avg_loss = profit_factor = 0

        # Calculate Sharpe ratio (simplified, assuming daily returns)
        if engine.portfolio_values:
            returns = pd.DataFrame(engine.portfolio_values)
            returns['daily_return'] = returns['value'].pct_change()
            avg_daily_return = returns['daily_return'].mean()
            std_daily_return = returns['daily_return'].std()
            sharpe_ratio = (avg_daily_return / std_daily_return * (365 ** 0.5)) if std_daily_return > 0 else 0
        else:
            sharpe_ratio = 0

        results = {
            'summary': {
                'symbol': symbol,
                'timeframe': timeframe,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'final_capital': final_value,
                'total_return_percent': total_return,
                'total_return_absolute': final_value - initial_capital,
                'max_drawdown_percent': engine.max_drawdown * 100,
                'total_trades': engine.total_trades,
                'winning_trades': engine.winning_trades,
                'losing_trades': engine.losing_trades,
                'win_rate_percent': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'sharpe_ratio': sharpe_ratio,
                'commission_rate': commission * 100
            },
            'trades': trades,
            'portfolio_values': engine.portfolio_values,
            'data_points': len(df_full)
        }

        logger.info("="*60)
        logger.info("BACKTEST COMPLETED")
        logger.info("="*60)
        logger.info(f"Final Capital: ${final_value:.2f}")
        logger.info(f"Total Return: {total_return:.2f}%")
        logger.info(f"Max Drawdown: {engine.max_drawdown*100:.2f}%")
        logger.info(f"Total Trades: {engine.total_trades}")
        logger.info(f"Win Rate: {win_rate:.1f}%")
        logger.info(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        logger.info("="*60)

        return results

    except Exception as e:
        logger.error(f"Error during backtest: {str(e)}")
        return {'error': str(e)}


def calculate_indicators(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Calculate technical indicators for backtesting.

    This is a simplified version for backtesting - uses the same logic
    as data_handler.py but optimized for sequential processing.
    """
    try:
        if df is None or df.empty:
            return None

        df_indicators = df.copy()

        # Calculate EMAs
        df_indicators['ema_12'] = ta.ema(df_indicators['close'], length=12)
        df_indicators['ema_26'] = ta.ema(df_indicators['close'], length=26)
        df_indicators['ema_50'] = ta.ema(df_indicators['close'], length=50)

        # Calculate MACD
        macd_data = ta.macd(df_indicators['close'], fast=12, slow=26, signal=9)
        if macd_data is not None:
            df_indicators['macd'] = macd_data['MACD_12_26_9']
            df_indicators['macd_signal'] = macd_data['MACDs_12_26_9']
            df_indicators['macd_histogram'] = macd_data['MACDh_12_26_9']

        # Calculate RSI
        df_indicators['rsi'] = ta.rsi(df_indicators['close'], length=14)

        # Calculate ADX
        adx_data = ta.adx(df_indicators['high'], df_indicators['low'], df_indicators['close'], length=14)
        if adx_data is not None:
            df_indicators['adx'] = adx_data['ADX_14']
            df_indicators['di_plus'] = adx_data['DMP_14']
            df_indicators['di_minus'] = adx_data['DMN_14']

        return df_indicators

    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        return None


def print_backtest_results(results: Dict):
    """
    Print formatted backtest results.

    Args:
        results (dict): Backtest results from run_backtest()
    """
    if 'error' in results:
        print(f"❌ Backtest failed: {results['error']}")
        return

    summary = results['summary']

    print("\n" + "="*80)
    print("                    BACKTEST RESULTS")
    print("="*80)
    print(f"Symbol: {summary['symbol']} | Timeframe: {summary['timeframe']}")
    print(f"Period: {summary['start_date']} to {summary['end_date']}")
    print(f"Data Points: {results['data_points']}")
    print("-"*80)
    print("PERFORMANCE METRICS:")
    print("-"*80)
    print(f"Initial Capital:     ${summary['initial_capital']:,.2f}")
    print(f"Final Capital:       ${summary['final_capital']:,.2f}")
    print(f"Total Return:        {summary['total_return_percent']:+.2f}% (${summary['total_return_absolute']:+.2f})")
    print(f"Max Drawdown:        {summary['max_drawdown_percent']:.2f}%")
    print(f"Sharpe Ratio:        {summary['sharpe_ratio']:.2f}")
    print("-"*80)
    print("TRADING STATISTICS:")
    print("-"*80)
    print(f"Total Trades:        {summary['total_trades']}")
    print(f"Winning Trades:      {summary['winning_trades']}")
    print(f"Losing Trades:       {summary['losing_trades']}")
    print(f"Win Rate:            {summary['win_rate_percent']:.1f}%")
    print(f"Average Win:         ${summary['avg_win']:,.2f}")
    print(f"Average Loss:        ${summary['avg_loss']:,.2f}")
    print(f"Profit Factor:       {summary['profit_factor']:.2f}")
    print(f"Commission Rate:     {summary['commission_rate']:.1f}%")
    print("="*80)


def main():
    """
    Example usage of the backtesting engine.
    """
    try:
        # Example backtest parameters
        symbol = 'BTC/USDT'
        timeframe = '1h'
        start_date = '2024-01-01'
        end_date = '2024-06-30'  # Shorter period for faster testing
        initial_capital = 10000.0
        commission = 0.001  # 0.1%

        print("Starting backtest example...")
        print(f"Testing {symbol} strategy from {start_date} to {end_date}")

        # Run backtest
        results = run_backtest(symbol, timeframe, start_date, end_date,
                             initial_capital, commission)

        # Print results
        print_backtest_results(results)

        # Save detailed results to file
        if 'error' not in results:
            import json
            with open('backtest_results.json', 'w') as f:
                # Convert timestamps to strings for JSON serialization
                results_copy = results.copy()
                for trade in results_copy['trades']:
                    if 'entry_time' in trade and trade['entry_time']:
                        trade['entry_time'] = str(trade['entry_time'])
                    if 'exit_time' in trade and trade['exit_time']:
                        trade['exit_time'] = str(trade['exit_time'])

                for pv in results_copy['portfolio_values']:
                    pv['timestamp'] = str(pv['timestamp'])

                json.dump(results_copy, f, indent=2, default=str)
            print("Detailed results saved to backtest_results.json")

    except Exception as e:
        print(f"Error in backtest example: {str(e)}")


if __name__ == "__main__":
    main()