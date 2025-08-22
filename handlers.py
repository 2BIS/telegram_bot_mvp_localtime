import logging
import asyncio
from datetime import datetime
from pathlib import Path

from aiogram import Dispatcher, types
from aiogram.types import InputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.exceptions import NetworkError

from bot import bot, ADMIN_CHAT_ID
from scheduler import schedule_user_messages
from storage import (
    save_user_tz, save_user_init, save_survey_answer, 
    get_video_file_id, save_video_file_id, 
    save_user_platform, get_user_platform, auto_detect_platform,
    get_user_data
)
from utils_time import tz_from_city_name
from utils_video import get_video_dimensions

# Constants
ERROR_MESSAGE = "Произошла ошибка. Свяжитесь, пожалуйста, с администратором бота: @aspronea"

async def _notify_admin_new_user(user_id: int, username: str, init_ts: str, survey_answer: str, user: types.User) -> None:
    """Notify admin about new user with survey answer"""
    logging.info("_notify_admin_new_user called: user_id=%s, ADMIN_CHAT_ID=%s", user_id, ADMIN_CHAT_ID)
    
    if not ADMIN_CHAT_ID:
        logging.warning("ADMIN_CHAT_ID is not set, cannot notify admin")
        return
    
    try:
        import pytz
        from datetime import datetime
        
        if user.username:
            profile = f"@{user.username}"
        else:
            profile = f"{user.first_name or ''} {user.last_name or ''}".strip()
        
        # Convert UTC timestamp to Moscow time
        moscow_tz = pytz.timezone('Europe/Moscow')
        utc_time = datetime.fromisoformat(init_ts.replace('Z', '+00:00'))
        moscow_time = utc_time.astimezone(moscow_tz)
        moscow_time_str = moscow_time.strftime("%Y-%m-%d %H:%M:%S")
        
        text = (
            "Новый пользователь запустил бота\n"
            f"Telegram ID: {user_id}\n"
            f"Профиль: {profile}\n"
            f"Время (Москва): {moscow_time_str}\n"
            f"Давно ли читает: {survey_answer}"
        )
        await bot.send_message(ADMIN_CHAT_ID, text)
    except Exception as e:
        logging.warning("Failed to notify admin about new user: %s", e)

# Keyboard layouts

def yes_no_keyboard() -> ReplyKeyboardMarkup:
    """Create yes/no survey keyboard"""
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton(text="Давно"), KeyboardButton(text="Я новенький(-ая)"))
    return kb

# Main command handlers
async def start_command(message: types.Message) -> None:
    """Handle /start command"""
    user_id = message.from_user.id
    user = message.from_user
    
    # Get username
    username = (
        user.username
        or " ".join(filter(None, [user.first_name, user.last_name]))
        or str(user.id)
    )
    
    # Save initialization data
    init_ts = datetime.utcfromtimestamp(message.date.timestamp()).strftime("%Y-%m-%dT%H:%M:%SZ")
    is_new = save_user_init(user_id, username, init_ts)
    
    # Auto-detect platform
    detected_platform = auto_detect_platform(message)
    save_user_platform(user_id, detected_platform)

    # Store if user is new for later notification after survey
    # Notification will be sent after survey response

    # Send survey question
    question_text = (
        f"Привет, {username}!\n"
        f"Очень приятно видеть Вас здесь!\n\n"
        f"Давно ли Вы читаете мой блог?"
    )
    await message.answer(question_text, reply_markup=yes_no_keyboard())

async def _send_day1_package(message: types.Message) -> None:
    """Send day 1 content package"""
    base_dir = Path(__file__).parent
    user_id = message.from_user.id

    try:
        # Send text message and video simultaneously
        user_platform = get_user_platform(user_id)
        logging.info("User %s platform: %s", user_id, user_platform)
        video_dir = base_dir / "content"
        
        # Select video based on platform
        if user_platform == "ios":
            video_path = video_dir / "ios" / "ios_day1.mp4"
            if not video_path.exists():
                video_path = video_dir / "day1.mp4"  # fallback
        else:
            video_path = video_dir / "day1_desktop.mp4"
            if not video_path.exists():
                video_path = video_dir / "day1.mp4"  # fallback
        
        # Read text message
        with open(base_dir / "messages" / "day1.txt", "r", encoding="utf-8") as f:
            text = f.read()

        # Send text and video simultaneously using asyncio.gather
        
        # Prepare both tasks
        text_task = message.answer(text, reply_markup=ReplyKeyboardRemove())
        video_task = _send_video_async(message, video_path, user_platform)
        
        # Execute both simultaneously
        results = await asyncio.gather(text_task, video_task, return_exceptions=True)
        
        # Check results
        text_result = results[0]
        video_result = results[1]
        
        # Handle video result
        if isinstance(video_result, Exception):
            logging.exception("Video sending failed: %s", video_result)
            await message.answer("Видео не удалось отправить, но текст доставлен.")
        elif (video_result and hasattr(video_result, 'video') and 
              video_result.video and video_result.video.file_id):
            # Save video file_id for caching
            save_video_file_id("1_desktop", video_result.video.file_id)
        elif (video_result and hasattr(video_result, 'audio') and 
              video_result.audio and video_result.audio.file_id):
            # Save audio file_id for iOS
            save_video_file_id("1_ios", video_result.audio.file_id)
        elif (video_result and hasattr(video_result, 'document') and 
              video_result.document and video_result.document.file_id):
            # Save document file_id for iOS (fallback)
            save_video_file_id("1_ios", video_result.document.file_id)
        

        
    except Exception as e:
        logging.exception("_send_day1_package failed: %s", e)
        await message.answer(ERROR_MESSAGE)
    
    # Send end message if exists
    try:
        end_path = base_dir / "messages" / "dayN_end.txt"
        if end_path.exists():
            end_text = end_path.read_text(encoding="utf-8")
            await message.answer(end_text)
    except Exception as e:
        logging.exception("send day1_end failed: %s", e)
    
    # Ask for city name after end message
    try:
        await message.answer(
            "И ещё один важный момент. Чтобы Вам было комфортно получать сообщения в течение курса, "
            "пожалуйста, напишите название города, в котором Вы проживаете и мы автоматически определим "
            "Ваш часовой пояс - сообщения будут приходить ровно в 15:00 по Вашему времени.\n\n"
            "Пожалуйста, напишите название города корректно и полностью, это важно!"
        )
    except Exception as e:
        logging.exception("send timezone request failed: %s", e)

