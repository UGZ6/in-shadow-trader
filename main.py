#!/usr/bin/env python3
"""
Trading Bot Main Entry Point

This module contains the main execution logic for the trading bot.
It orchestrates data fetching, technical analysis, and trading decisions
in a continuous loop.

Author: Trading Bot System
"""

import time
import pandas as pd
from data_handler import get_historical_data, calculate_indicators
from strategy import check_buy_condition, check_sell_condition


def run_bot():
    """
    Main trading bot execution function.

    This function runs the trading bot in a continuous loop, performing:
    1. Data fetching and indicator calculation
    2. Buy/sell signal detection
    3. Position management
    4. Wait period between iterations

    The bot operates on a 1-hour timeframe and maintains state between iterations
    to track current position and entry price.
    """

    # Initial configuration settings
    symbol = 'BTC/USDT'
    timeframe = '1h'
    in_position = False  # Position status: False = no position, True = holding position
    entry_price = 0      # Entry price for current position (0 when no position)

    # Bot startup message
    print("=" * 60)
    print("> TRADING BOT IS RUNNING...")
    print(f"=Ê Symbol: {symbol}")
    print(f"ð Timeframe: {timeframe}")
    print(f"=¼ Initial Position: {'HOLDING' if in_position else 'WAITING TO BUY'}")
    print("=" * 60)
    print()

    # Main trading loop - runs continuously
    while True:
        try:
            print(f"ð {time.strftime('%Y-%m-%d %H:%M:%S')} - Starting new analysis cycle...")

            # ================================================================
            # STEP 1: DATA FETCHING AND INDICATOR CALCULATION
            # ================================================================

            print("=á Fetching new data...")

            try:
                # Fetch latest historical data (200 candles for sufficient indicator calculation)
                df = get_historical_data(symbol=symbol, timeframe=timeframe, limit=200)

                if df is None or df.empty:
                    print("L ERROR: No data received from exchange")
                    print("ó Waiting 5 minutes before retry...")
                    time.sleep(300)  # Wait 5 minutes before retry
                    continue

                print(f" Successfully fetched {len(df)} candles")

                # Calculate all technical indicators
                df = calculate_indicators(df)

                if df is None or df.empty:
                    print("L ERROR: Indicator calculation failed")
                    print("ó Waiting 5 minutes before retry...")
                    time.sleep(300)  # Wait 5 minutes before retry
                    continue

                print(" Technical indicators calculated successfully")

                # Get current price for display
                current_price = df['close'].iloc[-1]
                print(f"=° Current {symbol} Price: ${current_price:.2f}")

            except Exception as data_error:
                print(f"L DATA FETCH ERROR: {str(data_error)}")
                print("ó Waiting 10 minutes before retry...")
                time.sleep(600)  # Wait 10 minutes on data error
                continue

            # ================================================================
            # STEP 2: TRADING DECISION LOGIC
            # ================================================================

            print(">à Analyzing market conditions...")

            # Decision logic based on current position status
            if not in_position:
                # Currently NOT in position - looking for BUY signal
                print("=Í Status: WAITING TO BUY - Checking buy conditions...")

                try:
                    # Check if buy conditions are met
                    buy_signal = check_buy_condition(df)

                    if buy_signal:
                        # BUY SIGNAL DETECTED
                        entry_price = df['close'].iloc[-1]
                        in_position = True

                        print("=€ BUY SIGNAL DETECTED! EXECUTING BUY ORDER.")
                        print(f"=µ Entry Price: ${entry_price:.2f}")
                        print(f"=Ê Position Status: HOLDING")

                        # Log the buy action with timestamp
                        print(f"=Ý BUY ORDER LOGGED: {time.strftime('%Y-%m-%d %H:%M:%S')} at ${entry_price:.2f}")

                    else:
                        print("ø  No buy signal detected. Waiting for entry opportunity...")

                except Exception as buy_error:
                    print(f"L BUY SIGNAL CHECK ERROR: {str(buy_error)}")

            else:
                # Currently IN position - looking for SELL signal
                print("=Í Status: HOLDING POSITION - Checking sell conditions...")
                print(f"=° Entry Price: ${entry_price:.2f}")

                # Calculate current P&L for display
                current_price = df['close'].iloc[-1]
                pnl_percentage = ((current_price - entry_price) / entry_price) * 100
                pnl_status = "PROFIT" if pnl_percentage > 0 else "LOSS"

                print(f"=È Current P&L: {pnl_percentage:+.2f}% ({pnl_status})")

                try:
                    # Check if sell conditions are met (pass entry_price for stop-loss/take-profit calculations)
                    sell_signal = check_sell_condition(df, entry_price)

                    if sell_signal:
                        # SELL SIGNAL DETECTED
                        exit_price = df['close'].iloc[-1]
                        final_pnl = ((exit_price - entry_price) / entry_price) * 100

                        print("=É SELL SIGNAL DETECTED! EXECUTING SELL ORDER.")
                        print(f"=µ Exit Price: ${exit_price:.2f}")
                        print(f"=¹ Final P&L: {final_pnl:+.2f}%")

                        # Reset position variables
                        in_position = False
                        entry_price = 0

                        print(f"=Ê Position Status: WAITING TO BUY")

                        # Log the sell action with timestamp
                        print(f"=Ý SELL ORDER LOGGED: {time.strftime('%Y-%m-%d %H:%M:%S')} at ${exit_price:.2f}")

                    else:
                        print("ø  No sell signal detected. Holding position...")

                except Exception as sell_error:
                    print(f"L SELL SIGNAL CHECK ERROR: {str(sell_error)}")

            # ================================================================
            # STEP 3: WAIT PERIOD
            # ================================================================

            print("ó Analysis complete. Waiting 1 hour for next cycle...")
            print("-" * 60)
            print()

            # Wait 1 hour (3600 seconds) before next iteration
            # This matches the 1h timeframe for optimal signal timing
            time.sleep(3600)

        except KeyboardInterrupt:
            # Handle Ctrl+C graceful shutdown
            print()
            print("=Ñ SHUTDOWN SIGNAL RECEIVED")
            print("> Trading Bot is shutting down gracefully...")

            if in_position:
                print("   WARNING: Bot is shutting down while holding a position!")
                print(f"=° Current Entry Price: ${entry_price:.2f}")
                print("=' Consider manually closing the position if needed.")

            print(" Trading Bot stopped successfully")
            break

        except Exception as main_error:
            # Handle any unexpected errors in the main loop
            print(f"L UNEXPECTED ERROR IN MAIN LOOP: {str(main_error)}")
            print("= Bot will continue running after 5-minute recovery period...")
            print("-" * 60)

            # Wait 5 minutes before continuing to prevent rapid error loops
            time.sleep(300)
            continue


def main():
    """
    Program entry point with additional error handling and setup.

    This function serves as the main entry point and provides an additional
    layer of error handling around the bot execution.
    """

    try:
        print("=€ Initializing Trading Bot...")
        print("=Ë Checking dependencies and configuration...")

        # Start the main bot execution
        run_bot()

    except ImportError as import_error:
        print(f"L IMPORT ERROR: {str(import_error)}")
        print("=' Please ensure all required modules are installed:")
        print("   - pandas: pip install pandas")
        print("   - ccxt: pip install ccxt")
        print("   - pandas_ta: pip install pandas_ta")
        print("   - Ensure data_handler.py and strategy.py exist")

    except Exception as startup_error:
        print(f"L STARTUP ERROR: {str(startup_error)}")
        print("=' Please check your configuration and try again")


# Program entry point
if __name__ == "__main__":
    main()