# logic.py
import pandas as pd
from typing import Dict, Any
import pytz
from datetime import datetime, time, timedelta
import numpy as np


def parse_weather_data(data: Dict[str, Any]) -> pd.DataFrame:
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


def create_routine_df(city_df: pd.DataFrame, city_name: str) -> pd.DataFrame:
    """
    Generates a DataFrame for the daily routine Gantt chart.
    """
    # --- Timezone setup ---
    home_tz_str = "America/Phoenix"
    home_tz = pytz.timezone(home_tz_str)

    # Get the target city's timezone from the DataFrame's index
    city_tz = city_df.index.tz

    # Get today's date in the context of the target city
    today_local = datetime.now(city_tz).date()

    # --- Define tasks ---
    tasks = []

    # 1. Work Block (9-5 Arizona Time)
    work_start_home = home_tz.localize(datetime.combine(today_local, time(9, 0)))
    work_end_home = home_tz.localize(datetime.combine(today_local, time(17, 0)))

    # Convert to the city's local time
    work_start_local = work_start_home.astimezone(city_tz)
    work_end_local = work_end_home.astimezone(city_tz)

    tasks.append(
        dict(
            Task="Work", Start=work_start_local, Finish=work_end_local, Resource="Work"
        )
    )

    # 2. Meal Times (local to the city)
    meal_times = [time(8, 0), time(12, 0), time(19, 0)]
    meal_labels = ["Breakfast", "Lunch", "Dinner"]
    for meal_time, label in zip(meal_times, meal_labels):
        start = city_tz.localize(datetime.combine(today_local, meal_time))
        tasks.append(
            dict(
                Task=label,
                Start=start,
                Finish=start + timedelta(hours=1),
                Resource="Personal",
            )
        )

    # 3. Workout Window (based on local sunrise)
    sunrise_local = city_df["sunrise"].iloc[0]  # Get today's sunrise
    workout_start = sunrise_local + timedelta(minutes=15)
    workout_end = sunrise_local + timedelta(minutes=90)
    tasks.append(
        dict(Task="Workout", Start=workout_start, Finish=workout_end, Resource="Health")
    )

    # Create DataFrame
    routine_df = pd.DataFrame(tasks)
    return routine_df


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
