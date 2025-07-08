# logic.py
import pandas as pd
import pytz
from datetime import datetime, time, timedelta
import numpy as np


def parse_weather_data(data: dict) -> pd.DataFrame:
    """
    REVISED: Parses the hourly weather data from the WeatherAPI.com response.
    """
    # The new JSON structure nests hourly data inside daily forecasts.
    # We need to extract and combine them.
    all_hours = []
    for day in data["forecast"]["forecastday"]:
        all_hours.extend(day["hour"])

    df = pd.DataFrame(all_hours)

    # Timezone is in a different location in the new JSON
    timezone_str = data["location"]["tz_id"]

    # "time_epoch" is the unix timestamp, "time" is a string version
    df["dt"] = (
        pd.to_datetime(df["time_epoch"], unit="s")
        .dt.tz_localize("UTC")
        .dt.tz_convert(timezone_str)
    )

    # Sunrise/Sunset are in the daily forecast, not hourly
    # We'll map the daily sunrise/sunset to each hour of that day.
    sunrise_sunset_map = {
        day["date"]: {
            "sunrise": day["astro"]["sunrise"],
            "sunset": day["astro"]["sunset"],
        }
        for day in data["forecast"]["forecastday"]
    }

    def parse_astro_time(astro_time_str, date, tz):
        # WeatherAPI sunrise/sunset is like "06:30 AM". We need to combine it with the date.
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

    # Select and rename columns to match what our plotting functions expect
    # Note: WeatherAPI uses 'temp_c' and 'uv'
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


# --- MODIFIED: Function to create a unified DataFrame for plotting ---
def create_unified_df(
    city1_df: pd.DataFrame,
    city1_name: str,
    city2_df: pd.DataFrame,
    city2_name: str,
    metric_col: str,
) -> pd.DataFrame:
    """
    Combines data, smooths it, and calculates daily averages.
    Normalizes all times to Arizona Time.
    """
    home_tz = pytz.timezone("America/Phoenix")

    def process_df(df, city_name):
        processed_df = df.copy()
        processed_df["City"] = city_name
        processed_df["Time_AZ"] = processed_df.index.tz_convert(home_tz)
        processed_df["Hour"] = (
            processed_df["Time_AZ"].dt.hour + processed_df["Time_AZ"].dt.minute / 60
        )
        processed_df["Day"] = processed_df["Time_AZ"].dt.strftime("%a %d")
        # --- NEW: Add a smoothed version of the metric using a rolling average ---
        smoothed_col_name = f"Smoothed_{metric_col}"
        processed_df[smoothed_col_name] = (
            processed_df[metric_col]
            .rolling(window=4, center=True, min_periods=1)
            .mean()
        )
        return processed_df

    # Combine data from both cities
    full_df = pd.concat(
        [process_df(city1_df, city1_name), process_df(city2_df, city2_name)]
    )

    # --- NEW: Calculate the daily average for each city ---
    avg_df = (
        full_df.groupby(["City", "Hour"])[f"Smoothed_{metric_col}"].mean().reset_index()
    )
    avg_df.rename(columns={f"Smoothed_{metric_col}": "Average"}, inplace=True)

    # Merge the average back into the main dataframe
    full_df = pd.merge(full_df, avg_df, on=["City", "Hour"])

    return full_df[["Hour", f"Smoothed_{metric_col}", "City", "Day", "Average"]].rename(
        columns={f"Smoothed_{metric_col}": metric_col}
    )


