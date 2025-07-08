# logic/user_profiles.py
import json
import os
from typing import Dict, Any, List

USER_PROFILES_PATH = os.path.join(
    os.path.dirname(__file__), "../data/user_profiles.json"
)


def load_profiles() -> Dict[str, Any]:
    """Load all user profiles from the JSON file."""
    if not os.path.exists(USER_PROFILES_PATH):
        return {}
    with open(USER_PROFILES_PATH, "r") as f:
        return json.load(f)


def save_profiles(profiles: Dict[str, Any]):
    """Save all user profiles to the JSON file."""
    with open(USER_PROFILES_PATH, "w") as f:
        json.dump(profiles, f, indent=4)


def get_profile_names() -> List[str]:
    profiles = load_profiles()
    return list(profiles.keys())


def get_profile(profile_name: str) -> Dict[str, Any]:
    profiles = load_profiles()
    return profiles.get(profile_name, {})


def update_profile(profile_name: str, profile_data: Dict[str, Any]):
    profiles = load_profiles()
    profiles[profile_name] = profile_data
    save_profiles(profiles)


def delete_profile(profile_name: str):
    profiles = load_profiles()
    if profile_name in profiles:
        del profiles[profile_name]
        save_profiles(profiles)