async def _send_video_async(message: types.Message, video_path: Path, user_platform: str):
    """Send video asynchronously based on platform"""
    try:
        logging.info("_send_video_async: platform=%s, path=%s", user_platform, video_path.name)
        await message.answer_chat_action("upload_video")
        
        # For iOS, send as document to avoid automatic conversion
        if user_platform == "ios":
            logging.info("iOS: sending as document")
            return await message.bot.send_document(
                message.chat.id,
                InputFile(str(video_path)),
                caption=f"День 1 - видео (iOS версия, бинарный файл)",
                disable_content_type_detection=True  # Принудительно отключаем автоопределение типа
            )
        else:
            # For other platforms, send as video
            width, height = get_video_dimensions(str(video_path))
            return await message.answer_video(InputFile(str(video_path)), supports_streaming=True, width=width, height=height)
            
    except Exception as e:
        logging.exception("_send_video_async failed: %s", e)
        raise e

async def yes_command(message: types.Message) -> None:
    """Handle yes survey answer"""
    try:
        user_id = message.from_user.id
        survey_answer = "Да"
        
        # Get user data to check if this is a new user
        user_data = get_user_data(user_id)
        is_new_user = not user_data.get("survey_answer")  # New if no previous survey answer
        
        logging.info("yes_command: user_id=%s, is_new_user=%s, existing_survey=%s", 
                    user_id, is_new_user, user_data.get("survey_answer"))
        
        save_survey_answer(user_id, survey_answer)
        await message.answer("Спасибо!", reply_markup=ReplyKeyboardRemove())
        
        # Notify admin about new user with survey answer
        if is_new_user:
            user_data = get_user_data(user_id)  # Get updated data
            await _notify_admin_new_user(
                user_id, 
                user_data.get("username", ""), 
                user_data.get("init_ts", ""), 
                survey_answer, 
                message.from_user
            )
        
        await _send_day1_package(message)
    except Exception as e:
        logging.exception("yes_command failed for user %s: %s", message.from_user.id, e)
        await message.answer(ERROR_MESSAGE)

async def no_command(message: types.Message) -> None:
    """Handle no survey answer"""
    try:
        user_id = message.from_user.id
        survey_answer = "Нет"
        
        # Get user data to check if this is a new user
        user_data = get_user_data(user_id)
        is_new_user = not user_data.get("survey_answer")  # New if no previous survey answer
        
        logging.info("no_command: user_id=%s, is_new_user=%s, existing_survey=%s", 
                    user_id, is_new_user, user_data.get("survey_answer"))
        
        save_survey_answer(user_id, survey_answer)
        await message.answer("Спасибо!", reply_markup=ReplyKeyboardRemove())
        
        # Notify admin about new user with survey answer
        if is_new_user:
            user_data = get_user_data(user_id)  # Get updated data
            await _notify_admin_new_user(
                user_id, 
                user_data.get("username", ""), 
                user_data.get("init_ts", ""), 
                survey_answer, 
                message.from_user
            )
        
        await _send_day1_package(message)
    except Exception as e:
        logging.exception("no_command failed for user %s: %s", message.from_user.id, e)
        await message.answer(ERROR_MESSAGE)

# Text message handlers for survey
def _is_yes_text(message: types.Message) -> bool:
    """Check if message text indicates yes answer"""
    if not message.text:
        return False
    text = message.text.strip().lower()
    return text in {"/yes", "yes", "да", "давно"}

def _is_no_text(message: types.Message) -> bool:
    """Check if message text indicates no answer"""
    if not message.text:
        return False
    text = message.text.strip().lower()
    return text in {"/no", "no", "нет", "я новенький(-ая)", "я новенький", "я новенькая"}

# Timezone setting handlers

async def on_city_name(message: types.Message) -> None:
    """Handle city name input to determine timezone"""
    city = message.text.strip()
    tz_name = tz_from_city_name(city)
    
    if not tz_name:
        await message.answer(
            "Не удалось определить часовой пояс по названию города. "
            "Попробуйте указать крупный город или латиницей."
        )
        return
    
    save_user_tz(message.from_user.id, tz_name)
    await message.answer(
        f"Спасибо! Часовой пояс определён: {tz_name}. "
        f"Планирую отправку сообщений на 15:00 Вашего времени."
    )
    await schedule_user_messages(message.from_user.id, tz_name)

# Diagnostic commands
# All diagnostic and testing commands removed for production

# Handler registration
def register_handlers(dp: Dispatcher) -> None:
    """Register all message handlers"""
    # Main commands
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_message_handler(yes_command, commands=["yes"])
    dp.register_message_handler(no_command, commands=["no"])
    
    # Survey text responses (must be before general text handler)
    dp.register_message_handler(yes_command, lambda m: _is_yes_text(m), content_types=["text"])
    dp.register_message_handler(no_command, lambda m: _is_no_text(m), content_types=["text"])
    
    # General text handler for city names (must be last!)
    dp.register_message_handler(on_city_name, content_types=["text"])