# api_clients.py
import requests
from typing import Dict, Optional, Any


def resolve_latlon_nominatim(city_name: str) -> Optional[Dict[str, float]]:
    """
    Resolves a city name to latitude and longitude using Nominatim.
    This function is perfect and remains unchanged.
    """
    if not city_name:
        return None
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "MoveGuiderAI/1.0"}

    print(f"[INFO] Resolving coordinates for '{city_name}' via Nominatim...")
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f"[SUCCESS] Resolved '{city_name}' to Lat: {lat}, Lon: {lon}")
            return {"lat": lat, "lon": lon}
        else:
            print(f"[WARN] Nominatim could not find coordinates for '{city_name}'.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Nominatim API call failed: {e}")
        return None


def get_weather_data_from_weatherapi(
    lat: float, lon: float, api_key: str
) -> Optional[Dict[str, Any]]:
    """
    NEW: Fetches weather data from WeatherAPI.com.
    This replaces the old OpenWeatherMap function.
    """
    base_url = "http://api.weatherapi.com/v1/forecast.json"
    # Format lat/lon as a string for the 'q' parameter
    lat_lon_str = f"{lat},{lon}"

    params = {
        "key": api_key,
        "q": lat_lon_str,
        "days": 7,  # We need a 7-day forecast
        "aqi": "no",
        "alerts": "no",
    }

    print(f"[INFO] Calling WeatherAPI.com for forecast at {lat_lon_str}...")
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        print(f"[SUCCESS] WeatherAPI.com call successful.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] WeatherAPI.com call failed: {e}")
        return None
