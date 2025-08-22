import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Function to get video duration in seconds
def get_duration_seconds(path: Path) -> Optional[float]:
    """Get the duration of a video file in seconds."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        return None
    return float(result.stdout.strip())

# Function to get video rotation in degrees
def get_rotation_degrees(path: Path) -> int:
    """Get the rotation of a video file in degrees."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream_tags=rotate',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        return 0
    return int(result.stdout.strip())

# Function to get video dimensions
def get_dimensions(path: Path) -> Optional[Tuple[int, int]]:
    """Get the width and height of a video file."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=s=,:p=0',
        str(path)
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        return None
    width, height = map(int, result.stdout.strip().split(','))
    return width, height

# Function to compress video
def compress_video(src: Path, dst: Path) -> bool:
    """Compress video to a smaller size."""
    try:
        subprocess.run([
            'ffmpeg', '-i', str(src), '-vf', 'scale=1280:720', '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '23', '-c:a', 'aac', '-b:a', '128k', str(dst)
        ], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# Main function to compress videos
def main():
    """Main function to compress videos."""
    video_dir = Path('content')
    output_dir = video_dir / 'compressed'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Compress each video in the content directory
    for video_file in video_dir.glob('*.mp4'):
        dst = output_dir / video_file.name

        if compress_video(video_file, dst):
            print(f'Successfully compressed {video_file.name}')
        else:
            print(f'Failed to compress {video_file.name}')

if __name__ == '__main__':
    main()
