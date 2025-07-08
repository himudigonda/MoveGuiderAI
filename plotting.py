# plotting.py
import plotly.express as px
import plotly.graph_objects as go  # Import graph_objects
import pandas as pd
import numpy as np
import webcolors
from colorsys import rgb_to_hls, hls_to_rgb


def plot_combined_metric(
    df: pd.DataFrame, metric: str, city1: str, city2: str, annotations: dict
):
    """
    REWRITTEN: Creates a sophisticated, multi-trace plot with daily dashed lines
    and a solid average line for each city.
    """
    fig = go.Figure()
    # --- Define color schemes ---
    city_colors = {city1: "red", city2: "green"}

    # Helper to get color gradients
    def get_color_gradient(base_color, n):
        r, g, b = webcolors.name_to_rgb(base_color)
        h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        lightness_gradient = np.linspace(l + 0.2, l - 0.1, n)
        return [
            f"rgb{tuple(int(x * 255) for x in hls_to_rgb(h, light, s))}"
            for light in np.clip(lightness_gradient, 0, 1)
        ]

    # --- Plotting logic ---
    for city_name, base_color in city_colors.items():
        city_df = df[df["City"] == city_name]
        days = city_df["Day"].unique()
        color_palette = get_color_gradient(base_color, len(days))
        # 1. Plot each day's smoothed data as a thin, dashed line
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
        # 2. Plot the solid average line for the city
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
    # --- Apply Layout and Annotations ---
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


def plot_hydration_timeline(df: pd.DataFrame, city_name: str):
    """
    Creates a stacked area chart for cumulative hydration needs.
    """
    import plotly.express as px

    fig = px.area(
        df,
        x=df.index,
        y="Cumulative Intake (ml)",
        title=f"Hydration Need Timeline for {city_name.split(',')[0]}",
        labels={"value": "Intake (ml)", "index": "Time"},
    )
    fig.update_traces(line=dict(color="#33C4FF"), fillcolor="rgba(51, 196, 255, 0.2)")
    fig.update_layout(showlegend=False)
    return fig


def plot_comfort_wheel(df: pd.DataFrame, city_name: str):
    """
    REVISED: Creates a radar chart (polar chart) for comfort metrics without using pivot.
    """
    # --- Data Preparation (No Pivot) ---

    # 1. Get the ideal range data by filtering and grouping
    ideal_df = (
        df[df["Category"] == "Ideal Range"]
        .groupby("Metric")["Value"]
        .agg(["min", "max"])
        .reset_index()
    )

    # 2. Get the current value data by filtering
    current_df = df[df["Category"] == "Current Value"][["Metric", "Value"]]

    # Ensure the order of metrics is the same for both dataframes
    # This is crucial for the plot to align correctly.
    metric_order = ideal_df["Metric"]
    current_df = current_df.set_index("Metric").loc[metric_order].reset_index()

    fig = go.Figure()

    # Add the 'Ideal Range' as a filled area
    # We trace from the min value out to the max value and back to the min to create a filled band
    fig.add_trace(
        go.Scatterpolar(
            r=list(ideal_df["max"]) + list(ideal_df["max"])[:1],  # Close the shape
            theta=list(ideal_df["Metric"]) + list(ideal_df["Metric"])[:1],
            fill="toself",
            fillcolor="rgba(44, 160, 44, 0.3)",
            line=dict(color="rgba(44, 160, 44, 0.5)"),
            name="Ideal Range",
        )
    )

    # Add the 'Current Values' as a separate line on top
    fig.add_trace(
        go.Scatterpolar(
            r=list(current_df["Value"]) + list(current_df["Value"])[:1],
            theta=list(current_df["Metric"]) + list(current_df["Metric"])[:1],
            fill="toself",
            fillcolor="rgba(255, 87, 87, 0.4)",
            line=dict(color="red"),
            name="Current Value",
        )
    )

    # Determine a dynamic range for the radial axis
    max_val = max(ideal_df["max"].max(), current_df["Value"].max())

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max_val * 1.1])  # Add 10% padding
        ),
        showlegend=True,
        title=f"Polar Comfort Wheel for {city_name.split(',')[0]}",
    )

    return fig
