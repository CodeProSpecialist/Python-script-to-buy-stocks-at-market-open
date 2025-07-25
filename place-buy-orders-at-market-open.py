import os
import alpaca_trade_api as tradeapi
import yfinance as yf
from time import sleep

# Load environment variables for Alpaca API
APIKEYID = os.getenv('APCA_API_KEY_ID')
APISECRETKEY = os.getenv('APCA_API_SECRET_KEY')
APIBASEURL = os.getenv('APCA_API_BASE_URL')

# Initialize the Alpaca API
api = tradeapi.REST(APIKEYID, APISECRETKEY, APIBASEURL)

# List of 30 S&P 500 symbols (Alpaca format, using BRK.B)
symbols = [
    'MSFT', 'NVDA', 'AAPL', 'AMZN', 'GOOGL', 'META', 'AVGO', 'BRK.B', 'TSLA', 'JPM',
    'UNH', 'V', 'MA', 'PG', 'JNJ', 'HD', 'MRK', 'ABBV', 'WMT', 'BAC',
    'KO', 'PFE', 'CSCO', 'DIS', 'INTC', 'CMCSA', 'VZ', 'ADBE', 'CRM', 'QCOM'
]

# Function to check if a symbol supports fractional trading
def is_fractional_trading_supported(symbol):
    try:
        asset = api.get_asset(symbol)
        return asset.fractionable
    except Exception as e:
        print(f"Error checking fractional trading for {symbol}: {e}")
        return False

# Function to get latest stock price using yfinance
def get_current_price(symbol):
    symbol = symbol.replace('.', '-')  # Replace '.' with '-' for yfinance
    try:
        stock_data = yf.Ticker(symbol)
        price = stock_data.history(period='1d')['Close'].iloc[-1]
        print(f"Fetched price for {symbol}: ${price:.2f}")
        return round(price, 2)
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

# Function to get prices for all symbols with 1.5s pause
def get_stock_prices(symbols):
    prices = {}
    for symbol in symbols:
        prices[symbol] = get_current_price(symbol)
        sleep(1.5)  # Pause 1.5 seconds after each price lookup
    return prices

# Function to place fractional order
def place_fractional_order(symbol, notional):
    try:
        if is_fractional_trading_supported(symbol):
            api.submit_order(
                symbol=symbol,
                notional=notional,  # Dollar amount for fractional shares
                side='buy',
                type='market',
                time_in_force='day'  # Use 'day' for fractional orders
            )
            print(f"Submitted $1.00 market order for {symbol} with day validity for next market open")
        else:
            print(f"{symbol} does not support fractional trading")
    except Exception as e:
        print(f"Error placing order for {symbol}: {e}")

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

        # Check for sufficient buying power
        if available_balance < 0:
            print(f"Insufficient buying power: ${cash_balance:.2f} available, ${total_order_cost:.2f} needed")
            return

        # Prompt for confirmation before placing orders
        print(f"\nAbout to place {len(valid_symbols)} buy orders of $1.00 each for execution at next market open.")
        confirmation = input("Is this OK? Type 'y' for yes: ").strip().lower()
        if confirmation != 'y':
            print("Order placement cancelled.")
            return

        # Place orders
        print("\nPlacing fractional orders for execution at next market open...")
        for symbol in valid_symbols:
            place_fractional_order(symbol, 1.00)
            sleep(0.5)  # Avoid API rate limits

        print("\nAll orders submitted successfully.")

    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()
