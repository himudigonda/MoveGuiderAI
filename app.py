# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, time

# --- REFACTORED & NEW IMPORTS ---
from config import WEATHERAPI_API_KEY
from api_clients import resolve_latlon_nominatim, get_weather_data_from_weatherapi
from logic.weather_parser import parse_weather_data
from logic.planner import (
    create_unified_df,
    get_plot_annotations,
    prepare_comfort_wheel_data,
    build_gantt_df,
    get_gantt_background_annotations,
    find_optimal_workout_slots,
)
from logic.performance import model_energy_curve
from logic.hydration import calculate_hydration_needs
from logic.user_profiles import load_profiles, get_profile_names, save_profile

from plotting.line_charts import plot_combined_metric

# --- UPDATED IMPORTS ---
from plotting.area_charts import plot_energy_curve, plot_combined_hydration
from plotting.radar_charts import plot_comfort_wheel
from plotting.gantt import plot_gantt_schedule

st.set_page_config(page_title="MoveGuiderAI", layout="wide")

# --- Initialize Session State ---
if "active_profile" not in st.session_state:
    profiles = load_profiles()
    st.session_state.active_profile = profiles.get("Default Profile", {})

# --- Sidebar for Profile Management ---
with st.sidebar:
    st.header("👤 Profile & Routine")

    profile_names = get_profile_names()

    # Profile selection and loading
    selected_profile_name = st.selectbox(
        "Select Profile",
        options=profile_names,
        index=(
            profile_names.index("Default Profile")
            if "Default Profile" in profile_names
            else 0
        ),
    )
    if st.button("Load Profile"):
        st.session_state.active_profile = load_profiles().get(selected_profile_name, {})
        st.success(f"Profile '{selected_profile_name}' loaded!")
        st.rerun()

    # Get current values from session state for editing
    active_profile_data = st.session_state.active_profile
    user_settings = active_profile_data.get("user_settings", {})
    routine_df = pd.DataFrame(active_profile_data.get("routine", []))

    st.subheader("Your Settings")
    weight = st.number_input(
        "Your Weight (kg)",
        min_value=40,
        max_value=150,
        value=user_settings.get("weight_kg", 75),
    )
    wake_str = st.text_input(
        "Wake-up time (HH:MM)", value=user_settings.get("wake_time", "06:00")
    )
    sleep_str = st.text_input(
        "Bedtime (HH:MM)", value=user_settings.get("sleep_time", "22:30")
    )

    st.subheader("Your Daily Routine (Home Timezone: AZ)")
    edited_routine_df = st.data_editor(
        routine_df, num_rows="dynamic", use_container_width=True
    )

    st.subheader("Save Changes")
    new_profile_name = st.text_input(
        "Save as profile name", value=selected_profile_name
    )
    if st.button("Save Profile"):
        updated_profile = {
            "user_settings": {
                "weight_kg": weight,
                "wake_time": wake_str,
                "sleep_time": sleep_str,
            },
            "routine": edited_routine_df.to_dict("records"),
        }
        save_profile(new_profile_name, updated_profile)
        st.session_state.active_profile = updated_profile
        st.success(f"Profile '{new_profile_name}' saved successfully!")


# --- Helper to convert string times from profile to time objects ---
def get_time_from_str(time_str: str, default_time: time) -> time:
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except (ValueError, TypeError):
        return default_time


# --- Caching function for weather data ---
@st.cache_data(ttl=3600)
def get_city_data(city_name: str):
    # (This function remains unchanged)
    from api_clients import resolve_latlon_nominatim, get_weather_data_from_weatherapi
    from logic.weather_parser import parse_weather_data

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


# --- Main App Body ---
st.title("MoveGuiderAI 🏙️")
st.markdown("A relocation intelligence platform for remote professionals.")

col1, col2 = st.columns(2)
with col1:
    city1_name = st.text_input("Compare City (Red)", "Tempe, AZ")
with col2:
    city2_name = st.text_input("With City (Green)", "Dallas, TX")

if st.button("Generate Comparison", type="primary"):
    df1 = get_city_data(city1_name)
    df2 = get_city_data(city2_name)
    if df1 is not None and df2 is not None:
        st.session_state["df1"] = df1
        st.session_state["df2"] = df2
        st.session_state["city1"] = city1_name
        st.session_state["city2"] = city2_name

