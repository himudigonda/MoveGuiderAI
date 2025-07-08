# plotting.py
import plotly.express as px
import pandas as pd
import numpy as np


def plot_combined_metric(
    df: pd.DataFrame, metric: str, city1: str, city2: str, annotations: dict
):
    """
    Creates a single, combined, multi-layered chart for a given metric.
    """
    city_colors = {city1: "red", city2: "green"}
    day_list = df["Day"].unique()

    def get_color_gradient(base_color, n):
        from colorsys import rgb_to_hls, hls_to_rgb
        import webcolors

        r, g, b = webcolors.name_to_rgb(base_color)
        h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        lightness_gradient = np.linspace(l + 0.2, l - 0.1, n)

        # Convert float RGB to int for webcolors.rgb_to_hex
        def float_rgb_to_int(rgb_tuple):
            # Ensure tuple is exactly 3 elements (R, G, B)
            rgb = tuple(int(round(x * 255)) for x in rgb_tuple[:3])
            return (rgb[0], rgb[1], rgb[2])  # force 3-tuple

        return [
            webcolors.rgb_to_hex(float_rgb_to_int(hls_to_rgb(h, light, s)))
            for light in np.clip(lightness_gradient, 0, 1)
        ]

    color_map = {}
    color_map.update(
        {
            f"{city1} {day}": color
            for day, color in zip(day_list, get_color_gradient("red", len(day_list)))
        }
    )
    color_map.update(
        {
            f"{city2} {day}": color
            for day, color in zip(day_list, get_color_gradient("green", len(day_list)))
        }
    )
    df["Series"] = df["City"] + " " + df["Day"]
    fig = px.line(
        df,
        x="Hour",
        y=metric,
        color="Series",
        color_discrete_map=color_map,
        title=f"Hourly {metric.split('(')[0].strip()}: {city2.split(',')[0]} (green) vs {city1.split(',')[0]} (red)",
    )
    fig.update_layout(
        xaxis_title="Time of Day (AZ Time)",
        yaxis_title=metric,
        xaxis=dict(
            tickmode="array",
            tickvals=[0, 3, 6, 9, 12, 15, 18, 21, 24],
            ticktext=["12AM", "3AM", "6AM", "9AM", "12PM", "3PM", "6PM", "9PM", "12AM"],
        ),
        plot_bgcolor="white",
        margin=dict(b=100),
        legend_title_text="Forecast Day",
    )
    fig.update_layout(shapes=annotations["shapes"])
    for anno in annotations["annotations"]:
        fig.add_annotation(**anno)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    return fig


def plot_energy_curve(df: pd.DataFrame):
    """
    Plots the modeled energy performance curve.
    """
    fig = px.line(
        df,
        x="Hour",
        y="Performance",
        title="Predicted Energy Performance Curve",
        labels={"Performance": "Performance (%)", "Hour": "Hour of Day"},
    )
    # Add a fill to make it look like an area chart
    fig.update_traces(
        fill="tozeroy",
        line=dict(color="rgba(0, 114, 255, 1)"),
        fillcolor="rgba(0, 114, 255, 0.2)",
    )
    fig.update_xaxes(
        range=[0, 24], dtick=2
    )  # Set x-axis from 0 to 24 with ticks every 2 hours
    fig.update_yaxes(range=[0, 105])
    return fig
