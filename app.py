# app.py
import streamlit as st
import pandas as pd
from config import OPENWEATHER_API_KEY
from api_clients import get_city_coordinates, get_weather_data
from logic import parse_weather_data, create_routine_df
from plotting import plot_weather_metrics, plot_gantt_chart

st.set_page_config(page_title="MoveGuiderAI", layout="wide")


@st.cache_data(ttl=3600)
def get_city_data(city_name: str) -> pd.DataFrame | None:
    coordinates = get_city_coordinates(city_name, OPENWEATHER_API_KEY)
    if not coordinates:
        st.error(f"Could not find coordinates for {city_name}.")
        return None
    weather_data = get_weather_data(
        coordinates["lat"], coordinates["lon"], OPENWEATHER_API_KEY
    )
    if not weather_data:
        st.error(f"Failed to fetch weather data for {city_name}.")
        return None
    return parse_weather_data(weather_data)


# --- UI Layout ---
st.title("MoveGuiderAI 🏙️")
st.markdown("Compare productivity and environmental metrics between two cities.")

# --- Row 1: Inputs ---
col1, col2 = st.columns(2)
with col1:
    city1_name = st.text_input("Enter City One", "Phoenix")
with col2:
    city2_name = st.text_input("Enter City Two", "London")

if st.button("Compare Cities", type="primary"):
    st.session_state["city1_df"] = get_city_data(city1_name) if city1_name else None
    st.session_state["city2_df"] = get_city_data(city2_name) if city2_name else None

# --- Row 2: Weather Line Charts ---
if "city1_df" in st.session_state and st.session_state["city1_df"] is not None:
    st.header("Weather Forecast")
    col1, col2 = st.columns(2)
    with col1:
        fig1 = plot_weather_metrics(st.session_state["city1_df"], city1_name)
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        if "city2_df" in st.session_state and st.session_state["city2_df"] is not None:
            fig2 = plot_weather_metrics(st.session_state["city2_df"], city2_name)
            st.plotly_chart(fig2, use_container_width=True)

# --- Row 3: Daily Routine Gantt Charts ---
if "city1_df" in st.session_state and st.session_state["city1_df"] is not None:
    st.header("Daily Routine Planner")
    col1, col2 = st.columns(2)
    with col1:
        routine1_df = create_routine_df(st.session_state["city1_df"], city1_name)
        gantt1 = plot_gantt_chart(routine1_df, city1_name)
        st.plotly_chart(gantt1, use_container_width=True)
    with col2:
        if "city2_df" in st.session_state and st.session_state["city2_df"] is not None:
            routine2_df = create_routine_df(st.session_state["city2_df"], city2_name)
            gantt2 = plot_gantt_chart(routine2_df, city2_name)
            st.plotly_chart(gantt2, use_container_width=True)
