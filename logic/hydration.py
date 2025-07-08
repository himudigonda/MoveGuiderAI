# logic/hydration.py
import pandas as pd


def calculate_hydration_needs(
    city_df: pd.DataFrame, user_weight_kg: float
) -> pd.DataFrame:
    """
    Computes hourly and cumulative water intake recommendations.
    (Moved from logic.py)
    """
    df = city_df[["Temperature (°C)", "Humidity (%)"]].copy()

    base_hourly_intake_ml = (user_weight_kg * 35) / 16
    temp_extra = df["Temperature (°C)"].apply(lambda t: max(0, (t - 25) / 5) * 150)
    humidity_extra = df["Humidity (%)"].apply(lambda h: 50 if h > 60 else 0)

    df["Recommended Intake (ml)"] = base_hourly_intake_ml + temp_extra + humidity_extra
    df["Cumulative Intake (ml)"] = df["Recommended Intake (ml)"].cumsum()

    return df.iloc[:24]
