# logic/performance.py
import pandas as pd
import numpy as np
from datetime import time


def model_energy_curve(wake_time: time, sleep_time: time) -> pd.DataFrame:
    """
    Models a user's energy/performance curve over 24 hours.
    (Moved from logic.py)
    """
    wake_hour = wake_time.hour + wake_time.minute / 60
    sleep_hour = sleep_time.hour + sleep_time.minute / 60

    if sleep_hour < wake_hour:
        sleep_hour += 24

    sleep_duration = sleep_hour - wake_hour
    hours_in_day = np.linspace(0, 24, 24 * 4)  # 15-minute intervals
    performance = np.zeros_like(hours_in_day)

    for i, hour in enumerate(hours_in_day):
        if wake_hour <= hour < sleep_hour:
            circadian_phase = (hour - wake_hour) / (sleep_duration) * np.pi
            circadian_effect = 0.8 * (np.sin(circadian_phase) + 0.1)
            dip_hour = 14.0
            dip_effect = -0.2 * np.exp(-((hour - dip_hour) ** 2) / 4)
            ultradian_phase = (hour - wake_hour) / 1.5 * 2 * np.pi
            ultradian_effect = 0.1 * np.sin(ultradian_phase)
            performance[i] = (circadian_effect + dip_effect + ultradian_effect) * 100

    performance = np.clip(performance, 5, 100)
    curve_df = pd.DataFrame({"Hour": hours_in_day, "Performance": performance})
    curve_df = curve_df.round(1)
    return curve_df