# --- Display charts if data is available ---
if "df1" in st.session_state:
    df1, df2 = st.session_state["df1"], st.session_state["df2"]
    c1_name, c2_name = st.session_state["city1"], st.session_state["city2"]

    current_settings = st.session_state.active_profile.get("user_settings", {})
    user_weight_kg = current_settings.get("weight_kg", 75)
    wake_time = get_time_from_str(current_settings.get("wake_time"), time(6, 0))
    sleep_time = get_time_from_str(current_settings.get("sleep_time"), time(22, 30))
    user_routine = st.session_state.active_profile.get("routine", [])

    st.header("🗓️ Daily Routine Planner")
    gantt_df = build_gantt_df(user_routine, df1, c1_name, df2, c2_name)

    # --- UPDATED: Full-width Gantt charts in separate rows ---
    st.markdown(f"**Timeline for {c1_name.split(',')[0]}**")
    df1_gantt = gantt_df[gantt_df["Resource"] == c1_name.split(",")[0]]
    bg_shapes1 = get_gantt_background_annotations(df1)
    gantt_fig1 = plot_gantt_schedule(df1_gantt, c1_name, c2_name, bg_shapes1)
    if gantt_fig1:
        st.plotly_chart(gantt_fig1, use_container_width=True)

    st.markdown(f"**Timeline for {c2_name.split(',')[0]}**")
    df2_gantt = gantt_df[gantt_df["Resource"] == c2_name.split(",")[0]]
    bg_shapes2 = get_gantt_background_annotations(df2)
    gantt_fig2 = plot_gantt_schedule(df2_gantt, c1_name, c2_name, bg_shapes2)
    if gantt_fig2:
        st.plotly_chart(gantt_fig2, use_container_width=True)

    st.markdown(
        """
        <span style="background-color: rgba(119, 221, 119, 0.2); padding: 2px 6px; border-radius: 4px;">Green Zones</span>: Optimal comfort (Temp 18-25°C, Low UV). Ideal for walks and outdoor breaks.  
        &nbsp;&nbsp;
        <span style="background-color: rgba(255, 82, 82, 0.2); padding: 2px 6px; border-radius: 4px;">Red Zones</span>: High Heat (>30°C) or High UV (>7). Caution advised for outdoor activity.
        """,
        unsafe_allow_html=True,
    )

    # --- NEW: WORKOUT RECOMMENDER SECTION ---
    with st.expander("🏋️‍♀️ Find the Best Workout Times", expanded=True):
        workout_duration = st.number_input(
            "Desired workout duration (minutes)",
            min_value=15,
            max_value=120,
            value=60,
            step=15,
        )
        rec_col1, rec_col2 = st.columns(2)
        with rec_col1:
            st.subheader(f"For {c1_name.split(',')[0]}")
            recommendations1 = find_optimal_workout_slots(
                df1, user_routine, workout_duration
            )
            if recommendations1:
                for i, rec in enumerate(recommendations1):
                    emoji = (
                        "🏆" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "✅"
                    )
                    st.markdown(
                        f"{emoji} **{rec['start_time'].strftime('%a, %I:%M %p')}** ({rec['details']})"
                    )
        with rec_col2:
            st.subheader(f"For {c2_name.split(',')[0]}")
            recommendations2 = find_optimal_workout_slots(
                df2, user_routine, workout_duration
            )
            if recommendations2:
                for i, rec in enumerate(recommendations2):
                    emoji = (
                        "🏆" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "✅"
                    )
                    st.markdown(
                        f"{emoji} **{rec['start_time'].strftime('%a, %I:%M %p')}** ({rec['details']})"
                    )

    st.header("\U0001f9d8 Personalized Productivity & Wellness")
    st.plotly_chart(
        plot_energy_curve(model_energy_curve(wake_time, sleep_time)),
        use_container_width=True,
    )

    # --- UPDATED: Hydration and Comfort Wheel plotting ---
    hydration_df1 = calculate_hydration_needs(df1, user_weight_kg)
    hydration_df2 = calculate_hydration_needs(df2, user_weight_kg)
    st.plotly_chart(
        plot_combined_hydration(hydration_df1, c1_name, hydration_df2, c2_name),
        use_container_width=True,
    )

    comfort_df = prepare_comfort_wheel_data(df1, c1_name, df2, c2_name)
    st.plotly_chart(
        plot_comfort_wheel(comfort_df, c1_name, c2_name), use_container_width=True
    )

    # (Environmental Comparison line charts section is now last)
    st.header("\U0001f327️ Environmental Comparison")
    annotations = get_plot_annotations(df1, c1_name, df2, c2_name)
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
