import subprocess
import os
import sys

def convert_to_wav(input_file, output_file):
    """Convert input m4a file to wav using ffmpeg and suppress the console window."""
    # Suppress console window on Windows
    creationflags = 0
    if os.name == 'nt':  # Windows specific
        creationflags = subprocess.CREATE_NO_WINDOW

    cmd = ["ffmpeg", "-nostdin", "-threads", "0", "-i", input_file, output_file]

    # Run ffmpeg without opening a console window
    subprocess.run(cmd, check=True, creationflags=creationflags)

def cleanup_file(file_path):
    """Remove the file after use."""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Removed temporary file: {file_path}")
    else:
        print(f"File not found: {file_path}")