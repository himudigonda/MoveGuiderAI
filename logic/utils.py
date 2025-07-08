# logic/utils.py
import pytz


def to_az_hour(dt_aware):
    """Converts a timezone-aware datetime object to a float hour in Arizona time."""
    home_tz = pytz.timezone("America/Phoenix")
    az_time = dt_aware.astimezone(home_tz)
    return az_time.hour + az_time.minute / 60
