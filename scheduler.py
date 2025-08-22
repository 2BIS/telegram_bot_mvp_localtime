import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from aiogram.types import InputFile
from aiogram.utils.exceptions import NetworkError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import bot
from storage import get_video_file_id, save_video_file_id, get_user_platform
from utils_time import local_15_to_utc
from utils_video import get_video_dimensions
# Removed import of create_force_document_bypass
# from ios_cache_bypass import create_force_document_bypass

# Initialize scheduler
scheduler = AsyncIOScheduler(timezone="UTC")

# Constants
FINAL_FOLLOWUP_TEXT = (
    "Если у вас есть вопросы по карьере, бизнесу, недвижимости, профориентации, "
    "отношениям, какой-то из моих программ или консультаций, присылайте их по этой "
    "форме - я запишу для вас отдельный подкаст в своем телеграм канале "
    "Китайский астролог.\n"
    "https://forms.gle/2S3KvfxGwGdSFexB8"
)

ERROR_MESSAGE = "Произошла ошибка. Свяжитесь, пожалуйста, с администратором бота: @aspronea"

async def send_followup_message(user_id: int) -> None:
    """Send final follow-up message to user"""
    try:
        await bot.send_message(user_id, FINAL_FOLLOWUP_TEXT)
    except Exception as e:
        logging.error(f"[send_followup_message] Ошибка для {user_id}: {e}")

def _get_video_path(day: int, platform: str, video_dir: Path) -> Path:
    """Get appropriate video path based on platform and day"""
    if platform == "ios":
        # iOS-specific version with improved encoding
        ios_path = video_dir / "ios" / f"ios_day{day}.mp4"
        if ios_path.exists():
            logging.info("iOS: using ios_day%d.mp4", day)
            return ios_path
        
        # Fallback to iOS desktop version if original not found
        ios_desktop_path = video_dir / "ios" / f"ios_day{day}_desktop.mp4"
        if ios_desktop_path.exists():
            logging.info("iOS: using ios_day%d_desktop.mp4 (fallback)", day)
            return ios_desktop_path
            
        # Final fallback to regular video if iOS versions not found
        logging.warning("iOS: no iOS-specific video found for day %d, using fallback", day)
        return video_dir / f"day{day}.mp4"
    else:
        # Desktop/Android version
        desktop_path = video_dir / f"day{day}_desktop.mp4"
        if desktop_path.exists():
            logging.info("Desktop: using day%d_desktop.mp4", day)
            return desktop_path
        
        compressed_path = video_dir / f"day{day}_compressed.mp4"
        if compressed_path.exists():
            logging.info("Desktop: using day%d_compressed.mp4", day)
            return compressed_path
        
        # Final fallback
        logging.info("Desktop: using day%d.mp4 (fallback)", day)
        return video_dir / f"day{day}.mp4"

async def _send_video(user_id: int, day: int, video_path: Path, platform: str = "desktop") -> None:
    """Send video to user with caching"""
    try:
        logging.info(
            "Sending video for user %s, day %d, platform: %s, path: %s", 
            user_id, day, platform, video_path.name
        )
        
        # Try to use cached file_id first
        cache_key = f"{day}_{platform}"
        cached_id = get_video_file_id(cache_key)
        if cached_id:
            logging.info("Using cached file_id for %s", cache_key)
            await bot.send_chat_action(user_id, "upload_video")
            await bot.send_video(user_id, cached_id, supports_streaming=True)
            return
        
        # Send new video and cache file_id
        logging.info("Sending new video for %s", cache_key)
        await bot.send_chat_action(user_id, "upload_video")
        
        # Get video dimensions for proper aspect ratio
        try:
            width, height = get_video_dimensions(str(video_path))
            msg = await bot.send_video(user_id, InputFile(str(video_path)), supports_streaming=True, width=width, height=height)
        except Exception as e:
            logging.warning("Failed to get video dimensions, sending without: %s", e)
            msg = await bot.send_video(user_id, InputFile(str(video_path)), supports_streaming=True)
        
        # Save video file_id
        if msg and msg.video and msg.video.file_id:
            logging.info("Saving video file_id")
            save_video_file_id(cache_key, msg.video.file_id)
        
    except NetworkError as e:
        logging.exception("send_video day%02d failed for user %s: %s", day, user_id, e)
        await bot.send_message(user_id, ERROR_MESSAGE)
    except Exception as e:
        logging.exception("send_video day%02d failed for user %s: %s", day, user_id, e)
        await bot.send_message(user_id, ERROR_MESSAGE)

