# plotting/gantt.py
import plotly.figure_factory as ff
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, time, date

# --- A constant to match the logic file, ensuring axis ranges are correct ---
REFERENCE_DATE = date(2024, 1, 1)


def plot_gantt_schedule(
    gantt_df: pd.DataFrame, background_shapes: List[Dict[str, Any]] = None
):
    """
    CORRECTED: Creates a 24-HOUR Gantt chart with environmental highlights.
    Fixes the color mapping and indexing issue.
    """
    if gantt_df.empty:
        return None

    city_name = gantt_df["Resource"].iloc[0]

    # The color dictionary keys MUST match the values in the 'Resource' column.
    # This dictionary might seem simple, but it's what Plotly needs.
    colors = {
        city_name: (
            "rgb(255, 87, 87)" if "tempe" in city_name.lower() else "rgb(0, 128, 0)"
        )
    }

    # --- THE FIX IS HERE ---
    fig = ff.create_gantt(
        gantt_df,
        colors=colors,
        index_col="Resource",  # Index by the Resource (e.g., 'Tempe') for coloring.
        show_colorbar=False,
        group_tasks=True,  # This is CRUCIAL. It tells Plotly to group tasks by Resource.
        title=f"Daily Schedule for {city_name}",
    )

    # Define the 24-hour range for the x-axis
    x_axis_start = datetime.combine(REFERENCE_DATE, time(0, 0)).replace(
        tzinfo=gantt_df["Start"].iloc[0].tzinfo
    )
    x_axis_end = datetime.combine(REFERENCE_DATE, time(23, 59)).replace(
        tzinfo=gantt_df["Start"].iloc[0].tzinfo
    )

    layout_updates = {
        "xaxis_title": "Time of Day (Local Time)",
        "yaxis_title": "",  # Cleaner look
        "xaxis": {
            "type": "date",
            "tickformat": "%I %p",
            "range": [x_axis_start, x_axis_end],
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "dtick": 7200000,  # Two hours in milliseconds for cleaner ticks
        },
        # Reverse y-axis so morning tasks are at the top
        "yaxis": {"autorange": "reversed"},
    }

    if background_shapes:
        layout_updates["shapes"] = background_shapes

    fig.update_layout(**layout_updates)

    return fig
