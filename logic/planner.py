# logic/planner.py
import pandas as pd
import pytz
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any

from logic.utils import to_az_hour  # We will create this helper function

# --- A constant to normalize all daily tasks to a single reference date ---
REFERENCE_DATE = date(2024, 1, 1)


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


def _ensure_datetime_index(df):
    idx = df.index
    if not isinstance(idx, pd.DatetimeIndex):
        try:
            idx = pd.to_datetime(idx)
        except Exception:
            raise ValueError(
                "DataFrame index must be or convertible to DatetimeIndex for time-based plotting."
            )
    return idx


def build_gantt_df(
    user_routine: list,
    city1_df: pd.DataFrame,
    city1_name: str,
    city2_df: pd.DataFrame,
    city2_name: str,
) -> pd.DataFrame:
    """
    REFACTORED: Creates a DataFrame for a 24-HOUR Gantt chart.
    All tasks are normalized to a single reference date for a "typical day" view.
    """
    gantt_data = []
    home_tz = pytz.timezone("America/Phoenix")

    city1_dtidx = _ensure_datetime_index(city1_df)
    city2_dtidx = _ensure_datetime_index(city2_df)
    tz1 = (
        city1_dtidx.tz
        if hasattr(city1_dtidx, "tz") and city1_dtidx.tz is not None
        else None
    )
    tz2 = (
        city2_dtidx.tz
        if hasattr(city2_dtidx, "tz") and city2_dtidx.tz is not None
        else None
    )
    if tz1 is None:
        tz1 = city1_dtidx[0].tzinfo if hasattr(city1_dtidx[0], "tzinfo") else None
    if tz2 is None:
        tz2 = city2_dtidx[0].tzinfo if hasattr(city2_dtidx[0], "tzinfo") else None

    for task_item in user_routine:
        try:
            start_time_naive = datetime.strptime(task_item["start"], "%H:%M").time()
            end_time_naive = datetime.strptime(task_item["end"], "%H:%M").time()

            start_home_aware = home_tz.localize(
                datetime.combine(REFERENCE_DATE, start_time_naive)
            )
            end_home_aware = home_tz.localize(
                datetime.combine(REFERENCE_DATE, end_time_naive)
            )

            # Time-shift for City 1 and replace date with REFERENCE_DATE
            start_city1 = start_home_aware.astimezone(tz1) if tz1 else start_home_aware
            start_city1 = start_city1.replace(
                year=REFERENCE_DATE.year,
                month=REFERENCE_DATE.month,
                day=REFERENCE_DATE.day,
            )
            end_city1 = end_home_aware.astimezone(tz1) if tz1 else end_home_aware
            end_city1 = end_city1.replace(
                year=REFERENCE_DATE.year,
                month=REFERENCE_DATE.month,
                day=REFERENCE_DATE.day,
            )
            gantt_data.append(
                dict(
                    Task=task_item["task"],
                    Start=start_city1,
                    Finish=end_city1,
                    Resource=city1_name.split(",")[0],
                )
            )

            # Time-shift for City 2 and replace date with REFERENCE_DATE
            start_city2 = start_home_aware.astimezone(tz2) if tz2 else start_home_aware
            start_city2 = start_city2.replace(
                year=REFERENCE_DATE.year,
                month=REFERENCE_DATE.month,
                day=REFERENCE_DATE.day,
            )
            end_city2 = end_home_aware.astimezone(tz2) if tz2 else end_home_aware
            end_city2 = end_city2.replace(
                year=REFERENCE_DATE.year,
                month=REFERENCE_DATE.month,
                day=REFERENCE_DATE.day,
            )
            gantt_data.append(
                dict(
                    Task=task_item["task"],
                    Start=start_city2,
                    Finish=end_city2,
                    Resource=city2_name.split(",")[0],
                )
            )
        except (ValueError, TypeError):
            continue  # Skip malformed routine items

    return pd.DataFrame(gantt_data) if gantt_data else pd.DataFrame()


