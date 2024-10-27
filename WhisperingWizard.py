# These are the primary imports for the application itself
import sys
import os
import ctypes
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox,
                             QPushButton, QFileDialog, QCheckBox, QRadioButton, QButtonGroup, QProgressBar, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from transcription.TranscriptionWorker import TranscriptionWorker
from transcription.normalize_path import normalize_path
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



# Write logs for the application
os.makedirs(normalize_path("logs"), exist_ok=True)
#os.makedirs(normalize_path("mediator"), exist_ok=True)
sys.stdout = open('logs/ww-out.log', 'w', encoding='utf-8-sig')
sys.stderr = open('logs/ww-warn_err.log', 'w')


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

        self.progress_bar.setValue(0)

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
