# plotting/area_charts.py
import plotly.express as px
import plotly.graph_objects as go  # New import
import pandas as pd


def plot_combined_hydration(
    df1: pd.DataFrame, name1: str, df2: pd.DataFrame, name2: str
):
    """
    Creates a single, overlapping area chart for hydration needs of two cities.
    """
    fig = go.Figure()

    # Add City 1 trace
    fig.add_trace(
        go.Scatter(
            x=df1.index,
            y=df1["Cumulative Intake (ml)"],
            fill="tozeroy",
            mode="lines",
            line_color="rgba(255, 87, 87, 1.0)",  # Solid Red Line
            fillcolor="rgba(255, 87, 87, 0.3)",  # Light Red Fill
            name=f"Hydration Need: {name1.split(',')[0]}",
        )
    )

    # Add City 2 trace
    fig.add_trace(
        go.Scatter(
            x=df2.index,
            y=df2["Cumulative Intake (ml)"],
            fill="tozeroy",
            mode="lines",
            line_color="rgba(0, 128, 0, 1.0)",  # Solid Green Line
            fillcolor="rgba(0, 128, 0, 0.3)",  # Light Green Fill
            name=f"Hydration Need: {name2.split(',')[0]}",
        )
    )

    fig.update_layout(
        title=f"Comparative Hydration Timeline",
        xaxis_title="Time of Day (First Forecast Day)",
        yaxis_title="Cumulative Water Intake (ml)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def plot_energy_curve(df: pd.DataFrame):
    """
    Plots the modeled energy performance curve. (Unchanged)
    """
    fig = px.line(
        df,
        x="Hour",
        y="Performance",
        title="Predicted Energy Performance Curve",
        labels={"Performance": "Performance (%)", "Hour": "Hour of Day"},
    )
    fig.update_traces(
        fill="tozeroy",
        line=dict(color="rgba(0, 114, 255, 1)"),
        fillcolor="rgba(0, 114, 255, 0.2)",
    )
    fig.update_xaxes(range=[0, 24], dtick=2)
    fig.update_yaxes(range=[0, 105])
    return fig
