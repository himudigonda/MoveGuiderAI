# plotting.py
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd


def plot_weather_metrics(df: pd.DataFrame, city_name: str):
    """
    Generates an interactive Plotly line chart for weather metrics.
    """
    fig = px.line(
        df,
        y=["Temperature (°C)", "Humidity (%)", "UV Index"],
        title=f"7-Day Hourly Forecast for {city_name}",
        labels={"value": "Value", "variable": "Metric"},
        color_discrete_map={
            "Temperature (°C)": "#FF5733",
            "Humidity (%)": "#33C4FF",
            "UV Index": "#F1C40F",
        },
    )
    fig.update_layout(
        legend_title_text="Metrics", xaxis_title="Date and Time", yaxis_title="Values"
    )
    return fig


def plot_gantt_chart(df: pd.DataFrame, city_name: str):
    """
    Creates a Gantt chart for the daily routine.
    """
    df["Start"] = df["Start"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["Finish"] = df["Finish"].dt.strftime("%Y-%m-%d %H:%M:%S")

    colors = {
        "Work": "rgb(0, 114, 255)",
        "Personal": "rgb(255, 107, 107)",
        "Health": "rgb(44, 160, 44)",
    }

    fig = ff.create_gantt(
        df,
        colors=colors,
        index_col="Resource",
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        title=f"Daily Routine in {city_name} (Local Time)",
    )

    fig.update_layout(xaxis_title="Time of Day")
    return fig
