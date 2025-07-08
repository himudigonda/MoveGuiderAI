# logic.py
import pandas as pd
from typing import Dict, Any
import pytz
from datetime import datetime, time, timedelta


def parse_weather_data(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Parses the hourly weather data from the API response into a pandas DataFrame.
    """
    hourly_data = data["hourly"]
    df = pd.DataFrame(hourly_data)
    timezone_str = data["timezone"]
    df["dt"] = (
        pd.to_datetime(df["dt"], unit="s")
        .dt.tz_localize("UTC")
        .dt.tz_convert(timezone_str)
    )

    # --- NEW: Extract sunrise for today ---
    # We also need daily data to get sunrise/sunset
    daily_data = data["daily"][0]  # Today's data
    df["sunrise"] = (
        pd.to_datetime(daily_data["sunrise"], unit="s")
        .dt.tz_localize("UTC")
        .dt.tz_convert(timezone_str)
    )
    df["sunset"] = (
        pd.to_datetime(daily_data["sunset"], unit="s")
        .dt.tz_localize("UTC")
        .dt.tz_convert(timezone_str)
    )

    df = df[["dt", "temp", "humidity", "uvi", "sunrise", "sunset"]]
    df = df.rename(
        columns={
            "dt": "Time",
            "temp": "Temperature (°C)",
            "humidity": "Humidity (%)",
            "uvi": "UV Index",
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
