# Import tools for date, time, and weather data
from datetime import datetime
from zoneinfo import ZoneInfo
from weather import get_weather


# Main function that starts the Morning Brief Agent
def main():

    # Get the current date and time in Eastern Time
    now = datetime.now(ZoneInfo("America/New_York"))

    # Display the project title
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
        # Continue running if the weather API fails
        print(f"Unable to retrieve weather: {error}")

    # Other sections will be added later
    print("\n--- COMING SOON ---")
    print("Financial Markets")
    print("General & Technology News")
    print("K-pop & Entertainment News")
    print("AI-Powered Insights")

    print("\nStatus: Morning Brief completed!")


if __name__ == "__main__":
    main()
