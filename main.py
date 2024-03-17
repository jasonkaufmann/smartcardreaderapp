from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QProcess, Qt, QTimer
import sys

class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.process = QProcess()
        self.auto_run_active = False
        self.current_script = ""
        self.running_dots = 0  # Track the number of dots
        self.running_timer = QTimer(self)  # Timer to update "Running" text
        self.running_timer.setInterval(1000)  # Update every second
        self.running_timer.timeout.connect(self.update_running_text)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.started.connect(self.on_script_start)
        self.process.finished.connect(self.script_finished)
        self.initUI()
        self.script_queue = [
            'take_picture.py',
            'take_video.py',
            'form_fillout.py',
            'get_fingerprint.py',
            'upload_info.py',
            'card_save.py'
        ]
        
    def initUI(self):
        self.setWindowTitle('Execute Python Scripts')
        self.setGeometry(300, 300, 500, 300)
        layout = QVBoxLayout()

        self.status_label = QLabel("Ready", self)
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.updateStatusLabel("Ready", "black")
        layout.addWidget(self.status_label)

        self.script_buttons = {}
        self.original_button_texts = {}
        scripts = [
            ('take_picture.py', '1. Take Picture'),
            ('take_video.py', '2. Take Video'),
            ('form_fillout.py', '3. Fill Out Form'),
            ('get_fingerprint.py', '4. Get Fingerprint'),
            ('upload_info.py', '5. Upload Data'),
            ('card_save.py', '6. Encode on Card')
        ]

        for script, label in scripts:
            btn = QPushButton(label, self)
            btn.clicked.connect(lambda _, s=script: self.individual_script_execution(s))
            layout.addWidget(btn)
            self.script_buttons[script] = btn
            self.original_button_texts[script] = label

        self.btn_auto_run = QPushButton('Auto Run All Steps', self)
        self.btn_auto_run.clicked.connect(self.auto_run_steps)
        layout.addWidget(self.btn_auto_run)

        self.btn_clear_run = QPushButton('Clear Run', self)
        self.btn_clear_run.clicked.connect(self.clear_run)
        layout.addWidget(self.btn_clear_run)

        self.setLayout(layout)

    def updateStatusLabel(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def update_running_text(self):
        # Append a dot each second, reset after 3 dots
        self.running_dots = (self.running_dots + 1) % 4
        self.updateStatusLabel("Running" + "." * self.running_dots, "green")

    def on_script_start(self):
        
        self.running_dots = 0  # Reset dots
        self.update_running_text()
        self.running_timer.start()  # Start updating "Running" text

    def flashStatusLabel(self, color="red"):
        if self.process.state() == QProcess.Running:
            originalColor = "green" if self.status_label.text() == "Running" else "black"
            self.updateStatusLabel("Running", color)
            QTimer.singleShot(1000, lambda: self.updateStatusLabel("Running", originalColor))

    def script_finished(self, exitCode, exitStatus):
        self.running_timer.stop()  # Stop updating "Running" text
        self.updateStatusLabel("Done", "black")
        script_name = self.current_script
        button = self.script_buttons.get(script_name)
        if button:
            # Reset the button text to the original value without a checkmark
            button.setText(self.original_button_texts[script_name])
            # Then, add a checkmark to indicate the script has finished running
            button.setText(f"{self.original_button_texts[script_name]} ✓")
        if self.auto_run_active:
            self.auto_run_steps()
        else:
            self.updateStatusLabel("Ready", "black")


    def individual_script_execution(self, script_name):
        if self.process.state() == QProcess.Running:
            self.flashStatusLabel()  # Flash the status label if another script is attempted to be run
            return
        self.auto_run_active = False
        self.current_script = script_name
        self.execute_script(script_name)

    def clear_run(self):
        for script, btn in self.script_buttons.items():
            btn.setText(self.original_button_texts[script])
        self.updateStatusLabel("Ready", "black")

    def execute_script(self, script_name):
        if self.process.state() == QProcess.NotRunning:
            print(f"Starting script: {script_name}")
            self.process.start(f'python {script_name}')
        else:
            print("A script is already running")
    
    def handle_stdout(self):
        # Read the standard output and convert it to a string
        output = bytes(self.process.readAllStandardOutput()).decode("utf8")
        print(output, end='')  # Print to the terminal

    def handle_stderr(self):
        # Read the standard error and convert it to a string
        output = bytes(self.process.readAllStandardError()).decode("utf8")
        print(output, end='')  # Print to the terminal

    def auto_run_steps(self):
        self.auto_run_active = True
        if self.script_queue:
            script_name = self.script_queue.pop(0)
            self.execute_script(script_name)
        else:
            print('All steps have been executed.')
            self.auto_run_active = False  # Reset the flag when all scripts have been executed
            # Reset the script queue
            self.script_queue = [
            'take_picture.py',
            'form_fillout.py',
            'take_video.py',
            'get_fingerprint.py',
            'upload_info.py',
            'card_save.py'
        ]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())
