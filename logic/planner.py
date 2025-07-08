# logic/planner.py
import pandas as pd
import pytz
from datetime import datetime, date, timedelta
from logic.utils import to_az_hour  # We will create this helper function


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
    (Moved from logic.py)
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
        smoothed_col_name = f"Smoothed_{metric_col}"
        processed_df[smoothed_col_name] = (
            processed_df[metric_col]
            .rolling(window=4, center=True, min_periods=1)
            .mean()
        )
        return processed_df

    full_df = pd.concat(
        [process_df(city1_df, city1_name), process_df(city2_df, city2_name)]
    )
    avg_df = (
        full_df.groupby(["City", "Hour"])[f"Smoothed_{metric_col}"].mean().reset_index()
    )
    avg_df.rename(columns={f"Smoothed_{metric_col}": "Average"}, inplace=True)
    full_df = pd.merge(full_df, avg_df, on=["City", "Hour"])

    return full_df[["Hour", f"Smoothed_{metric_col}", "City", "Day", "Average"]].rename(
        columns={f"Smoothed_{metric_col}": metric_col}
    )


def get_plot_annotations(
    city1_df: pd.DataFrame, city1_name: str, city2_df: pd.DataFrame, city2_name: str
) -> dict:
    """
    Generates background highlight and text annotations.
    (Moved from logic.py)
    """
    sunrise_ref = city1_df["sunrise"].iloc[0]
    sunset_ref = city1_df["sunset"].iloc[0]

    shapes = [
        dict(
            type="rect",
            xref="x",
            yref="paper",
            x0=to_az_hour(sunrise_ref),
            y0=0,
            x1=to_az_hour(sunset_ref),
            y1=1,
            fillcolor="rgba(255, 224, 130, 0.3)",
            layer="below",
            line_width=0,
        ),
    ]

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


def prepare_comfort_wheel_data(
    city1_df: pd.DataFrame, city1_name: str, city2_df: pd.DataFrame, city2_name: str
) -> pd.DataFrame:
    """
    Prepares data for a dual-city Polar Comfort Wheel.
    (Moved from logic.py)
    """
    ideal_ranges = {
        "Temperature (°C)": [20, 24],
        "Humidity (%)": [40, 60],
        "UV Index": [0, 2],
    }
    all_data = []

    # Process Cities
    for city_name, city_df in [(city1_name, city1_df), (city2_name, city2_df)]:
        current_metrics = city_df.iloc[0]
        for metric, _ in ideal_ranges.items():
            all_data.append(
                {
                    "Metric": metric,
                    "Value": current_metrics[metric],
                    "City": city_name,
                    "Category": "Current",
                }
            )

    # Add Ideal Range
    for metric, ideal_range in ideal_ranges.items():
        all_data.extend(
            [
                {
                    "Metric": metric,
                    "Value": ideal_range[0],
                    "City": "Ideal",
                    "Category": "Ideal",
                },
                {
                    "Metric": metric,
                    "Value": ideal_range[1],
                    "City": "Ideal",
                    "Category": "Ideal",
                },
            ]
        )

    return pd.DataFrame(all_data)


def build_gantt_df(
    user_routine: list,
    city1_df: pd.DataFrame,
    city1_name: str,
    city2_df: pd.DataFrame,
    city2_name: str,
) -> pd.DataFrame:
    """
    Creates a DataFrame for the Gantt chart, showing the user's routine
    time-shifted for two different cities.
    """
    gantt_data = []
    home_tz = pytz.timezone("America/Phoenix")

    # Get the local timezone from the weather data's index
    tz1 = city1_df.index.tz
    tz2 = city2_df.index.tz

    # Use today's date as a reference to create datetime objects
    today = date.today()

    for task_item in user_routine:
        # Combine date and time string to create a naive datetime
        start_time_naive = datetime.strptime(task_item["start"], "%H:%M").time()
        end_time_naive = datetime.strptime(task_item["end"], "%H:%M").time()

        # Create timezone-aware datetime objects in the user's "home" timezone (AZ)
        start_home_aware = home_tz.localize(datetime.combine(today, start_time_naive))
        end_home_aware = home_tz.localize(datetime.combine(today, end_time_naive))

        # --- Time-shift for City 1 ---
        start_city1 = start_home_aware.astimezone(tz1)
        end_city1 = end_home_aware.astimezone(tz1)
        gantt_data.append(
            dict(
                Task=task_item["task"],
                Start=start_city1,
                Finish=end_city1,
                Resource=city1_name.split(",")[0],
            )
        )

        # --- Time-shift for City 2 ---
        start_city2 = start_home_aware.astimezone(tz2)
        end_city2 = end_home_aware.astimezone(tz2)
        gantt_data.append(
            dict(
                Task=task_item["task"],
                Start=start_city2,
                Finish=end_city2,
                Resource=city2_name.split(",")[0],
            )
        )

    if not gantt_data:
        return pd.DataFrame()

    return pd.DataFrame(gantt_data)


