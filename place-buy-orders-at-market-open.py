import os
import alpaca_trade_api as tradeapi
import yfinance as yf
from datetime import datetime, time
import pytz
from time import sleep

# Load environment variables for Alpaca API
APIKEYID = os.getenv('APCA_API_KEY_ID')
APISECRETKEY = os.getenv('APCA_API_SECRET_KEY')
APIBASEURL = os.getenv('APCA_API_BASE_URL')

# Initialize the Alpaca API
api = tradeapi.REST(APIKEYID, APISECRETKEY, APIBASEURL)

# List of S&P 500 symbols
symbols = [
    'MSFT', 'NVDA', 'AAPL', 'AMZN', 'GOOGL', 'META', 'AVGO', 'BRK-B', 'TSLA', 'JPM',
    'UNH', 'V', 'MA', 'PG', 'JNJ', 'HD', 'MRK', 'ABBV', 'WMT', 'BAC',
    'KO', 'PFE', 'CSCO', 'DIS', 'INTC', 'CMCSA', 'VZ', 'ADBE', 'CRM', 'QCOM',
    'AMD', 'TXN', 'AMGN', 'ISRG', 'GILD', 'BMY', 'SCHW', 'C', 'GS', 'NFLX',
    'PEP', 'COST', 'MCD', 'T', 'TMO', 'LLY'
]

# Function to check if a symbol supports fractional trading
def is_fractional_trading_supported(symbol):
    try:
        asset = api.get_asset(symbol)
        return asset.fractionable
    except Exception as e:
        print(f"Error checking fractional trading for {symbol}: {e}")
        return False

# Function to get latest stock prices using yfinance
def get_stock_prices(symbols):
    prices = {}
    try:
        tickers = yf.Tickers(' '.join(symbols))
        for symbol in symbols:
            try:
                ticker = tickers.tickers[symbol]
                price = ticker.history(period='1d')['Close'].iloc[-1]
                prices[symbol] = round(price, 2)
            except Exception as e:
                print(f"Error fetching price for {symbol}: {e}")
                prices[symbol] = None
    except Exception as e:
        print(f"Error fetching prices: {e}")
    return prices

# Function to place fractional order at market open
def place_fractional_order_at_open(symbol, notional):
    try:
        if is_fractional_trading_supported(symbol):
            api.submit_order(
                symbol=symbol,
                notional=notional,  # Dollar amount for fractional shares
                side='buy',
                type='market',
                time_in_force='opg'  # Order executes at market open
            )
            print(f"Submitted $1.00 market order for {symbol} to execute at market open")
        else:
            print(f"{symbol} does not support fractional trading")
    except Exception as e:
        print(f"Error placing order for {symbol}: {e}")

# Function to check if market is open
def is_market_open():
    clock = api.get_clock()
    return clock.is_open

# Main execution
def main():
    try:
        # Get account balance
        account = api.get_account()
        cash_balance = float(account.cash)
        print(f"Current Alpaca account cash balance: ${cash_balance:.2f}")

        # Get stock prices
        print("\nFetching latest stock prices from yfinance...")
        prices = get_stock_prices(symbols)

        # Calculate total order cost
        total_order_cost = 0.0
        valid_symbols = []
        for symbol in symbols:
            if prices.get(symbol) is not None:
                total_order_cost += 1.00  # $1.00 per symbol
                valid_symbols.append(symbol)
            else:
                print(f"Skipping {symbol} due to missing price data")

        print(f"\nTotal order cost for {len(valid_symbols)} symbols: ${total_order_cost:.2f}")
        available_balance = cash_balance - total_order_cost
        print(f"Available cash balance after orders: ${available_balance:.2f}")

        # Check if market is open
        if is_market_open():
            print("\nMarket is currently open. Orders will be submitted for the next market open.")
        else:
            print("\nMarket is currently closed. Orders will be submitted for the next market open.")

        # Check for sufficient buying power
        if available_balance < 0:
            print(f"Insufficient buying power: ${cash_balance:.2f} available, ${total_order_cost:.2f} needed")
            return

        # Place orders
        print("\nPlacing orders for execution at market open...")
        for symbol in valid_symbols:
            place_fractional_order_at_open(symbol, 1.00)
            sleep(0.5)  # Avoid API rate limits

        # Print confirmation message
        print("\nAsk is this ok? Yes ? Type y for yes.")

    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()
