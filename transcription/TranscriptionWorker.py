import os
import sys
import whisper
import datetime
import itertools
import time
import csv
import subprocess
from datetime import datetime
from .normalize_path import normalize_path
from PyQt5.QtCore import QThread, pyqtSignal

# Global lists for supported formats
AUDIO_FORMATS = ["mp3", "wav", "flac", "m4a", "ogg"]
VIDEO_FORMATS = ["mp4", "webm", "mov", "avi", "mkv", "flv", "wmv", "mpeg", "mpg", "3gp", "asf"]

# Monkey patching to suppress console windows for all subprocess
#                 __------__
#               /~          ~\
#              |    //^\\//^\|
#            /~~\  ||  o| |o|:~\
#           | |6   ||___|_|_||:|
#            \__.  /      o  \/'
#             |   (       O   )
#    /~~~~\    `\  \         /
#   | |~~\ |     )  ~------~`\
#  /' |  | |   /     ____ /~~~)\
# (_/'   | | |     /'    |    ( |
#        | | |     \    /   __)/ \
#        \  \ \      \/    /' \   `\
#          \  \|\        /   | |\___|
#            \ |  \____/     | |
#            /^~>  \        _/ <
#           |  |         \       \
#           |  | \        \        \
#           -^-\  \       |        )
#                `\_______/^\______/

def no_console_popen(*args, **kwargs):
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return original_popen(*args, **kwargs)

def no_console_call(*args, **kwargs):
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return original_call(*args, **kwargs)

def no_console_run(*args, **kwargs):
    # Set creationflags to suppress the console window
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return original_run(*args, **kwargs)

# Keep references to the original subprocess functions
original_run = subprocess.run
original_popen = subprocess.Popen
original_call = subprocess.call

# Override subprocess functions
subprocess.run = no_console_run
subprocess.Popen = no_console_popen
subprocess.call = no_console_call


# End of monkey patching
# End of monkey patching
# End of monkey patching



class TranscriptionWorker(QThread):
    update_status_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)
    transcription_complete_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, input_folder, output_folder, model_name, include_timestamps, output_format, parent=None):
        super().__init__(parent)
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.model_name = model_name
        self.include_timestamps = include_timestamps
        self.output_format = output_format

        # Create "conversions" folder for temporary wav files
        self.conversions_folder = "conversions"
        os.makedirs(self.conversions_folder, exist_ok=True)

    def run(self):
        try:
            self._spinner_running = True
            spinner_thread = QThread()
            spinner_thread.run = self.start_spinner
            spinner_thread.start()

            model_dir = normalize_path("whisper_models")
            os.makedirs(model_dir, exist_ok=True)

            model = whisper.load_model(self.model_name, download_root=model_dir)

            self._spinner_running = False
            spinner_thread.wait()

            self.update_status_signal.emit("Model loaded successfully.")

            files_to_process = self.list_files_with_extensions(self.input_folder)
            total_files = len(files_to_process)

            if self.output_format == "csv":
                csv_filename = self.get_csv_filename()
                csv_filepath = os.path.join(self.output_folder, csv_filename)

                with open(normalize_path(csv_filepath), mode='w', newline='', encoding='utf-8-sig') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    header = ['filename', 'start_time', 'stop_time', 'text'] if self.include_timestamps else ['filename', 'text']
                    csv_writer.writerow(header)

                    for i, input_file in enumerate(files_to_process):
                        self.process_and_transcribe_file(input_file, csv_writer, model)
                        overall_progress = int((i + 1) / total_files * 100)
                        self.update_progress_signal.emit(overall_progress)
            else:
                for i, input_file in enumerate(files_to_process):
                    self.process_and_transcribe_file(input_file, None, model)
                    overall_progress = int((i + 1) / total_files * 100)
                    self.update_progress_signal.emit(overall_progress)

            self.transcription_complete_signal.emit()

        except Exception as e:
            print(f"Error during transcription: {e}", file=sys.stderr)
            self.error_signal.emit(f"Error during transcription: {e}")

    def process_and_transcribe_file(self, input_file, csv_writer, model):
        self.update_status_signal.emit(f"Processing file: {os.path.basename(input_file)}")

        if any(input_file.lower().endswith(ext) for ext in VIDEO_FORMATS):  # Check if it's a video file
            temp_wav_file = os.path.join(self.conversions_folder, "temp_audio.wav")
            self.convert_to_wav(input_file, temp_wav_file)
            result = model.transcribe(temp_wav_file, verbose=False)
            os.remove(temp_wav_file)  # Clean up temporary file
        else:
            result = model.transcribe(input_file, verbose=False)

        self.write_transcription(result, input_file, csv_writer)

    def convert_to_wav(self, input_file, output_wav_file):
        command = ["ffmpeg", "-i", input_file, "-ar", "16000", "-ac", "1", output_wav_file]
        subprocess.run(
            command,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=False,
            creationflags=CREATE_NO_WINDOW if os.name == 'nt' else 0  # Apply only on Windows
        )

    def write_transcription(self, result, input_file, csv_writer):
        if csv_writer:
            for segment in result['segments']:
                start_time = segment['start']
                end_time = segment['end']
                text = segment['text'].strip()
                if self.include_timestamps:
                    csv_writer.writerow([os.path.basename(input_file), start_time, end_time, text])
                else:
                    csv_writer.writerow([os.path.basename(input_file), text])
        else:
            output_file_path = os.path.join(self.output_folder, os.path.basename(input_file) + ".txt")
            with open(normalize_path(output_file_path), 'w', encoding='utf-8-sig') as output_file:
                for segment in result['segments']:
                    start_time = segment['start']
                    end_time = segment['end']
                    text = segment['text'].strip()
                    if self.include_timestamps:
                        output_file.write(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}\n")
                    else:
                        output_file.write(f"{text}\n")

    def get_csv_filename(self):
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{now} - Whispering Wizard Output.csv"

    def list_files_with_extensions(self, folder_path: str) -> list:
        file_list = []
        supported_extensions = AUDIO_FORMATS + VIDEO_FORMATS  # Combine audio and video formats
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_extensions):
                    file_list.append(os.path.join(root, file))
        return file_list

    def start_spinner(self):
        """Show spinner animation in the status bar while downloading model."""
        spinner = itertools.cycle(["|", "/", "–", "\\"])
        while self._spinner_running:
            self.update_status_signal.emit(f"Downloading/loading model: {self.model_name}... {next(spinner)}")
            time.sleep(0.2)
