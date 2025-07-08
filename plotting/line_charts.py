# plotting/line_charts.py
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import webcolors
from colorsys import rgb_to_hls, hls_to_rgb


def plot_combined_metric(
    df: pd.DataFrame, metric: str, city1: str, city2: str, annotations: dict
):
    """
    Creates a multi-trace plot with daily dashed lines and a solid average line.
    (Moved from plotting.py)
    """
    fig = go.Figure()
    city_colors = {city1: "red", city2: "green"}

    def get_color_gradient(base_color, n):
        r, g, b = webcolors.name_to_rgb(base_color)
        h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        lightness_gradient = np.linspace(l + 0.2, l - 0.1, n)
        return [
            f"rgb{tuple(int(x * 255) for x in hls_to_rgb(h, light, s))}"
            for light in np.clip(lightness_gradient, 0, 1)
        ]

    for city_name, base_color in city_colors.items():
        city_df = df[df["City"] == city_name]
        days = city_df["Day"].unique()
        color_palette = get_color_gradient(base_color, len(days))
        for i, day in enumerate(days):
            day_df = city_df[city_df["Day"] == day]
            fig.add_trace(
                go.Scatter(
                    x=day_df["Hour"],
                    y=day_df[metric],
                    mode="lines",
                    line=dict(color=color_palette[i], width=1.5, dash="dash"),
                    name=f"{city_name.split(',')[0]} {day}",
                    legendgroup=city_name,
                )
            )
        avg_df = city_df[["Hour", "Average"]].drop_duplicates().sort_values("Hour")
        fig.add_trace(
            go.Scatter(
                x=avg_df["Hour"],
                y=avg_df["Average"],
                mode="lines",
                line=dict(color=base_color, width=4),
                name=f"{city_name.split(',')[0]} Avg",
                legendgroup=city_name,
            )
        )

    fig.update_layout(
        title=f"Hourly {metric.split('(')[0].strip()}: {city2.split(',')[0]} (green) vs {city1.split(',')[0]} (red)",
        xaxis_title="Time of Day (AZ Time)",
        yaxis_title=metric,
        xaxis=dict(
            tickmode="array",
            tickvals=[0, 3, 6, 9, 12, 15, 18, 21, 24],
            ticktext=["12AM", "3AM", "6AM", "9AM", "12PM", "3PM", "6PM", "9PM", "12AM"],
        ),
        plot_bgcolor="white",
        margin=dict(b=100),
        legend_title_text="Forecast",
    )
    fig.update_layout(shapes=annotations["shapes"])
    for anno in annotations["annotations"]:
        fig.add_annotation(**anno)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray", range=[0, 24])
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    return fig
