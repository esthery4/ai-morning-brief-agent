# Import Yahoo Finance library
import yfinance as yf


# Define the market indices we want to track
MARKETS = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI"
}


# Retrieve the latest market data
def get_markets():
    results = []

    for name, symbol in MARKETS.items():
        try:
            # Download recent daily closing prices
            data = yf.Ticker(symbol).history(period="5d")

            if len(data) < 2:
                raise ValueError("Not enough price data")

            # Get the two latest closing prices
            previous = float(data["Close"].iloc[-2])
            latest = float(data["Close"].iloc[-1])

            # Calculate percentage change
            change = ((latest - previous) / previous) * 100

            results.append({
                "name": name,
                "price": round(latest, 2),
                "change_percent": round(change, 2),
                "date": str(data.index[-1].date())
            })

        except Exception as error:
            print(f"Unable to retrieve {name}: {error}")

    return results
