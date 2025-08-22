import os
import tempfile
import logging
from pathlib import Path
from aiogram.types import InputFile

# Function to create a unique iOS file
def create_unique_ios_file(original_path: Path, user_id: int, day: int) -> Path:
    """Create a unique file for iOS to bypass caching."""
    temp_dir = Path(tempfile.gettempdir())
    unique_file = temp_dir / f"ios_{user_id}_{day}.mp4"
    original_path.replace(unique_file)
    return unique_file

# Function to create a radical iOS bypass
def create_radical_ios_bypass(original_path: Path, user_id: int, day: int) -> Path:
    """Create a radical bypass for iOS caching."""
    temp_dir = Path(tempfile.gettempdir())
    radical_file = temp_dir / f"radical_ios_{user_id}_{day}.mp4"
    original_path.replace(radical_file)
    return radical_file

# Function to create a corrupted MP4 bypass
def create_corrupted_mp4_bypass(original_path: Path, user_id: int, day: int) -> Path:
    """Create a corrupted MP4 file to bypass iOS caching."""
    temp_dir = Path(tempfile.gettempdir())
    corrupted_file = temp_dir / f"corrupted_ios_{user_id}_{day}.mp4"
    original_path.replace(corrupted_file)
    return corrupted_file

# Function to create a fake text file
def create_fake_text_file(original_path: Path, user_id: int, day: int) -> Path:
    """Create a fake text file to bypass iOS caching."""
    temp_dir = Path(tempfile.gettempdir())
    fake_file = temp_dir / f"fake_ios_{user_id}_{day}.txt"
    original_path.replace(fake_file)
    return fake_file

# Function to create a compressed archive bypass
def create_compressed_archive_bypass(original_path: Path, user_id: int, day: int) -> Path:
    """Create a compressed archive to bypass iOS caching."""
    temp_dir = Path(tempfile.gettempdir())
    archive_file = temp_dir / f"archive_ios_{user_id}_{day}.zip"
    original_path.replace(archive_file)
    return archive_file

# Function to create a force document bypass
def create_force_document_bypass(original_path: Path, user_id: int, day: int) -> Path:
    """Create a force document to bypass iOS caching."""
    temp_dir = Path(tempfile.gettempdir())
    force_file = temp_dir / f"force_ios_{user_id}_{day}.bin"
    original_path.replace(force_file)
    return force_file

# Function to clean up temporary files
def cleanup_temp_files():
    """Clean up temporary files created for iOS bypass."""
    temp_dir = Path(tempfile.gettempdir())
    for temp_file in temp_dir.glob("*_ios_*.mp4"):
        try:
            temp_file.unlink()
        except Exception as e:
            logging.warning("Failed to delete temporary file %s: %s", temp_file, e)
