# plotting/gantt.py
import plotly.figure_factory as ff
import pandas as pd


def plot_gantt_schedule(
    gantt_df: pd.DataFrame,
    city1_name: str,
    city2_name: str,
    background_shapes: list | None = None,
):
    """
    Creates an interactive Gantt chart with environmental background highlights.
    """
    if gantt_df.empty:
        return None  # Return None if there's no data to plot

    # Define colors for the chart
    city_colors = {
        city1_name.split(",")[0]: "rgb(255, 87, 87)",  # Red
        city2_name.split(",")[0]: "rgb(0, 128, 0)",  # Green
    }

    # Create the Gantt chart
    fig = ff.create_gantt(
        gantt_df,
        colors=city_colors,
        index_col="Resource",
        show_colorbar=True,
        group_tasks=True,
        title="Your Daily Routine: Environmentally-Aware Timeline",
    )

    # Improve layout
    layout_updates = {
        "xaxis_title": "Time of Day (Local Time for Each City)",
        "yaxis_title": "Tasks",
        "xaxis": {
            "type": "date",
            "tickformat": "%I:%M %p",  # Format as 12-hour time with AM/PM
            "rangebreaks": [
                dict(bounds=[23, 6], pattern="hour"),  # Hide overnight hours
            ],
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "gridwidth": 1,
            "dtick": 3600000,
        },
    }
    if background_shapes:
        layout_updates["shapes"] = background_shapes
    fig.update_layout(**layout_updates)

    return fig
