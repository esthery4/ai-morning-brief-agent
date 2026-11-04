# Import date, time, weather, and market tools
from datetime import datetime
from zoneinfo import ZoneInfo
from weather import get_weather
from markets import get_markets


# Main function for the Morning Brief Agent
def main():

    # Get the current Eastern Time
    now = datetime.now(ZoneInfo("America/New_York"))

    print("=" * 40)
    print("AI MORNING BRIEF AGENT")
    print("=" * 40)

    print(f"Date: {now.strftime('%A, %B %d, %Y')}")
    print(f"Time: {now.strftime('%I:%M %p %Z')}")

    # Retrieve live weather data
    print("\n--- WEATHER FORECAST ---")

    try:
        weather = get_weather()

        print(f"Location: {weather['location']}")
        print(f"Temperature: {weather['temperature']}°F")
        print(f"Feels like: {weather['feels_like']}°F")
        print(f"Precipitation: {weather['precipitation']} mm")

    except Exception as error:
        print(f"Unable to retrieve weather: {error}")

    # Retrieve financial market data
    print("\n--- FINANCIAL MARKETS ---")

    markets = get_markets()

    if markets:
        for market in markets:
            print(f"\n{market['name']}")
            print(f"Latest Close: {market['price']:,.2f}")
            print(f"Change: {market['change_percent']:+.2f}%")
            print(f"As of: {market['date']}")
    else:
        print("No market data available.")

    # Upcoming features
    print("\n--- COMING SOON ---")
    print("General & Technology News")
    print("K-pop & Entertainment News")
    print("AI-Powered Insights")

    print("\nStatus: Morning Brief completed!")


if __name__ == "__main__":
    main()