def get_gantt_background_annotations(city_df: pd.DataFrame) -> list:
    """
    Scans the forecast to generate background highlights for
    'Optimal Comfort' (green) and 'High Heat/UV' (red) zones for the Gantt chart.
    """
    shapes = []
    HEAT_TEMP_THRESHOLD = 30
    HEAT_UV_THRESHOLD = 7
    COMFORT_TEMP_RANGE = (18, 25)
    COMFORT_UV_THRESHOLD = 4
    for idx, row in city_df.iterrows():
        import pandas as pd
        from datetime import timedelta, datetime, date

        # Only try to use idx if it's a datetime/date or string/number
        if isinstance(idx, (pd.Timestamp, datetime, date)):
            x0 = idx
            x1 = idx + timedelta(hours=1)
        elif isinstance(idx, (str, int, float)):
            try:
                x0 = pd.Timestamp(idx)
                x1 = x0 + timedelta(hours=1)
            except Exception:
                continue
        else:
            continue
        # High Heat/UV Warning Zone (Red)
        if (
            row.get("Temperature (°C)", 0) > HEAT_TEMP_THRESHOLD
            or row.get("UV Index", 0) > HEAT_UV_THRESHOLD
        ):
            shapes.append(
                dict(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0=x0,
                    y0=0,
                    x1=x1,
                    y1=1,
                    fillcolor="rgba(255, 82, 82, 0.2)",
                    layer="below",
                    line_width=0,
                )
            )
        # Optimal Comfort Zone (Green)
        if (
            COMFORT_TEMP_RANGE[0]
            <= row.get("Temperature (°C)", 0)
            <= COMFORT_TEMP_RANGE[1]
        ) and (row.get("UV Index", 0) < COMFORT_UV_THRESHOLD):
            shapes.append(
                dict(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0=x0,
                    y0=0,
                    x1=x1,
                    y1=1,
                    fillcolor="rgba(119, 221, 119, 0.2)",
                    layer="below",
                    line_width=0,
                )
            )
    return shapes


def find_optimal_workout_slots(city_df, user_routine, workout_duration_min, top_n=5):
    """
    Finds the best time slots for a workout based on weather and free time.
    """
    busy_slots = []
    home_tz = pytz.timezone("America/Phoenix")
    city_tz = getattr(city_df.index, "tz", None)
    today = date.today()
    for task in user_routine:
        try:
            start_home = home_tz.localize(
                datetime.combine(
                    today, datetime.strptime(task["start"], "%H:%M").time()
                )
            )
            end_home = home_tz.localize(
                datetime.combine(today, datetime.strptime(task["end"], "%H:%M").time())
            )
            if city_tz:
                busy_slots.append(
                    (start_home.astimezone(city_tz), end_home.astimezone(city_tz))
                )
        except Exception:
            continue
    possible_slots = []
    start_time = city_df.index.min()
    end_time = city_df.index.max()
    current_time = start_time
    while current_time + timedelta(minutes=workout_duration_min) <= end_time:
        workout_window_end = current_time + timedelta(minutes=workout_duration_min)
        is_free = True
        for busy_start, busy_end in busy_slots:
            if (
                current_time.time() < busy_end.time()
                and workout_window_end.time() > busy_start.time()
            ):
                is_free = False
                break
        if is_free:
            window_df = city_df.loc[current_time:workout_window_end]
            if not window_df.empty:
                avg_temp = window_df["Temperature (°C)"].mean()
                avg_humidity = window_df["Humidity (%)"].mean()
                max_uv = window_df["UV Index"].max()
                score = 0
                score += max(0, avg_temp - 22) * 2
                score += min(0, avg_temp - 15) * -1
                score += max(0, avg_humidity - 60) * 0.5
                score += max_uv * 5
                sunrise = (
                    window_df["sunrise"].iloc[0] if "sunrise" in window_df else None
                )
                sunset = window_df["sunset"].iloc[0] if "sunset" in window_df else None
                if (
                    sunrise
                    and sunset
                    and current_time >= sunrise
                    and workout_window_end <= sunset
                ):
                    score -= 10
                else:
                    score += 5
                possible_slots.append(
                    {
                        "start_time": current_time,
                        "score": score,
                        "details": f"Temp: {avg_temp:.1f}°C, Hum: {avg_humidity:.1f}%, UV: {max_uv}",
                    }
                )
        current_time += timedelta(minutes=30)
    sorted_slots = sorted(possible_slots, key=lambda x: x["score"])
    return sorted_slots[:top_n]
