import os
import sys
import whisper
import datetime
import itertools
import time
import csv
from datetime import datetime
from .normalize_path import normalize_path
from PyQt5.QtCore import QThread, pyqtSignal


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

    def run(self):
        try:
            file_extensions = ["mp3", "wav", "flac", "m4a", "ogg", "mp4", "webm"]

            self._spinner_running = True
            spinner_thread = QThread()
            spinner_thread.run = self.start_spinner
            spinner_thread.start()

            # Define the custom directory for models
            model_dir = normalize_path("whisper_models")
            os.makedirs(model_dir, exist_ok=True)

            # Load the model from the custom directory
            model = whisper.load_model(self.model_name, download_root=model_dir)

            # Stop the spinner once the model is downloaded
            self._spinner_running = False
            spinner_thread.wait()

            self.update_status_signal.emit("Model loaded successfully.")

            files_to_process = self.list_files_with_extensions(self.input_folder, file_extensions)

            total_files = len(files_to_process)

            if self.output_format == "csv":
                csv_filename = self.get_csv_filename()
                csv_filepath = os.path.join(self.output_folder, csv_filename)

                try:
                    with open(normalize_path(csv_filepath), mode='w', newline='', encoding='utf-8-sig') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        header = ['filename', 'start_time', 'stop_time', 'text'] if self.include_timestamps else ['filename', 'text']
                        csv_writer.writerow(header)

                        for i, input_file in enumerate(files_to_process):
                            self.update_status_signal.emit(f"Transcribing file: {os.path.basename(input_file)}")

                            #temp_wav_file = os.path.join("mediator", "output.wav")
                            #ffmpeg_tools.ffmpegPreprocessing.convert_to_wav(input_file=input_file, output_file=temp_wav_file)
                            #result = model.transcribe(temp_wav_file, verbose=False)
                            #ffmpeg_tools.ffmpegPreprocessing.cleanup_file(temp_wav_file)
                            result = model.transcribe(input_file, verbose=False)

                            for segment in result['segments']:
                                start_time = segment['start']
                                end_time = segment['end']
                                text = segment['text'].strip()

                                if self.include_timestamps:
                                    csv_writer.writerow([os.path.basename(input_file), start_time, end_time, text])
                                else:
                                    csv_writer.writerow([os.path.basename(input_file), text])

                            overall_progress = int((i + 1) / total_files * 100)
                            self.update_progress_signal.emit(overall_progress)
                except Exception as e:
                    print(input_file)
                    #raise e
                    print(f"Error during transcription: {e}", file=sys.stderr)
                    self.error_signal.emit(f"Error writing to output folder: {e}")
                    return
            else:
                for i, input_file in enumerate(files_to_process):

                    self.update_status_signal.emit(f"Transcribing file: {os.path.basename(input_file)}")

                    # temp_wav_file = os.path.join("mediator", "output.wav")
                    # ffmpeg_tools.ffmpegPreprocessing.convert_to_wav(input_file=input_file, output_file=temp_wav_file)
                    # result = model.transcribe(temp_wav_file, verbose=False)
                    # ffmpeg_tools.ffmpegPreprocessing.cleanup_file(temp_wav_file)
                    result = model.transcribe(input_file, verbose=False)

                    output_file_path = os.path.join(self.output_folder, os.path.basename(input_file) + ".txt")
                    try:
                        with open(normalize_path(output_file_path), 'w', encoding='utf-8-sig') as output_file:
                            for segment in result['segments']:
                                start_time = segment['start']
                                end_time = segment['end']
                                text = segment['text'].strip()
                                if self.include_timestamps:
                                    output_file.write(f"[{start_time:.2f}s - {end_time:.2f}s]: {text}\n")
                                else:
                                    output_file.write(f"{text}\n")
                    except Exception as e:
                        print(input_file)
                        #raise e
                        print(f"Error during transcription: {e}", file=sys.stderr)
                        self.error_signal.emit(f"Error writing to output folder: {e}")
                        return

                    overall_progress = int((i + 1) / total_files * 100)
                    self.update_progress_signal.emit(overall_progress)

            self.transcription_complete_signal.emit()

        except Exception as e:
            #raise e
            print(f"Error during transcription: {e}", file=sys.stderr)
            self.error_signal.emit(f"Error during transcription: {e}")

    def get_csv_filename(self):
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{now} - Whispering Wizard Output.csv"

    def list_files_with_extensions(self, folder_path: str, file_extensions: list) -> list:
        file_list = []
        file_extensions = [ext.lower() for ext in file_extensions]
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in file_extensions):
                    file_list.append(os.path.join(root, file))
        return file_list

    def start_spinner(self):
        """Show spinner animation in the status bar while downloading model."""
        spinner = itertools.cycle(["|", "/", "–", "\\"])
        while self._spinner_running:
            self.update_status_signal.emit(f"Downloading/loading model: {self.model_name}... {next(spinner)}")
            time.sleep(0.2)