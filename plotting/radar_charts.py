# plotting/radar_charts.py
import plotly.graph_objects as go
import pandas as pd


def plot_comfort_wheel(df: pd.DataFrame, city1_name: str, city2_name: str):
    """
    Creates a radar chart comparing two cities against an ideal range.
    (Moved from plotting.py)
    """
    fig = go.Figure()
    ideal_df = (
        df[df["City"] == "Ideal"]
        .groupby("Metric")["Value"]
        .agg(["min", "max"])
        .reset_index()
    )
    metric_order = ideal_df["Metric"]
    fig.add_trace(
        go.Scatterpolar(
            r=list(ideal_df["max"]) + list(ideal_df["max"])[::1],
            theta=list(ideal_df["Metric"]) + list(ideal_df["Metric"])[::1],
            fill="toself",
            fillcolor="rgba(44, 160, 44, 0.2)",
            line=dict(color="rgba(44, 160, 44, 0.4)"),
            name="Ideal Range",
        )
    )

    city_plot_config = {
        city1_name: {"color": "red", "fill": "rgba(255, 87, 87, 0.4)"},
        city2_name: {"color": "green", "fill": "rgba(0, 128, 0, 0.4)"},
    }

    for city, config in city_plot_config.items():
        city_df = (
            df[df["City"] == city].set_index("Metric").loc[metric_order].reset_index()
        )
        fig.add_trace(
            go.Scatterpolar(
                r=list(city_df["Value"]) + list(city_df["Value"])[::1],
                theta=list(city_df["Metric"]) + list(city_df["Metric"])[::1],
                fill="toself",
                fillcolor=config["fill"],
                line=dict(color=config["color"]),
                name=f"Current: {city.split(',')[0]}",
            )
        )

    max_val = df[df["Category"] == "Current"]["Value"].max()
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(max_val, 30) * 1.1])),
        showlegend=True,
        title=f"Polar Comfort Wheel: {city1_name.split(',')[0]} (Red) vs. {city2_name.split(',')[0]} (Green)",
        height=500,
    )
    return fig
