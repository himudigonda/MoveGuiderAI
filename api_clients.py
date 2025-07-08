# api_clients.py
import requests
from typing import Dict, Optional, Any


def get_city_coordinates(city_name: str, api_key: str) -> Optional[Dict[str, float]]:
    """
    Fetches latitude and longitude for a given city name.
    Returns a dictionary with 'lat' and 'lon' or None if not found.
    """
    base_url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city_name,
        "limit": 1,
        "appid": api_key,
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()
        if data:
            return {"lat": data[0]["lat"], "lon": data[0]["lon"]}
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API request failed for coordinates: {e}")
        return None


def get_weather_data(lat: float, lon: float, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetches hourly weather data for the next 7 days using the One Call API.
    """
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    # In the get_weather_data function...
    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "current,minutely,alerts",  # REMOVED 'daily'
        "units": "metric",
        "appid": api_key,
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API request failed for weather data: {e}")
        return None
