import platform
import requests
import zipfile
import tarfile
import shutil
import itertools
import time
from pathlib import Path
import os
import sys
from PyQt5.QtCore import QThread, pyqtSignal

class DownloadFFmpegThread(QThread):
    update_progress_signal = pyqtSignal(int)  # For the progress bar
    update_status_signal = pyqtSignal(str)    # For status messages
    ffmpeg_complete_signal = pyqtSignal()     # Signal when FFmpeg is ready

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._spinner_running = False

    def run(self):
        """Download FFmpeg and update the progress bar."""
        try:
            # Get the root directory of the running application, regardless of PyInstaller or regular execution
            if getattr(sys, 'frozen', False):
                # If running in a PyInstaller bundle
                root_dir = Path(sys.executable).parent
            else:
                # If running as a regular Python script
                root_dir = Path(os.path.dirname(os.path.abspath(__file__)))

            # Define the path where ffmpeg will be downloaded and extracted
            ffmpeg_dir = root_dir / "ffmpeg"
            ffmpeg_executable = ffmpeg_dir / "ffmpeg.exe" if platform.system() == "Windows" else ffmpeg_dir / "ffmpeg"

            # Check if FFmpeg is already downloaded
            if ffmpeg_executable.exists():
                # Set FFmpeg in the environment
                os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ["PATH"]
                self.update_status_signal.emit("FFmpeg is already installed.")
                self.ffmpeg_complete_signal.emit()
                return

            self.update_status_signal.emit("Downloading dependency: ffmpeg")

            # URLs for different platforms
            if platform.system() == "Windows":
                url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                zip_name = "ffmpeg-release-essentials.zip"
            elif platform.system() == "Darwin":  # macOS
                url = "https://evermeet.cx/ffmpeg/getrelease/zip"
                zip_name = "ffmpeg-macos.zip"
            elif platform.system() == "Linux":
                url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz"
                zip_name = "ffmpeg-release-linux.tar.xz"
            else:
                raise RuntimeError(f"Unsupported OS: {platform.system()}")

            # Create ffmpeg directory if it doesn't exist
            ffmpeg_dir.mkdir(exist_ok=True)
            zip_path = ffmpeg_dir / zip_name

            # Download FFmpeg
            with requests.get(url, stream=True) as r:
                total_size = int(r.headers.get('content-length', 0))
                chunk_size = 1024
                downloaded_size = 0

                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            progress_percent = int((downloaded_size / total_size) * 100)
                            self.update_progress_signal.emit(progress_percent)
                            self.update_status_signal.emit(f"Downloading ffmpeg...")

            # Start the spinner in a separate thread
            self._spinner_running = True
            spinner_thread = QThread()
            spinner_thread.run = self.start_spinner
            spinner_thread.start()

            # Extract FFmpeg
            self.update_status_signal.emit("Extracting FFmpeg...")
            if platform.system() == "Windows":
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(ffmpeg_dir)
                ffmpeg_bin_dir = next(ffmpeg_dir.glob("*/bin"))  # Find bin folder in extracted contents
                shutil.move(ffmpeg_bin_dir / "ffmpeg.exe", ffmpeg_executable)

            elif platform.system() == "Darwin":
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(ffmpeg_dir)
                shutil.move(ffmpeg_dir / "ffmpeg", ffmpeg_executable)

                # Add this line to give execute permission
                ffmpeg_executable.chmod(0o755)

            elif platform.system() == "Linux":
                with tarfile.open(zip_path, 'r:xz') as tar_ref:
                    tar_ref.extractall(ffmpeg_dir)
                ffmpeg_bin_dir = next(ffmpeg_dir.glob("*/ffmpeg"))
                shutil.move(ffmpeg_bin_dir, ffmpeg_executable)

                # Add this line to give execute permission
                ffmpeg_executable.chmod(0o755)

            # Stop the spinner once extraction is done
            self._spinner_running = False
            spinner_thread.wait()

            # Clean up the archive
            zip_path.unlink()

            # Set FFmpeg in the environment
            os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ["PATH"]

            self.update_status_signal.emit("FFmpeg setup completed.")
            self.ffmpeg_complete_signal.emit()

        except Exception as e:
            print(f"Error during ffmpeg download: {e}", file=sys.stderr)
            self.update_status_signal.emit(f"Error: {str(e)}")

    def start_spinner(self):
        """Show spinner animation in the status bar while extraction is running."""
        spinner = itertools.cycle(["|",
                                   "/",
                                   "–",
                                   "\\"])
        while self._spinner_running:
            self.update_status_signal.emit(f"Extracting FFmpeg... {next(spinner)}")
            time.sleep(0.2)
