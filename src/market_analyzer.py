# Tools for downloading and analyzing stock data
import pandas as pd
import yfinance as yf

# Public Nasdaq-100 constituent list
NASDAQ_URL = (
    "https://en.wikipedia.org/wiki/"
    "List_of_NASDAQ-100_companies"
)


def get_nasdaq100_tickers():
    # Read the Nasdaq-100 company table
    tables = pd.read_html(NASDAQ_URL)

    for table in tables:
        if "Ticker" in table.columns:
            tickers = table["Ticker"].dropna().astype(str)

            # Convert symbols into Yahoo Finance format
            return [
                ticker.strip().replace(".", "-")
                for ticker in tickers
            ]

    raise ValueError("Nasdaq-100 ticker list not found")


def analyze_stock(ticker):
    # Download roughly six months of daily prices
    stock = yf.Ticker(ticker)
    data = stock.history(period="6mo", auto_adjust=True)

    if len(data) < 30:
        return None

    close = data["Close"]
    volume = data["Volume"]

    # Calculate daily percentage returns
    returns = close.pct_change().dropna()

    # Latest daily return
    daily_change = returns.iloc[-1] * 100

    # Calculate 5-day and 20-day momentum
    weekly_change = (
        (close.iloc[-1] / close.iloc[-6]) - 1
    ) * 100

    monthly_change = (
        (close.iloc[-1] / close.iloc[-21]) - 1
    ) * 100

    # Compare today against the previous 20 returns
    baseline = returns.iloc[-21:-1]
    average = baseline.mean()
    volatility = baseline.std()

    z_score = (
        (returns.iloc[-1] - average) / volatility
        if volatility > 0 else 0
    )

    # Compare volume against its previous 20 sessions
    average_volume = volume.iloc[-21:-1].mean()
    volume_ratio = (
        volume.iloc[-1] / average_volume
        if average_volume > 0 else 0
    )

    # Identify abnormal movements
    is_anomaly = (
        abs(daily_change) >= 5
        or abs(z_score) >= 2
        or volume_ratio >= 1.5
    )

    # Identify stocks gaining momentum
    is_rising = (
        weekly_change >= 10
        or monthly_change >= 20
    )

    return {
        "ticker": ticker,
        "date": str(data.index[-1].date()),
        "daily_change": round(float(daily_change), 2),
        "weekly_change": round(float(weekly_change), 2),
        "monthly_change": round(float(monthly_change), 2),
        "z_score": round(float(z_score), 2),
        "volume_ratio": round(float(volume_ratio), 2),
        "is_anomaly": bool(is_anomaly),
        "is_rising": bool(is_rising)
    }


def scan_market():
    # Get all Nasdaq-100 stock symbols
    tickers = get_nasdaq100_tickers()
    results = []

    print(f"Scanning {len(tickers)} Nasdaq-100 symbols...")

    # Analyze each stock individually
    for ticker in tickers:
        try:
            result = analyze_stock(ticker)

            if result:
                results.append(result)

        except Exception as error:
            print(f"Skipped {ticker}: {error}")

    if not results:
        raise RuntimeError("No Nasdaq-100 data retrieved")

    # Keep all abnormal stocks
    anomalies = [
        stock for stock in results
        if stock["is_anomaly"]
    ]

    # Rank anomalies by absolute daily movement
    anomalies.sort(
        key=lambda stock: abs(stock["daily_change"]),
        reverse=True
    )

    # Rank rising stocks by weekly performance
    rising = [
        stock for stock in results
        if stock["is_rising"]
    ]

    rising.sort(
        key=lambda stock: stock["weekly_change"],
        reverse=True
    )

    return {
        "anomalies": anomalies[:5],
        "rising": rising[:5],
        "scanned": len(results),
        "expected": len(tickers)
    }
