# Import tools for getting the current date and time
from datetime import datetime
from zoneinfo import ZoneInfo


# Main function that starts the Morning Brief Agent
def main():

    # Get the current date and time in Eastern Time
    now = datetime.now(ZoneInfo("America/New_York"))

    # Display the project title
    print("=" * 40)
    print("AI MORNING BRIEF AGENT")
    print("=" * 40)

    # Display today's date and time
    print(f"Date: {now.strftime('%A, %B %d, %Y')}")
    print(f"Time: {now.strftime('%I:%M %p %Z')}")

    # List the sections of the future morning brief
    print("\nToday's Morning Brief:")
    print("1. Weather Forecast")
    print("2. Financial Markets")
    print("3. General & Technology News")
    print("4. K-pop & Entertainment News")
    print("5. AI-Powered Insights")

    # Confirm the program started successfully
    print("\nStatus: Agent initialized successfully!")


# Run the main function when this file is executed
if __name__ == "__main__":
    main()
