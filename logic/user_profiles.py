# logic/user_profiles.py
import json
import os
from typing import Dict, Any, List
from datetime import datetime

# Build an absolute path to the data file
USER_PROFILES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "user_profiles.json"
)


def load_profiles() -> Dict[str, Any]:
    """Load all user profiles from the JSON file."""
    try:
        if not os.path.exists(USER_PROFILES_PATH):
            # Create a default if it doesn't exist
            default_profile = {
                "Default Profile": {
                    "user_settings": {
                        "weight_kg": 75,
                        "wake_time": "06:00",
                        "sleep_time": "22:30",
                    },
                    "routine": [
                        {
                            "task": "Morning Deep Work",
                            "start": "08:00",
                            "end": "10:00",
                            "type": "work",
                        },
                        {
                            "task": "Team Standup",
                            "start": "10:00",
                            "end": "10:30",
                            "type": "meetings",
                        },
                        {
                            "task": "Lunch & Walk",
                            "start": "12:30",
                            "end": "13:30",
                            "type": "break",
                        },
                        {
                            "task": "Afternoon Tasks",
                            "start": "13:30",
                            "end": "17:00",
                            "type": "work",
                        },
                        {
                            "task": "Workout",
                            "start": "17:30",
                            "end": "18:30",
                            "type": "fitness",
                        },
                    ],
                }
            }
            save_profiles(default_profile)
            return default_profile
        with open(USER_PROFILES_PATH, "r") as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading profiles: {e}")
        return {}


def save_profiles(profiles: Dict[str, Any]):
    """Save all user profiles to the JSON file."""
    try:
        with open(USER_PROFILES_PATH, "w") as f:
            json.dump(profiles, f, indent=4)
    except IOError as e:
        print(f"Error saving profiles: {e}")


def get_profile_names() -> List[str]:
    """Get a list of all profile names."""
    profiles = load_profiles()
    return sorted(list(profiles.keys()))


def get_profile(profile_name: str) -> Dict[str, Any]:
    """Retrieve a single profile by name."""
    profiles = load_profiles()
    return profiles.get(profile_name, {})


def save_profile(profile_name: str, profile_data: Dict[str, Any]):
    """Save or update a single profile."""
    if not profile_name.strip():
        raise ValueError("Profile name cannot be empty.")
    profiles = load_profiles()
    profiles[profile_name] = profile_data
    save_profiles(profiles)
