# logic/weather_parser.py
import pandas as pd
import pytz
from datetime import datetime


def parse_weather_data(data: dict) -> pd.DataFrame:
    """
    Parses the hourly weather data from the WeatherAPI.com response.
    (Moved from logic.py)
    """
    all_hours = []
    for day in data["forecast"]["forecastday"]:
        all_hours.extend(day["hour"])

    df = pd.DataFrame(all_hours)
    timezone_str = data["location"]["tz_id"]

    df["dt"] = (
        pd.to_datetime(df["time_epoch"], unit="s")
        .dt.tz_localize("UTC")
        .dt.tz_convert(timezone_str)
    )

    sunrise_sunset_map = {
        day["date"]: {
            "sunrise": day["astro"]["sunrise"],
            "sunset": day["astro"]["sunset"],
        }
        for day in data["forecast"]["forecastday"]
    }

    def parse_astro_time(astro_time_str, date, tz):
        return tz.localize(
            datetime.strptime(f"{date} {astro_time_str}", "%Y-%m-%d %I:%M %p")
        )

    df["sunrise"] = df["dt"].apply(
        lambda x: parse_astro_time(
            sunrise_sunset_map[x.strftime("%Y-%m-%d")]["sunrise"],
            x.strftime("%Y-%m-%d"),
            pytz.timezone(timezone_str),
        )
    )
    df["sunset"] = df["dt"].apply(
        lambda x: parse_astro_time(
            sunrise_sunset_map[x.strftime("%Y-%m-%d")]["sunset"],
            x.strftime("%Y-%m-%d"),
            pytz.timezone(timezone_str),
        )
    )

    df = df[["dt", "temp_c", "humidity", "uv", "sunrise", "sunset"]]
    df = df.rename(
        columns={
            "dt": "Time",
            "temp_c": "Temperature (°C)",
            "humidity": "Humidity (%)",
            "uv": "UV Index",
        }
    )

    df.set_index("Time", inplace=True)
    return df
