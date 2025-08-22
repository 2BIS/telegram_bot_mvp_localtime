import subprocess
import os
from pathlib import Path

# Function to create iOS-compatible video
def create_ios_video(input_file: str, output_file: str):
    """Create an iOS-compatible video file."""
    command = [
        'ffmpeg',
        '-i', input_file,
        '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1',
        '-c:v', 'libx264',
        '-profile:v', 'baseline',
        '-level', '3.0',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        output_file
    ]
    subprocess.run(command, check=True)

# Main function to create iOS videos
def main():
    """Main function to create iOS-compatible videos."""
    video_dir = Path('content')
    ios_dir = video_dir / 'ios'

    # Ensure output directory exists
    ios_dir.mkdir(parents=True, exist_ok=True)

    # Create iOS-compatible version for each video
    for video_file in video_dir.glob('*.mp4'):
        output_file = ios_dir / video_file.name
        create_ios_video(str(video_file), str(output_file))
        print(f'Created iOS-compatible video: {output_file.name}')

if __name__ == '__main__':
    main()
