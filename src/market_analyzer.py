
# Tools for retrieving Nasdaq-100 stock symbols
from io import StringIO
from urllib.request import Request, urlopen

# Tools for financial data analysis
import pandas as pd
import yfinance as yf


# Public Nasdaq-100 constituent list
NASDAQ_URL = (
    "https://en.wikipedia.org/wiki/"
    "List_of_NASDAQ-100_companies"
)


# Temporary backup list if Wikipedia is unavailable
FALLBACK_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
    "GOOG", "META", "TSLA", "AVGO", "AMD",
    "NFLX", "COST", "ADBE", "INTC", "AMAT",
    "MU", "CSCO", "QCOM", "INTU", "PEP"
]


def get_nasdaq100_tickers():
    """Retrieve Nasdaq-100 stock symbols."""

    try:
        # Request the website using a browser-like header
        request = Request(
            NASDAQ_URL,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urlopen(request, timeout=20) as response:
            html = response.read().decode("utf-8")

        # Find the table containing stock symbols
        tables = pd.read_html(StringIO(html))

        for table in tables:
            if "Ticker" in table.columns:
                tickers = table["Ticker"].dropna()

                return list(dict.fromkeys(
                    str(ticker).strip().replace(".", "-")
                    for ticker in tickers
                ))

        raise ValueError("Nasdaq-100 ticker table not found")

    except Exception as error:
        print(f"Nasdaq-100 list error: {error}")
        print("Using temporary backup stock list.")
        print("WARNING: This is a partial market scan.")

        return FALLBACK_TICKERS


def analyze_stock(ticker):
    """Calculate stock returns, volume, and anomalies."""

    # Download approximately six months of stock data
    stock = yf.Ticker(ticker)
    data = stock.history(period="6mo", auto_adjust=True)

    if data.empty:
        return None

    # Keep valid closing prices and matching volumes
    data = data[["Close", "Volume"]].copy()
    data = data.dropna(subset=["Close"])

    # Remove invalid or zero closing prices
    data = data[data["Close"] > 0]

    # Require enough history for momentum calculations
    if len(data) < 30:
        return None

    close = data["Close"]
    volume = data["Volume"]

    # Calculate daily returns without filling missing values
    returns = close.pct_change(fill_method=None).dropna()

    if len(returns) < 21:
        return None

    # Latest daily price change (%)
    daily_change = (
        (close.iloc[-1] / close.iloc[-2]) - 1
    ) * 100

    # Price change over five trading sessions (%)
    weekly_change = (
        (close.iloc[-1] / close.iloc[-6]) - 1
    ) * 100

    # Price change over twenty trading sessions (%)
    monthly_change = (
        (close.iloc[-1] / close.iloc[-21]) - 1
    ) * 100

    # Compare latest return with previous 20 sessions
    baseline = returns.iloc[-21:-1]

    average = baseline.mean()
    volatility = baseline.std()

    # Statistical measure of unusual price movement
    z_score = (
        (returns.iloc[-1] - average) / volatility
        if pd.notna(volatility) and volatility > 0
        else 0
    )

    # Compare latest trading volume with prior 20 sessions
    average_volume = volume.iloc[-21:-1].mean()

    volume_ratio = (
        volume.iloc[-1] / average_volume
        if pd.notna(average_volume) and average_volume > 0
        else 0
    )

    # Flag unusual price movements or trading volume
    is_anomaly = (
        abs(daily_change) >= 5
        or abs(z_score) >= 2
        or volume_ratio >= 1.5
    )

    # Flag strong upward momentum
    is_rising = (
        weekly_change >= 10
        or monthly_change >= 20
    )

    # Calculate a combined anomaly ranking score
    anomaly_score = (
        abs(z_score)
        + min(volume_ratio, 5)
        + abs(daily_change) / 5
    )

    return {
        "ticker": ticker,
        "date": str(data.index[-1].date()),
        "daily_change": round(float(daily_change), 2),
        "weekly_change": round(float(weekly_change), 2),
        "monthly_change": round(float(monthly_change), 2),
        "z_score": round(float(z_score), 2),
        "volume_ratio": round(float(volume_ratio), 2),
        "anomaly_score": round(float(anomaly_score), 2),
        "is_anomaly": bool(is_anomaly),
        "is_rising": bool(is_rising)
    }


def scan_market():
    """Scan Nasdaq-100 stocks and rank unusual movements."""

    tickers = get_nasdaq100_tickers()
    results = []

    print(f"Scanning {len(tickers)} Nasdaq-100 symbols...")

    # Download and analyze each stock
    for ticker in tickers:
        try:
            result = analyze_stock(ticker)

            if result:
                results.append(result)

        except Exception as error:
            print(f"Skipped {ticker}: {error}")

    if not results:
        raise RuntimeError("No stock data retrieved")

    # Find abnormal stock movements
    anomalies = [
        stock for stock in results
        if stock["is_anomaly"]
    ]

    # Rank by combined anomaly score
    anomalies.sort(
        key=lambda stock: stock["anomaly_score"],
        reverse=True
    )

    # Find stocks with upward momentum
    rising = [
        stock for stock in results
        if stock["is_rising"]
    ]

    # Rank by strongest weekly gains
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
