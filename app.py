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
    find_daily_best_workout,
)
from logic.performance import model_energy_curve
from logic.hydration import calculate_hydration_needs
from logic.user_profiles import load_profiles, get_profile_names, save_profile
from logic.generator import generate_move_checklist_text

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
    st.header("\U0001f464 Profile & Routine")

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

    # --- NEW Chronotype Selector ---
    chronotype_options = ["Default", "Morning Lark", "Night Owl"]
    chronotype = st.selectbox(
        "Your Chronotype",
        options=chronotype_options,
        index=chronotype_options.index(user_settings.get("chronotype", "Default")),
    )

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
                "chronotype": chronotype,
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


# --- Move Checklist Generator ---
def generate_move_checklist(city1, city2, plan_mode, sim_month, user_profile):
    """
    Generates a personalized move checklist based on cities, planning mode, month, and user profile.
    """
    checklist = []
    # General items
    checklist.append(
        f"✅ Research cost of living and housing in both {city1.split(',')[0]} and {city2.split(',')[0]}"
    )
    checklist.append(
        f"✅ Check visa/work permit requirements if moving internationally"
    )
    checklist.append(
        f"✅ Set up mail forwarding and update your address with banks, subscriptions, etc."
    )
    checklist.append(
        f"✅ Arrange for internet and utilities setup at your new location"
    )
    checklist.append(f"✅ Back up important digital files and documents")
    checklist.append(
        f"✅ Notify your employer/team of your move and update your working hours if needed"
    )

    # Weather/seasonal items
    if plan_mode == "Seasonal Simulation" and sim_month:
        checklist.append(
            f"✅ Review typical weather for {sim_month} in both cities (see above charts)"
        )
        checklist.append(
            f"✅ Pack clothing suitable for {sim_month} conditions in {city2.split(',')[0]}"
        )
        checklist.append(
            f"✅ Prepare for local climate: e.g., {'high humidity' if 'Humidity' in user_profile.get('user_settings', {}).get('chronotype', '') else 'heat/UV'} in {sim_month}"
        )
    else:
        checklist.append(
            f"✅ Check 7-day weather forecast for both cities (see above charts)"
        )
        checklist.append(
            f"✅ Pack for current weather conditions in {city2.split(',')[0]}"
        )

    # Routine/time zone items
    wake = user_profile.get("user_settings", {}).get("wake_time", "07:00")
    sleep = user_profile.get("user_settings", {}).get("sleep_time", "22:00")
    checklist.append(
        f"✅ Adjust your daily routine: wake at {wake}, sleep at {sleep} (local time)"
    )
    checklist.append(f"✅ Update calendar events and reminders to new time zone")
    checklist.append(
        f"✅ Plan for best workout times based on local weather (see recommendations above)"
    )

    # Health & wellness
    checklist.append(
        f"✅ Review hydration needs for your new city (see Hydration Timeline)"
    )
    checklist.append(
        f"✅ Prepare for changes in sunlight hours (see Gantt/energy charts)"
    )
    checklist.append(f"✅ Set up a new healthcare provider if needed")

    # Remote work
    checklist.append(
        f"✅ Test your remote work setup (Wi-Fi, VPN, video calls) in the new location"
    )
    checklist.append(f"✅ Research local coworking spaces or cafes if needed")

    return checklist


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
    # (Data loading and user settings retrieval remain the same)
    df1, df2 = st.session_state["df1"], st.session_state["df2"]
    c1_name, c2_name = st.session_state["city1"], st.session_state["city2"]

    current_settings = st.session_state.active_profile.get("user_settings", {})
    user_weight_kg = current_settings.get("weight_kg", 75)
    wake_time = get_time_from_str(current_settings.get("wake_time"), time(6, 0))
    sleep_time = get_time_from_str(current_settings.get("sleep_time"), time(22, 30))
    user_routine = st.session_state.active_profile.get("routine", [])

    # Get chronotype from the active profile
    user_settings = st.session_state.active_profile.get("user_settings", {})
    chronotype_setting = user_settings.get("chronotype", "Default")

    # --- GANTT CHART SECTION (RE-ORGANIZED INTO COLUMNS) ---
    st.header("🗓️ Daily Routine Planner")
    st.markdown(
        "Your AZ-based routine, visualized in local time with environmental context."
    )

    gantt_df = build_gantt_df(user_routine, df1, c1_name, df2, c2_name)

    gantt_col1, gantt_col2 = st.columns(2)
    with gantt_col1:
        df1_gantt = gantt_df[gantt_df["Resource"] == c1_name.split(",")[0]]
        bg_shapes1 = get_gantt_background_annotations(df1)
        gantt_fig1 = plot_gantt_schedule(df1_gantt, bg_shapes1)
        if gantt_fig1:
            st.plotly_chart(gantt_fig1, use_container_width=True)

    with gantt_col2:
        df2_gantt = gantt_df[gantt_df["Resource"] == c2_name.split(",")[0]]
        bg_shapes2 = get_gantt_background_annotations(df2)
        gantt_fig2 = plot_gantt_schedule(df2_gantt, bg_shapes2)
        if gantt_fig2:
            st.plotly_chart(gantt_fig2, use_container_width=True)

    st.markdown(
        """<span style="background-color: rgba(119, 221, 119, 0.2); padding: 2px 6px; border-radius: 4px;">Green Zones</span>: Optimal comfort.  \
        &nbsp;&nbsp;<span style="background-color: rgba(255, 82, 82, 0.2); padding: 2px 6px; border-radius: 4px;">Red Zones</span>: High Heat/UV.""",
        unsafe_allow_html=True,
    )

    # --- WORKOUT RECOMMENDER SECTION (UPDATED LOGIC) ---
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
            recommendations1 = find_daily_best_workout(
                df1, user_routine, workout_duration
            )
            if recommendations1:
                for rec in recommendations1:
                    st.markdown(
                        f"**{rec['day_label']}:** {rec['start_time'].strftime('%I:%M %p')} ({rec['details']})"
                    )
            else:
                st.info("No ideal slots found in the next 3 days.")

        with rec_col2:
            st.subheader(f"For {c2_name.split(',')[0]}")
            recommendations2 = find_daily_best_workout(
                df2, user_routine, workout_duration
            )
            if recommendations2:
                for rec in recommendations2:
                    st.markdown(
                        f"**{rec['day_label']}:** {rec['start_time'].strftime('%I:%M %p')} ({rec['details']})"
                    )
            else:
                st.info("No ideal slots found in the next 3 days.")

    st.header("\U0001f9d8 Personalized Productivity & Wellness")

    # --- UPDATED Energy Curve Call ---
    energy_df = model_energy_curve(wake_time, sleep_time, chronotype_setting)
    st.plotly_chart(plot_energy_curve(energy_df), use_container_width=True)

    # --- SIMPLIFIED: MOVE CHECKLIST GENERATOR (.txt) ---
    st.header("✅ Your Personalized Move Plan")
    st.markdown(
        "A practical, actionable checklist generated from your comparison to help you prepare."
    )

    plan_mode = st.session_state.get("plan_mode", "7-Day Forecast")
    sim_month = st.session_state.get("selected_month_name", None)

    # Generate the checklist as a single string
    checklist_text = generate_move_checklist_text(
        c1_name, c2_name, plan_mode, sim_month, st.session_state.active_profile
    )

    # Display a preview in a code block for clean formatting
    st.text_area("Checklist Preview", checklist_text, height=300)

    # Add a download button for the .txt file
    st.download_button(
        label="\U0001f4e5 Download Checklist (.txt)",
        data=checklist_text,
        file_name=f"MoveGuiderAI_Checklist_{c1_name.split(',')[0]}_to_{c2_name.split(',')[0]}.txt",
        mime="text/plain",
    )
