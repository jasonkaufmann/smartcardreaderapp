import subprocess
import time
import pyautogui
import pygetwindow as gw

import sys
import subprocess
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QHBoxLayout
from PyQt5.QtCore import QProcess
from PyQt5.QtCore import Qt
import json
import os

class ImageExportGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.fingerButtons = {}  # Store button references
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Fingerprint Capture')
        self.setGeometry(100, 100, 500, 300)

        mainLayout = QVBoxLayout()
        handsLayout = QHBoxLayout()

        # Representing two hands
        self.leftHand = self.createHandLayout("Left")
        self.rightHand = self.createHandLayout("Right")

        handsLayout.addLayout(self.leftHand)
        handsLayout.addLayout(self.rightHand)

        mainLayout.addLayout(handsLayout)

        self.setLayout(mainLayout)
        self.checkExistingFingerprintsAndUpdateButtons()

    def createHandLayout(self, handSide):
        handLayout = QVBoxLayout()
        label = QLabel(f'{handSide} Hand')
        label.setAlignment(Qt.AlignCenter)  # This will center the label
        handLayout.addWidget(label)

        fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Little']
        finger_order = {'Left': {'Little': 0, 'Ring': 1, 'Middle': 2, 'Index': 3, 'Thumb': 4},
                        'Right': {'Thumb': 5, 'Index': 6, 'Middle': 7, 'Ring': 8, 'Little': 9}}

        for finger in fingers:
            finger_number = finger_order[handSide][finger]
            btn = QPushButton(f'{finger}')
            btn.clicked.connect(lambda checked, a=handSide, b=finger: self.startFingerCapture(a, b, finger_number))
            handLayout.addWidget(btn)
            # Store button reference
            self.fingerButtons[f"{handSide}_{finger}"] = btn

        return handLayout
    
    def checkExistingFingerprintsAndUpdateButtons(self):
        """Check for existing fingerprint images and update button texts accordingly."""
        for (hand_finger, btn) in self.fingerButtons.items():
            hand, finger = hand_finger.split("_")
            finger_number = self.getFingerNumber(hand, finger)
            if os.path.exists(f'finger_{finger_number}.jpeg'):
                btn.setText(f"{finger} ✔")

    def getFingerNumber(self, hand, finger):
        finger_order = {'Left': {'Little': 0, 'Ring': 1, 'Middle': 2, 'Index': 3, 'Thumb': 4},
                        'Right': {'Thumb': 5, 'Index': 6, 'Middle': 7, 'Ring': 8, 'Little': 9}}
        return finger_order[hand][finger]

    def updateButtonWithCheckmark(self, hand, finger):
        # Find the button corresponding to the finger and update its text with a checkmark
        btn = self.fingerButtons.get(f"{hand}_{finger}")
        if btn:
            btn.setText(f"{finger} ✔")
            print(f"Updated button for {hand} hand, {finger} finger with checkmark")
        else:
            print(f"Button for {hand} hand, {finger} finger not found.")

    def processFinished(self, exitCode, exitStatus, hand, finger):
        
        self.renameOutput(hand, finger)
        print(f"Capture for {hand} hand, {finger} finger completed successfully.")
        self.updateButtonWithCheckmark(hand, finger)
    
    def startFingerCapture(self, hand, finger, finger_number):
       
        print(f"Selected: {hand} hand, {finger} finger")  # Debug print
        
        # Start the export process

        process = QProcess(self)
        process.finished.connect(lambda exitCode, exitStatus: self.processFinished(exitCode, exitStatus, hand, finger))
        process.start("ExportImage.exe")
        
        try:
            # Wait for the application to open
            time.sleep(5)  # Adjust the sleep time as needed

            # Get the application window
            app_window = gw.getWindowsWithTitle("SecuBSP - Export Image from FIR")[0]

            # Get the position and size of the application window
            window_position = (app_window.left, app_window.top)
            window_size = (app_window.width, app_window.height)

            # Define the region within the application window where the button is located
            region = (window_position[0], window_position[1], window_size[0], window_size[1])

            # Locate the button with the label "NEXT" within the specified region and click it
            next_button_location = pyautogui.locateOnScreen('next_button.png', region=region, confidence=0.75)
            if next_button_location is not None:
                # Center of the button
                next_button_x, next_button_y = pyautogui.center(next_button_location)
                print("Next button found at:", next_button_x, next_button_y)
                pyautogui.click(next_button_x, next_button_y)
            else:
                print("Next button not found")

            time.sleep(2)  # Add a short delay before clicking the finger button
                # Locate the button with the label "NEXT" within the specified region and click it
            finger_button_location = pyautogui.locateOnScreen('finger_button.png', region=region, confidence=0.75)
            if finger_button_location is not None:
                # Center of the button
                next_button_x, next_button_y = pyautogui.center(finger_button_location)
                print("Finger button found at:", next_button_x, next_button_y)
                pyautogui.click(next_button_x, next_button_y)
            else:
                print("Finger button not found")
                
            time.sleep(2)  # Add a short delay before clicking the next button
            # Wait for the "Next" button to appear with a timeout
            start_time = time.time()
            timeout = 120  # seconds
            reg_screen_gone = False
            reg_screen_counter = 0
            while time.time() - start_time < timeout:
                try:
                    reg_screen_location = pyautogui.locateOnScreen('registration_screen.png', region=region, confidence=0.75)
                except Exception as e:
                    reg_screen_counter += 1
                    print("Registration screen not found: " + str(reg_screen_counter))
                    reg_screen_location = None
                    
                if reg_screen_location:
                    print("Registration screen found at:", pyautogui.center(next_button_location))
                if reg_screen_counter >= 2:
                    reg_screen_gone = True
                    break
                time.sleep(5)

            time.sleep(2)  # Add a short delay before clicking the next button
            next_button_location = pyautogui.locateOnScreen('next_button.png', region=region, confidence=0.75)
            if next_button_location is not None:
                # Center of the button
                next_button_x, next_button_y = pyautogui.center(next_button_location)
                print("Next button found at:", next_button_x, next_button_y)
                pyautogui.click(next_button_x, next_button_y)
            else:
                print("Next button not found")
            
            finish_button_location = pyautogui.locateOnScreen('finish_button.png', region=region, confidence=0.95)
            if finish_button_location is not None:
                # Center of the button
                next_button_x, next_button_y = pyautogui.center(finish_button_location)
                print("Finish button found at:", next_button_x, next_button_y)
                pyautogui.click(next_button_x, next_button_y)
            else:
                print("Finish button not found")
        except Exception as e:
            print("Error occurred:", e)
            process.kill()
            print("Process killed.")

    def renameOutput(self, hand, finger):
    
        finger_order = {'Left': {'Little': 0, 'Ring': 1, 'Middle': 2, 'Index': 3, 'Thumb': 4},
                        'Right': {'Thumb': 5, 'Index': 6, 'Middle': 7, 'Ring': 8, 'Little': 9}}
        finger_number =  finger_order[hand][finger]
        renamed_output_filename = f"finger_{finger_number}.jpeg"
        
        output_path = 'output.jpg'  # Assuming 'output.jpg' is the expected output filename
        max_wait_time = 30  # Maximum time to wait for the file to appear, in seconds
        check_interval = 1  # Time interval between checks, in seconds
        
        # Wait for the file to exist, with a maximum wait time
        file_exists = False
        for _ in range(max_wait_time):
            if os.path.exists(output_path):
                file_exists = True
                break
            time.sleep(check_interval)
        
        # Rename the file if it exists
        if file_exists:
            if os.path.exists(renamed_output_filename):
                os.remove(renamed_output_filename)  # Remove the existing file if it exists
                print(f"Existing file {renamed_output_filename} removed.")
                
            os.rename(output_path, renamed_output_filename)
            print(f"File renamed to {renamed_output_filename}")
            self.updateUserDataJson(renamed_output_filename)
        else:
            print("Output file not found within the wait period.")
        
        #sys.exit(app.exec_())
            
    def updateUserDataJson(self, filename):
            user_data_file = 'user_data.json'
            try:
                with open(user_data_file, 'r') as file:
                    data = json.load(file)
            except FileNotFoundError:
                data = {}

            if 'fingerprint_images' not in data:
                data['fingerprint_images'] = []
            if filename not in data['fingerprint_images']:
                data['fingerprint_images'].append(filename)

            with open(user_data_file, 'w') as file:
                json.dump(data, file, indent=4)

            print(f"{filename} added to {user_data_file}.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageExportGUI()
    ex.show()
    sys.exit(app.exec_())



