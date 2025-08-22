from datetime import datetime, timedelta
from typing import Optional, Union
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

import pytz
import re

# Initialize global objects
_tf = TimezoneFinder()
_geocoder = Nominatim(user_agent="bazi_sender_bot")

def guess_tz_from_location(lat: float, lon: float) -> Optional[str]:
    """Guess timezone from coordinates"""
    try:
        return _tf.timezone_at(lat=lat, lng=lon)
    except Exception:
        return None

def tz_name_to_tz(tz_name: str) -> Union[pytz.FixedOffset, pytz.BaseTzInfo]:
    """Convert timezone name to pytz timezone object"""
    # Check if it's a UTC offset format (e.g., "UTC+3", "UTC-5")
    m = re.fullmatch(r"UTC([+-]\d{1,2})", tz_name)
    if m:
        hours = int(m.group(1))
        return pytz.FixedOffset(hours * 60)
    
    # Otherwise treat as timezone name
    return pytz.timezone(tz_name)

def local_15_to_utc(now_utc: datetime, tz_name: str, day_offset: int, hour: int = 15, minute: int = 0) -> datetime:
    """Convert local time to UTC for scheduling"""
    tz = tz_name_to_tz(tz_name)
    
    # Convert current UTC time to local timezone
    now_local = pytz.utc.localize(now_utc).astimezone(tz)
    
    # Calculate target local time
    target_local = now_local.replace(
        hour=hour, 
        minute=minute, 
        second=0, 
        microsecond=0
    ) + timedelta(days=day_offset)
    
    # Convert back to UTC
    return target_local.astimezone(pytz.utc)

def tz_from_city_name(city_name: str) -> Optional[str]:
    """Get timezone from city name using geocoding"""
    try:
        # Geocode city name
        loc = _geocoder.geocode(city_name, language="ru,en")
        if not loc:
            return None
        
        # Get timezone from coordinates
        tz = _tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
        return tz
        
    except Exception:
        return None