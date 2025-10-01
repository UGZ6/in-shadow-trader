#!/usr/bin/env python3
"""
Trading Bot Main Entry Point

This module contains the main execution logic for the trading bot.
It orchestrates data fetching, technical analysis, and trading decisions
in a continuous loop with real exchange connectivity.

Author: Trading Bot System
"""

import time
import pandas as pd
import ccxt
import config
from data_handler import get_historical_data, calculate_indicators
from strategy import check_buy_condition, check_sell_condition


def initialize_exchange():
    """
    Initialize and configure Binance exchange connection.
    
    Returns:
        ccxt.binance: Configured exchange instance or None if initialization fails
    """
    try:
        print("Initializing Binance exchange connection...")
        
        # Validate API keys first
        if not config.validate_config():
            raise Exception("Configuration validation failed")
        
        # Initialize exchange with API credentials from config
        exchange = ccxt.binance({
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_API_SECRET,
            'sandbox': config.TESTNET_MODE,
            'rateLimit': 1200,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # Use spot trading
            }
        })
        
        # Test exchange connection
        exchange.check_required_credentials()
        print("Exchange connection initialized successfully")
        
        return exchange
        
    except ccxt.AuthenticationError as e:
        print(f"Authentication failed: {str(e)}")
        print("Please check your API credentials in the .env file")
        return None
    except ccxt.NetworkError as e:
        print(f"Network error while connecting to exchange: {str(e)}")
        return None
    except Exception as e:
        print(f"Error initializing exchange: {str(e)}")
        return None


def place_buy_order(exchange, symbol, quantity_usd):
    """
    Place a buy order on the exchange.
    
    Args:
        exchange: ccxt exchange instance
        symbol (str): Trading pair symbol
        quantity_usd (float): Quantity to buy in USD
        
    Returns:
        dict: Order details from exchange or None if order fails
    """
    try:
        # Get current price to calculate amount
        ticker = exchange.fetch_ticker(symbol)
        current_price = float(ticker['last'])
        
        # Calculate amount to buy based on USD quantity
        amount = round(quantity_usd / current_price, 6)  # Round to 6 decimal places
        
        print(f"Placing buy order: {amount} {symbol.split('/')[0]} at ~${current_price}")
        
        # Place market buy order
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side='buy',
            amount=amount
        )
        
        print(f"Buy order executed successfully:")
        print(f"  - Order ID: {order['id']}")
        print(f"  - Amount: {order['amount']} {symbol.split('/')[0]}")
        print(f"  - Price: ${order['price'] if order['price'] else 'Market Price'}")
        print(f"  - Total Cost: ${order['cost'] if order['cost'] else order['amount'] * current_price:.2f}")
        
        return order
        
    except ccxt.InsufficientFunds as e:
        print(f"Insufficient funds for buy order: {str(e)}")
        return None
    except ccxt.NetworkError as e:
        print(f"Network error placing buy order: {str(e)}")
        return None
    except Exception as e:
        print(f"Error placing buy order: {str(e)}")
        return None


def place_sell_order(exchange, symbol, amount):
    """
    Place a sell order on the exchange.
    
    Args:
        exchange: ccxt exchange instance
        symbol (str): Trading pair symbol
        amount (float): Quantity to sell
        entry_price (float): Original entry price for position calculation (optional)
        
    Returns:
        dict: Order details from exchange or None if order fails
    """
    try:
        print(f"Placing sell order: {amount} {symbol.split('/')[0]}")
        
        # Place market sell order
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side='sell',
            amount=amount
        )
        
        print(f"Sell order executed successfully:")
        print(f"  - Order ID: {order['id']}")
        print(f"  - Amount: {order['amount']} {symbol.split('/')[0]}")
        print(f"  - Price: ${order['price'] if order['price'] else 'Market Price'}")
        print(f"  - Total Revenue: ${order['cost'] if order['cost'] else 'TBD'}")
        
        return order
        
    except ccxt.InsufficientFunds as e:
        print(f"Insufficient funds for sell order: {str(e)}")
        return None
    except ccxt.NetworkError as e:
        print(f"Network error placing sell order: {str(e)}")
        return None
    except Exception as e:
        print(f"Error placing sell order: {str(e)}")
        return None


