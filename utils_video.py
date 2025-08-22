#!/usr/bin/env python3
"""
Утилиты для работы с видео
"""

import subprocess
from pathlib import Path
from typing import Tuple, Optional


def get_video_dimensions(video_path: str) -> tuple:
    """Retrieve the width and height of a video using ffprobe."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=s=,:p=0',
        video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error: {result.stderr}")
    width, height = map(int, result.stdout.strip().split(','))
    return width, height

def get_video_duration(video_path: Path) -> Optional[float]:
    """Получить длительность видео в секундах"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=duration",
            "-of", "csv=p=0",
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        
        if output:
            return float(output)
        
        return None
        
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None

def is_video_compatible_for_ios(video_path: Path) -> bool:
    """Проверяет, совместимо ли видео для iOS"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,pix_fmt",
            "-of", "csv=p=0",
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        
        if output:
            codec, pix_fmt = output.split(',')
            # Проверяем H.264 кодек и YUV420p цветовое пространство
            # Убираем строгую проверку профиля для большей гибкости
            return (codec == "h264" and pix_fmt == "yuv420p")
        
        return False
        
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return False