def get_gantt_background_annotations(city_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    REFACTORED: Scans the FIRST 24 HOURS of the forecast to generate background highlights
    for a single 24-hour Gantt chart view.
    """
    shapes = []
    dtidx = _ensure_datetime_index(city_df)
    first_day_df = city_df.iloc[:24]

    HEAT_TEMP_THRESHOLD, HEAT_UV_THRESHOLD = 30, 7
    COMFORT_TEMP_RANGE, COMFORT_UV_THRESHOLD = (18, 25), 4

    for local_time, row in first_day_df.iterrows():
        # local_time is the index, which should be a Timestamp
        if not isinstance(local_time, pd.Timestamp):
            continue
        x0 = datetime.combine(REFERENCE_DATE, local_time.time()).replace(
            tzinfo=local_time.tzinfo
        )
        x1 = x0 + timedelta(hours=1)

        if (
            row["Temperature (°C)"] > HEAT_TEMP_THRESHOLD
            or row["UV Index"] > HEAT_UV_THRESHOLD
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
        elif (
            COMFORT_TEMP_RANGE[0] <= row["Temperature (°C)"] <= COMFORT_TEMP_RANGE[1]
            and row["UV Index"] < COMFORT_UV_THRESHOLD
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
                    fillcolor="rgba(119, 221, 119, 0.2)",
                    layer="below",
                    line_width=0,
                )
            )

    return shapes


def find_daily_best_workout(
    city_df: pd.DataFrame, user_routine: list, workout_duration_min: int
) -> List[Dict[str, Any]]:
    """
    NEW LOGIC: Finds the single best workout slot for each of the next 3 days.
    """
    daily_bests = []
    dtidx = _ensure_datetime_index(city_df)
    if not hasattr(dtidx, "normalize"):
        raise ValueError(
            "DataFrame index must be a DatetimeIndex for workout recommendation."
        )
    unique_days = dtidx.normalize().unique()

    for day_index, day_date in enumerate(unique_days[:3]):  # Limit to first 3 days
        # Select rows for this day
        day_df = city_df[dtidx.normalize() == day_date]
        if day_df.empty:
            continue

        # Create a list of busy time intervals for the day
        busy_times = []
        for task in user_routine:
            try:
                busy_times.append(
                    (
                        datetime.strptime(task["start"], "%H:%M").time(),
                        datetime.strptime(task["end"], "%H:%M").time(),
                    )
                )
            except (ValueError, TypeError):
                continue

        possible_slots = []
        current_time = day_df.index.min()
        day_end_time = day_df.index.max()

        while current_time + timedelta(minutes=workout_duration_min) <= day_end_time:
            workout_end = current_time + timedelta(minutes=workout_duration_min)
            # Check if free
            is_free = all(
                current_time.time() >= busy_end or workout_end.time() <= busy_start
                for busy_start, busy_end in busy_times
            )
            if is_free:
                window_df = day_df.loc[current_time:workout_end]
                if not window_df.empty:
                    avg_temp = window_df["Temperature (°C)"].mean()
                    avg_humidity = window_df["Humidity (%)"].mean()
                    max_uv = window_df["UV Index"].max()
                    # Scoring (lower is better)
                    score = (
                        max(0, avg_temp - 22) * 2
                        + min(0, avg_temp - 15) * -1
                        + max(0, avg_humidity - 60) * 0.5
                        + max_uv * 5
                    )
                    if not (
                        current_time >= window_df["sunrise"].iloc[0]
                        and workout_end <= window_df["sunset"].iloc[0]
                    ):
                        score += 5  # Penalty for darkness
                    else:
                        score -= 10  # Bonus for daylight
                    possible_slots.append(
                        {
                            "start_time": current_time,
                            "score": score,
                            "details": f"Temp: {avg_temp:.1f}°C, Hum: {avg_humidity:.1f}%, UV: {max_uv}",
                        }
                    )
            current_time += timedelta(minutes=30)
        if possible_slots:
            best_slot = min(possible_slots, key=lambda x: x["score"])
            day_label = (
                "Today"
                if day_index == 0
                else (
                    "Tomorrow"
                    if day_index == 1
                    else best_slot["start_time"].strftime("%A")
                )
            )
            best_slot["day_label"] = day_label
            daily_bests.append(best_slot)
    return daily_bests


# (Other functions like create_unified_df remain unchanged but are not shown for brevity)