async def _send_end_message(user_id: int, base_dir: Path) -> None:
    """Send end message if exists"""
    try:
        end_path = base_dir / "messages" / "dayN_end.txt"
        if end_path.exists():
            end_text = end_path.read_text(encoding="utf-8")
            await bot.send_message(user_id, end_text)
    except Exception as e:
        logging.exception("send dayN_end failed for user %s: %s", user_id, e)

async def send_daily_message(user_id: int, day: int) -> None:
    """Send daily message and video to user"""
    if day > 6:
        return

    base_dir = Path(__file__).parent
    text_path = base_dir / f"messages/day{day}.txt"
    video_dir = base_dir / "content"
    
    try:
        # Read text message
        if day == 6:
            # Day 6 has two separate messages
            message1 = ("Подписывайтесь на мой канал, чтобы не пропустить новые курсы, прогнозы на неделю, месяц, "
                       "мои интервью в СМИ и новые практики!\n@fengshuichannel")
            message2 = ("Приходите на мой лунный ретрит \"Алхимия Луны\", чтобы исследовать практики по Луне более основательно!\n"
                       "Посмотрите подробности по ссылке\nhttp://onfengshui.ru/moonretreat")
            
            # Send both messages sequentially
            await bot.send_message(user_id, message1)
            await bot.send_message(user_id, message2)
            return  # Exit early for Day 6 as we don't send video
        else:
            with open(text_path, "r", encoding="utf-8") as f:
                text = f.read()
        
        # Get user platform and video path
        user_platform = get_user_platform(user_id)
        logging.info("User %s platform: %s", user_id, user_platform)
        video_path = _get_video_path(day, user_platform, video_dir)
        
        # Send text and video simultaneously using asyncio.gather
        
        # Prepare both tasks
        text_task = bot.send_message(user_id, text)
        video_task = _send_video(user_id, day, video_path, user_platform)
        
        # Execute both simultaneously
        await asyncio.gather(text_task, video_task)

        # Send end message for days 1-4
        if 1 <= day <= 4:
            await _send_end_message(user_id, base_dir)
        
        # Schedule follow-up after day 5
        if day == 5:
            run_at = datetime.utcnow() + timedelta(days=1)
            try:
                scheduler.add_job(
                    send_daily_message,
                    trigger="date",
                    run_date=run_at,
                    args=[user_id, 6],
                    id=f"{user_id}_day6",
                    replace_existing=True,
                )
            except Exception as e:
                logging.exception("schedule day 6 failed for user %s: %s", user_id, e)
                
    except Exception as e:
        logging.exception("send_daily_message failed for user %s: %s", user_id, e)
        try:
            await bot.send_message(user_id, ERROR_MESSAGE)
        except Exception:
            pass

async def schedule_user_messages(user_id: int, tz_name: str, hour: int = 15, minute: int = 0) -> None:
    """Schedule daily messages for user at specified time"""
    now_utc = datetime.utcnow()
    
    for i in range(2, 6):
        run_utc = local_15_to_utc(now_utc, tz_name, day_offset=i-1, hour=hour, minute=minute)
        
        try:
            scheduler.add_job(
                send_daily_message,
                trigger="date",
                run_date=run_utc,
                args=[user_id, i],
                id=f"{user_id}_{i}",
                replace_existing=True,
            )
        except Exception as e:
            logging.exception("Failed to schedule day %d for user %s: %s", i, user_id, e)