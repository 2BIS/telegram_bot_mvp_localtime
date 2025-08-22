import json
from pathlib import Path
from aiogram import types
from typing import Dict, Any, Optional

STORE = Path("users.json")
ASSETS = Path("assets.json")

def _load() -> Dict[str, Any]:
    """Load users data from JSON file"""
    if STORE.exists():
        try:
            return json.loads(STORE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save(data: Dict[str, Any]) -> None:
    """Save users data to JSON file"""
    STORE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# Removed _rewrite_survey_csv function as we no longer use CSV files

def save_user_tz(user_id: int, tz_name: str) -> None:
    """Save user's timezone"""
    data = _load()
    key = str(user_id)
    record = data.get(key, {})
    record["tz"] = tz_name
    data[key] = record
    _save(data)

def save_user_init(user_id: int, username: str, init_ts: str) -> bool:
    """Save user initialization data, returns True if new user"""
    data = _load()
    key = str(user_id)
    is_new = key not in data
    record = data.get(key, {})
    record["username"] = username
    record["init_ts"] = init_ts
    data[key] = record
    _save(data)
    # Removed _rewrite_survey_csv(data) since we no longer use CSV
    return is_new

def save_survey_answer(user_id: int, answer: str) -> None:
    """Save user's survey answer"""
    data = _load()
    key = str(user_id)
    record = data.get(key, {})
    record["survey_answer"] = answer
    data[key] = record
    _save(data)
    # Removed _rewrite_survey_csv(data) to stop saving in CSV

def save_user_platform(user_id: int, platform: str) -> None:
    """Save user's platform preference"""
    data = _load()
    key = str(user_id)
    record = data.get(key, {})
    record["platform"] = platform
    data[key] = record
    _save(data)

def get_user_platform(user_id: int) -> str:
    """Get user's platform preference, default to 'desktop'"""
    data = _load()
    key = str(user_id)
    record = data.get(key, {})
    return record.get("platform", "desktop")

def get_user_data(user_id: int) -> dict:
    """Get user's complete data record"""
    data = _load()
    key = str(user_id)
    return data.get(key, {})

def auto_detect_platform(message: types.Message) -> str:
    """Automatically detect user's platform from message data"""
    user = message.from_user
    
    # Check first_name and last_name for iOS-specific patterns
    full_name = ""
    if user.first_name:
        full_name += user.first_name
    if user.last_name:
        full_name += " " + user.last_name
    
    # Check for iOS-specific emojis in name
    ios_emojis = ['📱', '🍎', '💻', '🌟', '✨', '🔥', '💯', '🎯', '🚀', '💝', '🎨', '🎭', '🎪', '🎢']
    if any(emoji in full_name for emoji in ios_emojis):
        return "ios"
    
    # Check username patterns (iOS users often use emojis or specific patterns)
    if user.username:
        username = user.username.lower()
        if any(emoji in username for emoji in ios_emojis):
            return "ios"
        # Check for patterns typical of iOS users
        if any(pattern in username for pattern in ['iphone', 'ios', 'apple', 'mac']):
            return "ios"
    
    # Check language_code for regions where iOS is more popular
    if user.language_code:
        lang = user.language_code.lower()
        # iOS is more popular in these regions
        ios_popular_langs = ['en-us', 'ja', 'ko', 'zh-cn', 'zh-tw', 'zh-hk']
        if lang in ios_popular_langs:
            return "ios"
    
    # Since we can't reliably detect platform from Telegram data alone,
    # we'll default to desktop but provide a way to override
    return "desktop"

# Removed force_ios_platform function - testing only

# --- Video file_id caching ---
def _load_assets() -> Dict[str, Any]:
    """Load assets data from JSON file"""
    if ASSETS.exists():
        try:
            return json.loads(ASSETS.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_assets(data: Dict[str, Any]) -> None:
    """Save assets data to JSON file"""
    ASSETS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_video_file_id(day: int) -> Optional[str]:
    """Get cached video file_id for specific day"""
    data = _load_assets()
    videos = data.get("videos", {})
    return videos.get(str(day))

def save_video_file_id(day: int, file_id: str) -> None:
    """Save video file_id to cache"""
    data = _load_assets()
    videos = data.get("videos", {})
    videos[str(day)] = file_id
    data["videos"] = videos
    _save_assets(data)

def clear_video_cache() -> None:
    """Clear all cached video file_ids"""
    data = _load_assets()
    if "videos" in data:
        del data["videos"]
    _save_assets(data)
    print("✅ Кэш видео очищен")

def clear_user_cache() -> None:
    """Clear all user data"""
    if STORE.exists():
        STORE.unlink()
        print("✅ Кэш пользователей очищен")
    else:
        print("ℹ️ Кэш пользователей уже пуст")