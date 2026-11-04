# Import tools for retrieving data from an API
import json
from urllib.request import urlopen


# Function to get the weather forecast for Rochester, NY
def get_weather():

    # Open-Meteo API URL with Rochester coordinates
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=43.1566&longitude=-77.6088"
        "&current=temperature_2m,apparent_temperature,"
        "precipitation,weather_code"
        "&temperature_unit=fahrenheit"
        "&timezone=America%2FNew_York"
    )

    # Request and read the weather data
    with urlopen(url, timeout=15) as response:
        data = json.load(response)

    # Extract the current weather information
    current = data["current"]

    return {
        "location": "Rochester, NY",
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "precipitation": current["precipitation"],
        "weather_code": current["weather_code"]
    }