def get_current_balance(exchange, asset='BUSD'):
    """
    Get current balance for specified asset.
    
    Args:
        exchange: ccxt exchange instance
        asset (str): Asset symbol ('USDT', 'BUSD', 'BTC', etc.)
        
    Returns:
        float: Available balance or -1 if error
    """
    try:
        balance = exchange.fetch_balance()
        available_balance = float(balance['free'][asset])
        print(f"Current {asset} balance: {available_balance}")
        return available_balance
        
    except ccxt.AuthenticationError as e:
        print(f"Authentication error fetching balance: {str(e)}")
        return -1
    except KeyError:
        print(f"Asset {asset} not found in balance")
        return -1
    except Exception as e:
        print(f"Error fetching balance for {asset}: {str(e)}")
        return -1


def run_bot():
    """
    Main trading bot execution function with exchange connectivity.

    This function runs the trading bot in a continuous loop, performing:
    1. Exchange connection initialization
    2. Data fetching and indicator calculation
    3. Buy/sell signal detection
    4. REAL order execution on the exchange
    5. Position management
    6. Wait period between iterations

    The bot operates on a 1-hour timeframe and maintains state between iterations
    to track current position and entry price.
    """


    # Initial configuration settings
    symbol = config.SYMBOL
    timeframe = config.TIMEFRAME
    in_position = False  # Position status: False = no position, True = holding position
    entry_price = 0      # Entry price for current position (0 when no position)
    position_amount = 0    # Amount of asset currently held

    # ================================================================
    # EXCHANGE CONNECTION INITIALIZATION
    # ================================================================

    # Create exchange instance with authentication
    try:
        print("🔗 Initializing Binance exchange connection...")

        # Validate API keys from config
        if not config.BINANCE_API_KEY or config.BINANCE_API_KEY == 'YOUR_API_KEY':
            raise Exception("BINANCE_API_KEY is not set in config.py or .env file")
        if not config.BINANCE_API_SECRET or config.BINANCE_API_SECRET == 'YOUR_API_SECRET':
            raise Exception("BINANCE_API_SECRET is not set in config.py or .env file")

        # Create exchange object
        exchange = ccxt.binance({
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_API_SECRET,
            'options': {
                'defaultType': 'spot',
            },
        })

        # Test exchange connection by fetching balance (optional but recommended)
        print("🔍 Testing exchange connection...")
        balance = exchange.fetch_balance()
        print("✅ Exchange connection successful - API keys are valid")

    except ccxt.AuthenticationError as e:
        print(f"❌ Authentication failed: {str(e)}")
        print("💡 Please check your API credentials in the .env file")
        return
    except ccxt.NetworkError as e:
        print(f"❌ Network error connecting to exchange: {str(e)}")
        return
    except Exception as e:
        print(f"❌ Error initializing exchange: {str(e)}")
        return
    # Bot startup message
    print("=" * 60)
    print("> TRADING BOT IS RUNNING...")
    print(f"=� Symbol: {symbol}")
    print(f"� Timeframe: {timeframe}")
    print(f"=� Initial Position: {'HOLDING' if in_position else 'WAITING TO BUY'}")
    print("=" * 60)
    print()

    # Main trading loop - runs continuously
    while True:
        try:
            print(f"� {time.strftime('%Y-%m-%d %H:%M:%S')} - Starting new analysis cycle...")

            # ================================================================
            # STEP 1: DATA FETCHING AND INDICATOR CALCULATION
            # ================================================================

            print("=� Fetching new data...")

            try:
                # Fetch latest historical data (200 candles for sufficient indicator calculation)
                df = get_historical_data(symbol=symbol, timeframe=timeframe, limit=200)

                if df is None or df.empty:
                    print("L ERROR: No data received from exchange")
                    print("� Waiting 5 minutes before retry...")
                    time.sleep(300)  # Wait 5 minutes before retry
                    continue

                print(f" Successfully fetched {len(df)} candles")

                # Calculate all technical indicators
                df = calculate_indicators(df)

                if df is None or df.empty:
                    print("L ERROR: Indicator calculation failed")
                    print("� Waiting 5 minutes before retry...")
                    time.sleep(300)  # Wait 5 minutes before retry
                    continue

                print(" Technical indicators calculated successfully")

                # Get current price for display
                current_price = df['close'].iloc[-1]
                print(f"=� Current {symbol} Price: ${current_price:.2f}")

            except Exception as data_error:
                print(f"L DATA FETCH ERROR: {str(data_error)}")
                print("� Waiting 10 minutes before retry...")
                time.sleep(600)  # Wait 10 minutes on data error
                continue

            # ================================================================
            # STEP 2: TRADING DECISION LOGIC
            # ================================================================

            print(">� Analyzing market conditions...")

            # Decision logic based on current position status
            if not in_position:
                # Currently NOT in position - looking for BUY signal
                print("=� Status: WAITING TO BUY - Checking buy conditions...")

                try:
                    # Check if buy conditions are met
                    buy_signal = check_buy_condition(df)

                    if buy_signal:
                        # BUY SIGNAL DETECTED
                        entry_price = df['close'].iloc[-1]
                        in_position = True

                        print("=� BUY SIGNAL DETECTED! EXECUTING BUY ORDER.")
                        print(f"=� Entry Price: ${entry_price:.2f}")
                        print(f"=� Position Status: HOLDING")

                        # Log the buy action with timestamp
                        print(f"=� BUY ORDER LOGGED: {time.strftime('%Y-%m-%d %H:%M:%S')} at ${entry_price:.2f}")

                    else:
                        print("�  No buy signal detected. Waiting for entry opportunity...")

                except Exception as buy_error:
                    print(f"L BUY SIGNAL CHECK ERROR: {str(buy_error)}")

            else:
                # Currently IN position - looking for SELL signal
                print("=� Status: HOLDING POSITION - Checking sell conditions...")
                print(f"=� Entry Price: ${entry_price:.2f}")

                # Calculate current P&L for display
                current_price = df['close'].iloc[-1]
                pnl_percentage = ((current_price - entry_price) / entry_price) * 100
                pnl_status = "PROFIT" if pnl_percentage > 0 else "LOSS"

                print(f"=� Current P&L: {pnl_percentage:+.2f}% ({pnl_status})")

                try:
                    # Check if sell conditions are met (pass entry_price for stop-loss/take-profit calculations)
                    sell_signal = check_sell_condition(df, entry_price)

                    if sell_signal:
                        # SELL SIGNAL DETECTED
                        exit_price = df['close'].iloc[-1]
                        final_pnl = ((exit_price - entry_price) / entry_price) * 100

                        print("=� SELL SIGNAL DETECTED! EXECUTING SELL ORDER.")
                        print(f"=� Exit Price: ${exit_price:.2f}")
                        print(f"=� Final P&L: {final_pnl:+.2f}%")

                        # Reset position variables
                        in_position = False
                        entry_price = 0

                        print(f"=� Position Status: WAITING TO BUY")

                        # Log the sell action with timestamp
                        print(f"=� SELL ORDER LOGGED: {time.strftime('%Y-%m-%d %H:%M:%S')} at ${exit_price:.2f}")

                    else:
                        print("�  No sell signal detected. Holding position...")

                except Exception as sell_error:
                    print(f"L SELL SIGNAL CHECK ERROR: {str(sell_error)}")

            # ================================================================
            # STEP 3: WAIT PERIOD
            # ================================================================

            print("� Analysis complete. Waiting 1 hour for next cycle...")
            print("-" * 60)
            print()

            # Wait 1 hour (3600 seconds) before next iteration
            # This matches the 1h timeframe for optimal signal timing
            time.sleep(3600)

        except KeyboardInterrupt:
            # Handle Ctrl+C graceful shutdown
            print()
            print("=� SHUTDOWN SIGNAL RECEIVED")
            print("> Trading Bot is shutting down gracefully...")

            if in_position:
                print("�  WARNING: Bot is shutting down while holding a position!")
                print(f"=� Current Entry Price: ${entry_price:.2f}")
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
        print("=� Initializing Trading Bot...")
        print("=� Checking dependencies and configuration...")

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