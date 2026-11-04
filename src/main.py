# Import date, weather, and financial analysis tools
from datetime import datetime
from zoneinfo import ZoneInfo
from weather import get_weather
from markets import get_markets
from market_analyzer import scan_market


def main():
    # Get current Eastern Time
    now = datetime.now(ZoneInfo("America/New_York"))

    print("=" * 40)
    print("AI MORNING BRIEF AGENT")
    print("=" * 40)

    print(f"Date: {now.strftime('%A, %B %d, %Y')}")
    print(f"Time: {now.strftime('%I:%M %p %Z')}")

    # Retrieve weather information
    print("\n--- WEATHER FORECAST ---")

    try:
        weather = get_weather()
        print(f"Location: {weather['location']}")
        print(f"Temperature: {weather['temperature']}°F")
        print(f"Feels like: {weather['feels_like']}°F")

    except Exception as error:
        print(f"Weather error: {error}")

    # Retrieve major market index performance
    print("\n--- MARKET OVERVIEW ---")

    try:
        markets = get_markets()

        for market in markets:
            print(
                f"{market['name']}: "
                f"{market['change_percent']:+.2f}%"
            )

    except Exception as error:
        print(f"Market overview error: {error}")

    # Scan Nasdaq-100 stocks for unusual movements
    print("\n--- NASDAQ-100 ANOMALY DETECTOR ---")

    try:
        report = scan_market()

        print(
            f"Successfully scanned: "
            f"{report['scanned']}/{report['expected']}"
        )

        # Display the largest abnormal movements
        print("\nTop Unusual Stock Movements:")

        if not report["anomalies"]:
            print("No anomalies detected.")

        for stock in report["anomalies"]:
            print(
                f"{stock['ticker']}: "
                f"{stock['daily_change']:+.2f}% | "
                f"Z-score: {stock['z_score']:.2f} | "
                f"Volume: {stock['volume_ratio']:.2f}x | "
                f"As of: {stock['date']}"
            )

        # Display stocks gaining momentum
        print("\nTop Rising Stocks:")

        if not report["rising"]:
            print("No stocks met the momentum thresholds.")

        for stock in report["rising"]:
            print(
                f"{stock['ticker']}: "
                f"5-day {stock['weekly_change']:+.2f}% | "
                f"20-day {stock['monthly_change']:+.2f}% | "
                f"As of: {stock['date']}"
            )

    except Exception as error:
        print(f"Anomaly detector error: {error}")

    # Future AI features
    print("\n--- COMING SOON ---")
    print("AI Stock News Investigation")
    print("Industry Analysis")
    print("Personalized Morning Email")

    print("\nStatus: Morning Brief completed!")


if __name__ == "__main__":
    main()
