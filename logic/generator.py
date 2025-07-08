# logic/generator.py
from datetime import datetime


def generate_move_checklist_text(
    city_from: str,
    city_to: str,
    plan_mode: str,
    sim_month: str | None,
    user_profile: dict,
) -> str:
    """
    REWRITTEN: Generates a personalized move checklist as a clean, formatted
    string suitable for a .txt file.
    """
    city_to_short = city_to.split(",")[0]
    lines = []

    # Header
    lines.append("===============================================")
    lines.append("    MoveGuiderAI - Your Personalized Move Plan")
    lines.append("===============================================")
    lines.append(f"\nMoving from: {city_from}")
    lines.append(f"Moving to: {city_to_short}")
    lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d')}\n")

    # Sections
    def add_section(title, items):
        lines.append(f"\n--- {title.upper()} ---\n")
        for item in items:
            lines.append(f"[ ] {item}")

    # Section 1: Logistics
    logistics_items = [
        "Research: Cost of living, housing, and neighborhoods.",
        "Legal: Check visa/work permit requirements if applicable.",
        "Address Change: Update with USPS/mail service, banks, subscriptions.",
        "Utilities: Arrange disconnection at old address and setup at new address (Internet, electricity, water, gas).",
        "Employer: Notify your team of the move and any changes to your working hours.",
    ]
    add_section("1. Logistics & Administration", logistics_items)

    # Section 2: Packing
    packing_items = []
    if plan_mode == "Seasonal Simulation" and sim_month:
        packing_items.append(
            f"Review Seasonal Data: You planned for a move in {sim_month}. Review the charts for typical conditions in {city_to_short}."
        )
        packing_items.append(
            f"Pack Accordingly: Pack clothing suitable for {sim_month} weather in {city_to_short}."
        )
    else:
        packing_items.append(
            f"Check 7-Day Forecast: Review the live forecast for {city_to_short} before you travel."
        )
        packing_items.append(
            "Pack Accordingly: Pack for the immediate weather conditions."
        )
    packing_items.append(
        "Local Climate Prep: Be ready for local norms (e.g., high humidity gear, rain protection, sunblock)."
    )
    add_section("2. Packing & Environmental Prep", packing_items)

    # Section 3: Wellness
    wake = user_profile.get("user_settings", {}).get("wake_time", "N/A")
    sleep = user_profile.get("user_settings", {}).get("sleep_time", "N/A")
    wellness_items = [
        f"Adjust Body Clock: Start adjusting to your new local time. Your plan is based on waking at {wake} and sleeping at {sleep}.",
        "Update Calendars: Shift all digital calendar events and reminders to the new timezone.",
        "Plan Workouts: Use the 'Best Workout Times' recommendations to schedule your first week of fitness.",
        f"Hydration: Note the hydration needs for {city_to_short} and plan to drink enough water, especially on day one.",
        "Healthcare: Research and shortlist new doctors, dentists, and other healthcare providers.",
    ]
    add_section("3. Routine & Wellness Transition", wellness_items)

    # Section 4: Remote Work
    remote_work_items = [
        "Day 1 Connectivity: Ensure you have a plan for internet on your first day (e.g., mobile hotspot as a backup).",
        "Test Your Setup: Once internet is live, test your full remote work stack (VPN, video calls, software access).",
        "Find Your Spots: Research local coffee shops or coworking spaces with good Wi-Fi as alternatives.",
    ]
    add_section("4. Remote Work Setup", remote_work_items)

    return "\n".join(lines)
