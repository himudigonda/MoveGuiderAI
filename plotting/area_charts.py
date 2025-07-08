# plotting/area_charts.py
import plotly.express as px
import pandas as pd


def plot_hydration_timeline(df: pd.DataFrame, city_name: str):
    """
    Creates a stacked area chart for cumulative hydration needs.
    (Moved from plotting.py)
    """
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


def plot_energy_curve(df: pd.DataFrame):
    """
    Plots the modeled energy performance curve.
    (Moved from plotting.py)
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