# --- MODIFIED: Function to get all annotations for the plots ---
def get_plot_annotations(
    city1_df: pd.DataFrame, city1_name: str, city2_df: pd.DataFrame, city2_name: str
) -> dict:
    """
    Generates a simplified background highlight for daylight hours and text annotations.
    All times are in Arizona Time (0-24 hours).
    """
    home_tz = pytz.timezone("America/Phoenix")

    def to_az_hour(dt_aware):
        return (
            dt_aware.astimezone(home_tz).hour + dt_aware.astimezone(home_tz).minute / 60
        )

    # --- NEW: Simplified Daylight Highlight ---
    # We'll use City 1 (the 'red' city) as the reference for the daylight band.
    # We take the sunrise/sunset from the first day of its forecast.
    sunrise_ref = city1_df["sunrise"].iloc[0]
    sunset_ref = city1_df["sunset"].iloc[0]

    shapes = [
        # Single, yellow highlight for daylight hours of City 1
        dict(
            type="rect",
            xref="x",
            yref="paper",
            x0=to_az_hour(sunrise_ref),
            y0=0,
            x1=to_az_hour(sunset_ref),
            y1=1,
            fillcolor="rgba(255, 224, 130, 0.3)",  # Soft yellow/gold color
            layer="below",
            line_width=0,
        ),
    ]

    # --- UNCHANGED: The text annotations for exact sun times are still useful ---
    text_annotations = []
    sun_times = [
        {
            "city": city1_name,
            "char": "T",
            "color": "red",
            "sunrise": city1_df["sunrise"].iloc[0],
            "sunset": city1_df["sunset"].iloc[0],
        },
        {
            "city": city2_name,
            "char": "D",
            "color": "green",
            "sunrise": city2_df["sunrise"].iloc[0],
            "sunset": city2_df["sunset"].iloc[0],
        },
    ]
    for item in sun_times:
        # Sunrise annotation
        text_annotations.append(
            dict(
                x=to_az_hour(item["sunrise"]),
                y=-0.1,
                xref="x",
                yref="paper",
                text=f"🌄{item['char']}",
                showarrow=False,
                font=dict(color=item["color"], size=14),
            )
        )
        # Sunset annotation
        text_annotations.append(
            dict(
                x=to_az_hour(item["sunset"]),
                y=-0.1,
                xref="x",
                yref="paper",
                text=f"🌇{item['char']}",
                showarrow=False,
                font=dict(color=item["color"], size=14),
            )
        )

    return {"shapes": shapes, "annotations": text_annotations}


def model_energy_curve(wake_time: time, sleep_time: time) -> pd.DataFrame:
    """
    Models a user's energy/performance curve over 24 hours.
    """
    # Convert time objects to hours (float)
    wake_hour = wake_time.hour + wake_time.minute / 60
    sleep_hour = sleep_time.hour + sleep_time.minute / 60

    # If bedtime is on the next day (e.g., wake at 6, sleep at 1 AM)
    if sleep_hour < wake_hour:
        sleep_hour += 24

    sleep_duration = sleep_hour - wake_hour

    hours_in_day = np.linspace(0, 24, 24 * 4)  # 15-minute intervals
    performance = np.zeros_like(hours_in_day)

    # Simple model: a sine wave that peaks mid-day + smaller ultradian rhythms
    for i, hour in enumerate(hours_in_day):
        if wake_hour <= hour < sleep_hour:
            # 1. Circadian Rhythm (24-hour cycle)
            # This sine wave starts at a low point at wake-up and peaks in the afternoon
            circadian_phase = (hour - wake_hour) / (sleep_duration) * np.pi
            circadian_effect = 0.8 * (np.sin(circadian_phase) + 0.1)  # Base performance
            # 2. Post-lunch dip (a negative gaussian curve around 2 PM)
            dip_hour = 14.0
            dip_effect = -0.2 * np.exp(-((hour - dip_hour) ** 2) / 4)
            # 3. Ultradian Rhythm (~90-minute cycles of focus)
            ultradian_phase = (hour - wake_hour) / 1.5 * 2 * np.pi
            ultradian_effect = 0.1 * np.sin(ultradian_phase)
            performance[i] = (circadian_effect + dip_effect + ultradian_effect) * 100
    # Clip values to be between 0 and 100
    performance = np.clip(performance, 5, 100)
    # Create DataFrame
    curve_df = pd.DataFrame({"Hour": hours_in_day, "Performance": performance})
    curve_df = curve_df.round(1)
    return curve_df
