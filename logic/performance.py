# logic/performance.py
import pandas as pd
import numpy as np
from datetime import time


def model_energy_curve(
    wake_time: time, sleep_time: time, chronotype: str = "Default"
) -> pd.DataFrame:
    """
    UPDATED: Models a user's energy/performance curve over 24 hours,
    now adjusting for different chronotypes.
    """
    wake_hour = wake_time.hour + wake_time.minute / 60
    sleep_hour = sleep_time.hour + sleep_time.minute / 60

    if sleep_hour < wake_hour:
        sleep_hour += 24

    sleep_duration = sleep_hour - wake_hour
    hours_in_day = np.linspace(0, 24, 24 * 4)  # 15-minute intervals

    # --- Chronotype Adjustments ---
    # These are offsets to shift the peak performance and afternoon dip.
    if chronotype == "Morning Lark":
        peak_offset = -1.5  # Peak energy is 1.5 hours earlier
        dip_offset = -1.0  # Afternoon dip is 1 hour earlier
    elif chronotype == "Night Owl":
        peak_offset = 2.0  # Peak energy is 2 hours later
        dip_offset = 1.5  # Afternoon dip is 1.5 hours later
    else:  # Default
        peak_offset = 0
        dip_offset = 0

    performance = np.zeros_like(hours_in_day)

    # The primary peak is roughly a quarter way through the waking day
    primary_peak_hour = wake_hour + (sleep_duration / 4) + peak_offset

    for i, hour in enumerate(hours_in_day):
        if wake_hour <= hour < sleep_hour:
            # Shifted sine wave for primary energy
            circadian_phase = (hour - primary_peak_hour) / (sleep_duration / 2) * np.pi
            circadian_effect = 0.8 * (np.cos(circadian_phase) + 0.1)

            # Shifted afternoon dip
            dip_hour = 14.0 + dip_offset
            dip_effect = -0.2 * np.exp(-((hour - dip_hour) ** 2) / 4)

            # Ultradian cycles remain the same
            ultradian_phase = (hour - wake_hour) / 1.5 * 2 * np.pi
            ultradian_effect = 0.1 * np.sin(ultradian_phase)

            performance[i] = (circadian_effect + dip_effect + ultradian_effect) * 100

    performance = np.clip(performance, 5, 100)
    curve_df = pd.DataFrame({"Hour": hours_in_day, "Performance": performance})
    return curve_df.round(1)
