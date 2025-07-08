# app.py
import streamlit as st
import pandas as pd
from datetime import time

# --- REFACTORED IMPORTS ---
from config import WEATHERAPI_API_KEY
from api_clients import resolve_latlon_nominatim, get_weather_data_from_weatherapi
from logic.weather_parser import parse_weather_data
from logic.planner import (
    create_unified_df,
    get_plot_annotations,
    prepare_comfort_wheel_data,
)
from logic.performance import model_energy_curve
from logic.hydration import calculate_hydration_needs
from plotting.line_charts import plot_combined_metric
from plotting.area_charts import plot_energy_curve, plot_hydration_timeline
from plotting.radar_charts import plot_comfort_wheel

# Gantt chart imports will be added later

st.set_page_config(page_title="MoveGuiderAI", layout="wide")

# --- UI and Logic remain the same for now ---
with st.sidebar:
    st.header("\U0001f464 User Profile")
    user_weight_kg = st.number_input(
        "Your Weight (kg)", min_value=40, max_value=150, value=64
    )
    st.header("\U0001f319 Circadian Rhythm")
    wake_time = st.time_input("Wake-up time", value=time(5, 00))
    sleep_time = st.time_input("Bedtime", value=time(22, 30))


@st.cache_data(ttl=3600)
def get_city_data(city_name: str) -> pd.DataFrame | None:
    coordinates = resolve_latlon_nominatim(city_name)
    if not coordinates:
        st.error(
            f"Could not find coordinates for '{city_name}'. Please try a different name or format."
        )
        return None
    weather_data = get_weather_data_from_weatherapi(
        coordinates["lat"], coordinates["lon"], WEATHERAPI_API_KEY
    )
    if not weather_data:
        st.error(f"Failed to fetch weather data for {city_name}.")
        return None
    return parse_weather_data(weather_data)


st.title("MoveGuiderAI \U0001f3d9️")
st.markdown(
    "A comparative analytics dashboard for personal productivity and environmental metrics."
)

col1, col2 = st.columns(2)
with col1:
    city1_name = st.text_input("City One (Red)", "Tempe, AZ")
with col2:
    city2_name = st.text_input("City Two (Green)", "Dallas, TX")

if st.button("Compare Cities", type="primary"):
    df1 = get_city_data(city1_name)
    df2 = get_city_data(city2_name)
    if df1 is not None and df2 is not None:
        st.session_state["df1"] = df1
        st.session_state["df2"] = df2
        st.session_state["city1"] = city1_name
        st.session_state["city2"] = city2_name
        st.session_state["energy_df"] = model_energy_curve(wake_time, sleep_time)

if "df1" in st.session_state:
    df1, df2 = st.session_state["df1"], st.session_state["df2"]
    c1_name, c2_name = st.session_state["city1"], st.session_state["city2"]
    energy_df = st.session_state["energy_df"]

    annotations = get_plot_annotations(df1, c1_name, df2, c2_name)

    st.header("\U0001f327️ Environmental Comparison")
    temp_df = create_unified_df(df1, c1_name, df2, c2_name, "Temperature (°C)")
    st.plotly_chart(
        plot_combined_metric(
            temp_df, "Temperature (°C)", c1_name, c2_name, annotations
        ),
        use_container_width=True,
    )

    hum_df = create_unified_df(df1, c1_name, df2, c2_name, "Humidity (%)")
    st.plotly_chart(
        plot_combined_metric(hum_df, "Humidity (%)", c1_name, c2_name, annotations),
        use_container_width=True,
    )

    uv_df = create_unified_df(df1, c1_name, df2, c2_name, "UV Index")
    st.plotly_chart(
        plot_combined_metric(uv_df, "UV Index", c1_name, c2_name, annotations),
        use_container_width=True,
    )

    st.header("\U0001f9d8 Personalized Productivity & Wellness")
    st.plotly_chart(plot_energy_curve(energy_df), use_container_width=True)

    col_hydro1, col_hydro2 = st.columns(2)
    with col_hydro1:
        hydration_df1 = calculate_hydration_needs(df1, user_weight_kg)
        st.plotly_chart(
            plot_hydration_timeline(hydration_df1, c1_name), use_container_width=True
        )
    with col_hydro2:
        hydration_df2 = calculate_hydration_needs(df2, user_weight_kg)
        st.plotly_chart(
            plot_hydration_timeline(hydration_df2, c2_name), use_container_width=True
        )

    comfort_df = prepare_comfort_wheel_data(df1, c1_name, df2, c2_name)
    st.plotly_chart(
        plot_comfort_wheel(comfort_df, c1_name, c2_name), use_container_width=True
    )
