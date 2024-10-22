# These are the primary imports for the application itself
import traceback
import sys
import os
import ctypes
import itertools
import time
import csv
import whisper
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox,
                             QPushButton, QFileDialog, QCheckBox, QRadioButton, QButtonGroup, QProgressBar, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from ffmpeg_tools.DownloadFFmpeg import DownloadFFmpegThread
#import ffmpeg_tools.ffmpegPreprocessing

# Check if running from a PyInstaller bundle
if hasattr(sys, '_MEIPASS'):
    # When bundled, the icon will be in the _MEIPASS directory, in the _include folder
    icon_path = os.path.join(sys._MEIPASS, 'wizard_icon.ico')
else:
    # When running directly, use the local path
    icon_path = 'wizard_icon.ico'

import os


def normalize_path(path):
    # Normalize slashes according to the operating system
    path = os.path.normpath(path)
    # Add long path prefix for Windows if needed
    if os.name == 'nt' and not path.startswith('\\\\?\\') and len(path) > 260:
        return '\\\\?\\' + os.path.abspath(path)
    return path


# Write logs for the application
os.makedirs(normalize_path("logs"), exist_ok=True)
#os.makedirs(normalize_path("mediator"), exist_ok=True)
sys.stdout = open('logs/ww-out.log', 'w', encoding='utf-8-sig')
sys.stderr = open('logs/ww-warn_err.log', 'w')

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


class TranscriptionApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Whispering Wizard")
        self.setFixedWidth(800)
        self.setMinimumWidth(800)

        layout = QVBoxLayout()

        self.model_label = QLabel("Choose Whisper Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["turbo", "tiny", "base", "small", "medium", "large"])
        layout.addWidget(self.model_label)
        layout.addWidget(self.model_combo)

        input_folder_layout = QHBoxLayout()
        self.input_folder_button = QPushButton("Select Input Folder")
        self.input_folder_button.clicked.connect(self.select_input_folder)
        self.input_folder_label = QLabel("No folder selected")
        self.style_label(self.input_folder_label)
        input_folder_layout.addWidget(self.input_folder_button)
        input_folder_layout.addWidget(self.input_folder_label)
        layout.addLayout(input_folder_layout)

        output_folder_layout = QHBoxLayout()
        self.output_folder_button = QPushButton("Select Output Folder")
        self.output_folder_button.clicked.connect(self.select_output_folder)
        self.output_folder_label = QLabel("No folder selected")
        self.style_label(self.output_folder_label)
        output_folder_layout.addWidget(self.output_folder_button)
        output_folder_layout.addWidget(self.output_folder_label)
        layout.addLayout(output_folder_layout)

        self.timestamp_checkbox = QCheckBox("Include timestamps in transcription")
        layout.addWidget(self.timestamp_checkbox)

        self.output_txt_radio = QRadioButton("Text Files (.txt)")
        self.output_csv_radio = QRadioButton("Single CSV File (.csv)")
        self.output_txt_radio.setChecked(True)
        self.output_type_group = QButtonGroup()
        self.output_type_group.addButton(self.output_txt_radio)
        self.output_type_group.addButton(self.output_csv_radio)
        layout.addWidget(self.output_txt_radio)
        layout.addWidget(self.output_csv_radio)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(QLabel("Overall progress:"))
        layout.addWidget(self.progress_bar)

        self.current_status_label = QLabel("Current Status: Idle")
        layout.addWidget(self.current_status_label)

        self.transcribe_button = QPushButton("Start Transcription")
        self.transcribe_button.clicked.connect(self.start_transcription)
        layout.addWidget(self.transcribe_button)

        self.setLayout(layout)

        # Disable main buttons until FFmpeg setup is complete
        self.input_folder_button.setEnabled(False)
        self.output_folder_button.setEnabled(False)
        self.transcribe_button.setEnabled(False)

        # Start the FFmpeg download in a separate thread after UI initialization
        self.ffmpeg_thread = DownloadFFmpegThread(self)
        self.ffmpeg_thread.update_progress_signal.connect(self.progress_bar.setValue)
        self.ffmpeg_thread.update_status_signal.connect(self.update_status)
        self.ffmpeg_thread.ffmpeg_complete_signal.connect(self.on_ffmpeg_complete)
        self.ffmpeg_thread.start()

    def on_ffmpeg_complete(self):
        """Re-enable UI components when FFmpeg setup is complete."""
        self.update_status("FFmpeg is installed.")
        self.progress_bar.setValue(0)
        self.input_folder_button.setEnabled(True)
        self.output_folder_button.setEnabled(True)

    def update_status(self, message):
        """Update the status message in the status label."""
        self.current_status_label.setText(f"Current Status: {message}")
        self.current_status_label.repaint()  # Force UI to refresh

    def style_label(self, label):
        label.setStyleSheet("border: 1px solid black; padding: 3px;")
        label.setFont(QFont("Arial", 10))
        label.setToolTip("No folder selected")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        label.setWordWrap(False)
        label.setMaximumWidth(400)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Input Folder')
        if folder:
            self.input_folder_label.setText(self.truncate_path(folder))
            self.input_folder_label.setToolTip(folder)
            self.input_folder = folder
            self.check_folders_selected()

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Output Folder')
        if folder:
            self.output_folder_label.setText(self.truncate_path(folder))
            self.output_folder_label.setToolTip(folder)
            self.output_folder = folder
            self.check_folders_selected()

    def check_folders_selected(self):
        """Enable the 'Start Transcription' button only if both input and output folders are selected."""
        if hasattr(self, 'input_folder') and hasattr(self, 'output_folder'):
            self.transcribe_button.setEnabled(True)

    def truncate_path(self, path, max_length=40):
        """Truncate a long file path with an ellipsis."""
        if len(path) > max_length:
            return f"...{path[-max_length:]}"
        return path

    def start_transcription(self):
        self.toggle_ui(False)

        model_name = self.model_combo.currentText()
        include_timestamps = self.timestamp_checkbox.isChecked()
        output_format = "csv" if self.output_csv_radio.isChecked() else "txt"

        input_folder = normalize_path(self.input_folder_label.toolTip())
        output_folder = normalize_path(self.output_folder_label.toolTip())

        if not input_folder or not output_folder:
            self.update_status("Please select both input and output folders.")
            self.toggle_ui(True)
            return

        self.worker = TranscriptionWorker(input_folder, output_folder, model_name, include_timestamps, output_format)
        self.worker.update_status_signal.connect(self.update_status)
        self.worker.update_progress_signal.connect(self.progress_bar.setValue)
        self.worker.error_signal.connect(self.show_error_message)
        self.worker.transcription_complete_signal.connect(self.on_transcription_complete)

        self.worker.start()

    def toggle_ui(self, enable):
        self.model_combo.setEnabled(enable)
        self.input_folder_button.setEnabled(enable)
        self.output_folder_button.setEnabled(enable)
        self.timestamp_checkbox.setEnabled(enable)
        self.output_txt_radio.setEnabled(enable)
        self.output_csv_radio.setEnabled(enable)
        self.transcribe_button.setEnabled(enable)

    def update_status(self, message):
        self.current_status_label.setText(f"Current Status: {message}")
        self.current_status_label.repaint()

    def show_error_message(self, error_message):
        """Show an error message in a dialog box."""
        QMessageBox.critical(self, "Error", error_message)
        self.toggle_ui(True)

    def on_transcription_complete(self):
        self.update_status("Transcription complete!")
        self.toggle_ui(True)

        # Show a message box when transcription is complete
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Transcription Complete")
        msg_box.setText("Transcription complete!")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()  # Display the message box



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set the global application icon (for the taskbar)
    app.setWindowIcon(QIcon(icon_path))
    

    # Explicitly set taskbar icon for Windows using ctypes
    if sys.platform.startswith('win'):
        myappid = 'RyanBoyd.WhisperingWizard'  # Arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    window = TranscriptionApp()
    window.show()
    sys.exit(app.exec_())
