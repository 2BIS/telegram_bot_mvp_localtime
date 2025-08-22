import logging
import asyncio
from pathlib import Path

from aiogram import types
from aiogram.types import InputFile
from aiogram.utils import executor

from bot import dp, bot, ADMIN_CHAT_ID
from handlers import register_handlers
from scheduler import scheduler
from storage import get_video_file_id, save_video_file_id

# Register handlers
register_handlers(dp)

async def _preload_video(day: int, video_dir: Path, platform: str = "desktop") -> None:
    """Preload video file_id for specific day and platform"""
    # Check if already cached for this platform
    cache_key = f"{day}_{platform}"
    if get_video_file_id(cache_key):
        return  # Already cached
    
    # Try different video versions based on platform
    if platform == "ios":
        video_paths = [
            video_dir / "ios" / f"ios_day{day}.mp4",
            video_dir / f"day{day}.mp4"  # fallback
        ]
    else:
        video_paths = [
            video_dir / f"day{day}_desktop.mp4",
            video_dir / f"day{day}_compressed.mp4",
            video_dir / f"day{day}.mp4"
        ]
    
    video_path = None
    for path in video_paths:
        if path.exists():
            video_path = path
            break
    
    if not video_path:
        return  # No video found
    
    try:
        await bot.send_chat_action(ADMIN_CHAT_ID, "upload_video")
        
        if platform == "ios":
            # For iOS, send as audio to avoid automatic conversion
            try:
                msg = await bot.send_audio(
                    ADMIN_CHAT_ID,
                    InputFile(str(video_path)),
                    disable_notification=True,
                    caption=f"preload day {day} (iOS)",
                    title=f"Day {day}",
                    performer="BaZi Bot"
                )
                
                if msg and msg.audio and msg.audio.file_id:
                    save_video_file_id(cache_key, msg.audio.file_id)
            except Exception as audio_error:
                logging.warning("Audio preload failed for iOS day %s, falling back to document: %s", day, audio_error)
                # Fallback to document
                msg = await bot.send_document(
                    ADMIN_CHAT_ID,
                    InputFile(str(video_path)),
                    disable_notification=True,
                    caption=f"preload day {day} (iOS)",
                )
                
                if msg and msg.document and msg.document.file_id:
                    save_video_file_id(cache_key, msg.document.file_id)
        else:
            # For desktop, send as video
            msg = await bot.send_video(
                ADMIN_CHAT_ID,
                InputFile(str(video_path)),
                supports_streaming=True,
                disable_notification=True,
                caption=f"preload day {day} (desktop)",
            )
            
            if msg and msg.video and msg.video.file_id:
                save_video_file_id(cache_key, msg.video.file_id)
            
    except Exception as e:
        logging.exception("preload day %s for %s failed: %s", day, platform, e)

async def on_startup(dp) -> None:
    """Bot startup handler"""
    # Set bot commands
    await bot.set_my_commands([
        types.BotCommand("start", "Запустить бота"),
    ])
    
    # Preload video file_ids for first user
    if ADMIN_CHAT_ID:
        try:
            print("🚀 Starting bot...")
            print("📹 Preloading video files...")
            
            base_dir = Path(__file__).parent
            video_dir = base_dir / "content"
            
            # Preload all days simultaneously
            preload_tasks = []
            
            for day in range(1, 6):
                # Preload for both platforms
                task_desktop = _preload_video(day, video_dir, "desktop")
                task_ios = _preload_video(day, video_dir, "ios")
                preload_tasks.append(task_desktop)
                preload_tasks.append(task_ios)
            
            # Execute all preloads simultaneously
            results = await asyncio.gather(*preload_tasks, return_exceptions=True)
            
            # Check results
            success_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ Preload error for day {i//2+1}: {result}")
                else:
                    success_count += 1
            
            print(f"✅ Preload complete: {success_count}/5 days successfully loaded")
            
        except Exception as e:
            logging.exception("on_startup preload failed: %s", e)
            print(f"❌ Startup error: {e}")
    
    print("🤖 Bot is ready!")

if __name__ == "__main__":
    scheduler.start()
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)