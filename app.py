# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, time
from config import OPENWEATHER_API_KEY, WEATHERAPI_API_KEY

# --- UPDATED IMPORT ---
from api_clients import resolve_latlon_nominatim, get_weather_data_from_weatherapi
from logic import parse_weather_data, create_routine_df, model_energy_curve
from plotting import plot_weather_metrics, plot_gantt_chart, plot_energy_curve

# --- Page & Sidebar Configuration ---
st.set_page_config(page_title="MoveGuiderAI", layout="wide")

with st.sidebar:
    st.header("\U0001f464 User Profile")
    user_weight_kg = st.number_input(
        "Your Weight (kg)", min_value=40, max_value=150, value=70
    )
    st.header("\U0001f319 Circadian Rhythm")
    wake_time = st.time_input("Wake-up time", value=time(6, 30))
    sleep_time = st.time_input("Bedtime", value=time(22, 30))
    st.info(
        "Future versions will allow importing Apple Health data for higher accuracy."
    )


# --- UPDATED CACHING FUNCTION ---
@st.cache_data(ttl=3600)
def get_city_data(city_name: str) -> pd.DataFrame | None:
    """
    High-level function to resolve coordinates, fetch weather, and parse it.
    """
    # Step 1: Use the new, robust geocoder
    coordinates = resolve_latlon_nominatim(city_name)
    if not coordinates:
        st.error(
            f"Could not find coordinates for '{city_name}'. Please try a different name or format (e.g., 'City, Country')."
        )
        return None

    # --- THIS IS THE KEY CHANGE ---
    # Call the new WeatherAPI.com function with the new key
    weather_data = get_weather_data_from_weatherapi(
        coordinates["lat"], coordinates["lon"], WEATHERAPI_API_KEY
    )

    if not weather_data:
        st.error(f"Failed to fetch weather data for {city_name}.")
        return None

    return parse_weather_data(weather_data)


# --- UI Layout (this remains the same) ---
st.title("MoveGuiderAI \U0001f3d9️")
st.markdown("Compare productivity and environmental metrics between two cities.")

col1, col2 = st.columns(2)
with col1:
    city1_name = st.text_input("Enter City One", "Phoenix, US")
with col2:
    city2_name = st.text_input("Enter City Two", "Euless, TX")

if st.button("Compare Cities", type="primary"):
    st.session_state["city1_name"] = city1_name
    st.session_state["city2_name"] = city2_name
    st.session_state["city1_df"] = get_city_data(city1_name) if city1_name else None
    st.session_state["city2_df"] = get_city_data(city2_name) if city2_name else None
    st.session_state["energy_df"] = model_energy_curve(wake_time, sleep_time)

# --- Row 2: Weather Line Charts ---
if "city1_df" in st.session_state and st.session_state.get("city1_df") is not None:
    st.header("Weather Forecast")
    col1, col2 = st.columns(2)
    with col1:
        fig1 = plot_weather_metrics(
            st.session_state["city1_df"], st.session_state["city1_name"]
        )
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        if (
            "city2_df" in st.session_state
            and st.session_state.get("city2_df") is not None
        ):
            fig2 = plot_weather_metrics(
                st.session_state["city2_df"], st.session_state["city2_name"]
            )
            st.plotly_chart(fig2, use_container_width=True)

# --- Row 3: Daily Routine Gantt Charts ---
if "city1_df" in st.session_state and st.session_state.get("city1_df") is not None:
    st.header("Daily Routine Planner")
    col1, col2 = st.columns(2)
    with col1:
        routine1_df = create_routine_df(
            st.session_state["city1_df"], st.session_state["city1_name"]
        )
        gantt1 = plot_gantt_chart(routine1_df, st.session_state["city1_name"])
        st.plotly_chart(gantt1, use_container_width=True)
    with col2:
        if (
            "city2_df" in st.session_state
            and st.session_state.get("city2_df") is not None
        ):
            routine2_df = create_routine_df(
                st.session_state["city2_df"], st.session_state["city2_name"]
            )
            gantt2 = plot_gantt_chart(routine2_df, st.session_state["city2_name"])
            st.plotly_chart(gantt2, use_container_width=True)

# --- Row 4: Personal Metrics ---
if "energy_df" in st.session_state and st.session_state.get("energy_df") is not None:
    st.header("Personalized Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        energy_fig = plot_energy_curve(st.session_state["energy_df"])
        st.plotly_chart(energy_fig, use_container_width=True)
