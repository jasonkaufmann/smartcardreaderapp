import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit, QLineEdit, QLabel, QHBoxLayout
from PyQt5 import QtGui  # PyQt5
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
import random

class SmartCardApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.select_card_type()
        self.memorySize = 256  # Memory size set to 256 bytes

    def initUI(self):
        self.setGeometry(100, 100, 1000, 750)
        self.setWindowTitle('Smart Card Reader and Writer')

        layout = QVBoxLayout()

        readLayout = QHBoxLayout()
        self.readAddressInput = QLineEdit()
        self.readLengthInput = QLineEdit()
        self.readAddressInput.setPlaceholderText("Hex, e.g., 0xFF")
        self.readLengthInput.setPlaceholderText("Decimal, e.g., 16")
        readLayout.addWidget(QLabel('Read Address (Hex):'))
        readLayout.addWidget(self.readAddressInput)
        readLayout.addWidget(QLabel('Length (Dec):'))
        readLayout.addWidget(self.readLengthInput)
        layout.addLayout(readLayout)

        self.testButton = QPushButton('Run Automated Test')
        self.testButton.clicked.connect(self.run_automated_test)
        layout.addWidget(self.testButton)

        self.uidTextEdit = QTextEdit()
        self.uidTextEdit.setReadOnly(True)
        layout.addWidget(self.uidTextEdit)

        self.readButton = QPushButton('Read Data')
        self.readButton.clicked.connect(self.readCardData)
        layout.addWidget(self.readButton)

        writeLayout = QHBoxLayout()
        self.writeAddressInput = QLineEdit()
        self.writeDataInput = QLineEdit()
        self.writeAddressInput.setPlaceholderText("Hex, e.g., 0xAF")
        self.writeDataInput.setPlaceholderText("Hex, e.g., 01AB")
        writeLayout.addWidget(QLabel('Write Address (Hex):'))
        writeLayout.addWidget(self.writeAddressInput)
        writeLayout.addWidget(QLabel('Data (Hex):'))
        writeLayout.addWidget(self.writeDataInput)
        layout.addLayout(writeLayout)

        self.writeButton = QPushButton('Write Data')
        self.writeButton.clicked.connect(self.writeCardData)
        layout.addWidget(self.writeButton)

        # Add a button for reading the PSC
        self.readPSCButton = QPushButton('Read PSC')
        self.readPSCButton.clicked.connect(self.read_psc_display)  # Connect to the slot method
        layout.addWidget(self.readPSCButton)

        # Add a button for clearing the text edit widget
        self.clearButton = QPushButton('Clear')
        self.clearButton.clicked.connect(self.clearText)  # Connect to the slot method for clearing text
        layout.addWidget(self.clearButton)

        # Add a button for reading protection bits
        self.readProtectionButton = QPushButton('Read Protection Bits')
        self.readProtectionButton.clicked.connect(self.read_protection_bits)  # Connect to the slot method
        layout.addWidget(self.readProtectionButton)

        self.setLayout(layout)

    def clearText(self):
        self.uidTextEdit.clear()

    def select_card_type(self):
        try:
            r = readers()
            if not r:
                self.uidTextEdit.append('No readers available')
                return
            
            reader = r[0]  # Assuming you are using the first reader
            self.connection = reader.createConnection()
            self.connection.connect()
            
            # Append the name of the reader to the text edit widget
            self.uidTextEdit.append(f'Connected to reader: {reader}')
            
            command = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x06]  # Command for selecting card type
            data, sw1, sw2 = self.connection.transmit(command)
            
            if (sw1, sw2) == (0x90, 0x00):
                self.uidTextEdit.append('Card type selected successfully.')
            else:
                self.uidTextEdit.append(f'Select card type failed with SW1 SW2 = {sw1:02X} {sw2:02X}')
        except Exception as e:
            self.uidTextEdit.append(f'Error selecting card type: {str(e)}')

    def read_memory(self, address, length):
        if address + length > self.memorySize - 1 or address < 0 or length <= 0:
            return (address, length, 'Address or length out of bounds'), False
        try:
            command = [0xFF, 0xB0, 0x00, address, length]
            data, sw1, sw2 = self.connection.transmit(command)
            if (sw1, sw2) == (0x90, 0x00):
                return (address, length, toHexString(data)), True
            else:
                return (address, length, f'Failed to read data with SW1 SW2 = {sw1:02X} {sw2:02X}'), False
        except Exception as e:
            return (address, length, f'Error reading data: {str(e)}'), False

    def write_memory(self, address, dataToWrite):
        if address + len(dataToWrite) > self.memorySize - 1 or address < 0:
            return (address, len(dataToWrite), 'Address or data length out of bounds'), False
        if not self.verify_psc():
            return (address, len(dataToWrite), 'PSC verification failed. Cannot perform write operation.'), False
        try:
            command = [0xFF, 0xD0, 0x00, address, len(dataToWrite)] + list(dataToWrite)
            _, sw1, sw2 = self.connection.transmit(command)
            if (sw1, sw2) == (0x90, 0x00):
                return (address, len(dataToWrite), 'Data written successfully'), True
            else:
                return (address, len(dataToWrite), f'Failed to write data with SW1 SW2 = {sw1:02X} {sw2:02X}'), False
        except Exception as e:
            return (address, len(dataToWrite), f'Error writing data: {str(e)}'), False

    def readCardData(self):
        self.uidTextEdit.append(' ')
        try:
            address = int(self.readAddressInput.text(), 16)
            length = int(self.readLengthInput.text())
        except ValueError:
            self.uidTextEdit.append('Error: Invalid input. Please enter valid hexadecimal address and decimal length.')
            return

        if address < 0 or length <= 0:
            self.uidTextEdit.append('Error: Address must be a positive hexadecimal number and length must be a positive decimal number.')
            return

        (addr, length_read, readData), success = self.read_memory(address, length)
        hexValues = readData.split()
        if success:
            protectable_memory = []
            data_memory = []
            for i in range(len(hexValues)):
                if i < 33:
                    protectable_memory.append(hexValues[i])
                else:
                    data_memory.append(hexValues[i])
            
            self.uidTextEdit.append(f'Addr: {addr:X}, Length: {length_read}')
            if protectable_memory:
                self.uidTextEdit.append('Protectable Memory:')
                self.uidTextEdit.append(' '.join(protectable_memory))
            if data_memory:
                self.uidTextEdit.append('Data Memory:')
                self.uidTextEdit.append(' '.join(data_memory))
        else:
            self.uidTextEdit.append(f'Failed to read data: {readData}')


    def writeCardData(self):
        self.uidTextEdit.append(' ')
        try:
            address = int(self.writeAddressInput.text(), 16)
        except ValueError:
            self.uidTextEdit.append('Error: Invalid input. Please enter a valid hexadecimal address.')
            return

        if address < 0:
            self.uidTextEdit.append('Error: Address must be a positive hexadecimal number.')
            return

        if address < 32:
            self.uidTextEdit.append('Error: Writing to the first 32 bytes is not allowed.')
            return

        dataToWrite = toBytes(self.writeDataInput.text())
        if not dataToWrite:
            self.uidTextEdit.append('Error: Data to write is null.')
            return

        (addr, length_written, writeMessage), success = self.write_memory(address, dataToWrite)
        if success:
            self.uidTextEdit.append(f'Addr: {addr:X}, Length: {length_written}, {writeMessage}')
        else:
            self.uidTextEdit.append(f'Failed to write data: {writeMessage}')


    def verify_psc(self):
        psc = self.read_psc_from_file()  # Reads the PSC from the file
        if not psc:
            self.uidTextEdit.append('Failed to retrieve PSC for verification.')
            return False
        
        try:
            # Construct the command to submit the PSC
            command = [0xFF, 0x20, 0x00, 0x00, 0x03] + psc
            data, sw1, sw2 = self.connection.transmit(command)
            
            # Interpret the response based on SW2
            if sw1 == 0x90:  # Check if SW1 indicates success
                if sw2 == 0x07:  # Verification is correct
                    # Move cursor to the end of the text
                    self.uidTextEdit.moveCursor(QtGui.QTextCursor.End)
                    # Insert text at the current cursor position, which is now at the end
                    self.uidTextEdit.insertPlainText('/PSC ✔')
                    return True
                elif sw2 == 0x00:  # Password is locked
                    self.uidTextEdit.append('PSC verification failed: password is locked.')
                else:  # Other values indicate failed verification attempts
                    self.uidTextEdit.append(f'PSC verification failed: current error count is {sw2}. ✖')
            else:
                self.uidTextEdit.append(f'Failed to verify PSC with SW1 SW2 = {sw1:02X} {sw2:02X} ✖')
            return False
        except Exception as e:
            self.uidTextEdit.append(f'Error during PSC verification: {str(e)} ✖')
            return False

    def change_secret_code(self, new_psc):
        if self.verify_psc():
            command = [0xFF, 0xD2, 0x00, 0x01, 0x03] + new_psc
            data, sw1, sw2 = self.connection.transmit(command)
            
            if (sw1, sw2) == (0x90, 0x00):
                self.write_psc_to_file(new_psc)
                self.uidTextEdit.append('Secret code changed successfully.')
            else:
                self.uidTextEdit.append('Failed to change secret code.')
        else:
            self.uidTextEdit.append('Current PSC verification required before changing the code.')

    def read_protection_bits(self):
        self.uidTextEdit.append(' ')
        if not hasattr(self, 'connection'):
            self.uidTextEdit.append('No connection to card. Please establish connection first.')
            return
        
        try:
            command = [0xFF, 0xB2, 0x00, 0x00, 0x04]  # Command to read protection bits
            data, sw1, sw2 = self.connection.transmit(command)
            
            if (sw1, sw2) == (0x90, 0x00):
                # Assuming data contains PROT 1 to PROT 4 as the first 4 bytes
                protection_bits_hex = ' '.join([f'{byte:02X}' for byte in data[:4]])
                protection_bits_binary = ' '.join([f'{byte:08b}' for byte in data[:4]])
                
                self.uidTextEdit.append(f'Protection bits (Hex): {protection_bits_hex}')
                self.uidTextEdit.append(f'Protection bits (Binary): {protection_bits_binary}')
            else:
                self.uidTextEdit.append(f'Failed to read protection bits with SW1 SW2 = {sw1:02X} {sw2:02X}')
        except Exception as e:
            self.uidTextEdit.append(f'Error reading protection bits: {str(e)}')

    def read_presentation_error_counter(self):
        command = [0xFF, 0xB1, 0x00, 0x00, 0x04]
        data, sw1, sw2 = self.connection.transmit(command)
        
        if (sw1, sw2) == (0x90, 0x00) and len(data) > 0:
            error_counter = data[0]
            self.uidTextEdit.append(f'Presentation error counter: {error_counter}')
        else:
            self.uidTextEdit.append('Failed to read presentation error counter.')

    def read_psc_display(self):
        self.uidTextEdit.append(' ')
        psc = self.read_psc_from_file()  # Use the existing method to read the PSC
        if psc:
            # Convert the PSC list to a hex string for display
            psc_hex = ' '.join([f'{byte:02X}' for byte in psc])
            self.uidTextEdit.append(f'Current PSC: {psc_hex}')
        else:
            self.uidTextEdit.append('Failed to read PSC from file.')

    def read_psc_from_file(self, filename="psc.txt"):
        try:
            with open(filename, "r") as file:
                # Read the PSC, strip whitespace and spaces, then parse
                psc_hex = file.readline().strip().replace(" ", "")
                return [int(psc_hex[i:i+2], 16) for i in range(0, len(psc_hex), 2)]
        except FileNotFoundError:
            self.uidTextEdit.append('PSC file not found, using default PSC.')
            return [0xFF, 0xFF, 0xFF]
        except ValueError as e:
            self.uidTextEdit.append(f'Error parsing PSC: {str(e)}')
            return [0xFF, 0xFF, 0xFF]

    def write_psc_to_file(self, psc, filename="psc.txt"):
        psc_hex = ''.join([f"{byte:02X}" for byte in psc])
        with open(filename, "w") as file:
            file.write(psc_hex)
            self.uidTextEdit.append('PSC updated in file.')

    def run_automated_test(self):
        self.uidTextEdit.append(' ')
        if not hasattr(self, 'connection'):
            self.uidTextEdit.append('No connection to card. Please establish connection first.')
            return

        # Select a random address outside the first 32 bytes
        address = random.randint(33, self.memorySize - 1)  # Ensure address is within bounds
        test_value = [random.randint(0, 255)]  # Write a single byte of random data
        self.uidTextEdit.append(f'Testing address: h\'{address:X}\', writing value: h\'{test_value[0]:02X}\'')

        # Step 1: Read the original value
        (addr, length, original_value), success = self.read_memory(address, 1)
        if not success:
            self.uidTextEdit.append(f'Failed to read from address h\'{addr:X}\': {original_value}')
            return

        original_value_bytes = [int(original_value[i:i+2], 16) for i in range(0, len(original_value), 2)]
        self.uidTextEdit.append(f'Original value at address h\'{addr:X}\': {original_value}')

        # Step 2: Write the test value
        (addr, length_written, message), success = self.write_memory(address, test_value)
        if not success:
            self.uidTextEdit.append(f'Failed to write to address h\'{addr:X}\': {message}')
            return

        self.uidTextEdit.append(f'Wrote test value h\'{test_value[0]:02X}\' at address h\'{addr:X}\'')

        # Step 3: Read back the value
        (addr, length, read_back_value), success = self.read_memory(address, 1)
        if not success:
            self.uidTextEdit.append(f'Failed to read back from address h\'{addr:X}\': {read_back_value}')
            return

        self.uidTextEdit.append(f'Read back value at address h\'{addr:X}\': {read_back_value}')

        # Step 4: Verify the write operation
        if read_back_value == toHexString(test_value):
            self.uidTextEdit.append(f'Successfully verified write at address h\'{addr:X}\'. Value: h\'{read_back_value}\'')
        else:
            self.uidTextEdit.append(f'Verification failed at address h\'{addr:X}\'. Expected h\'{test_value[0]:02X}\', got h\'{read_back_value}\'')

        # Step 5: Write back the original value
        (addr, length_restored, message), success = self.write_memory(address, original_value_bytes)
        if success:
            self.uidTextEdit.append(f'Original value h\'{original_value}\' restored at address h\'{addr:X}\'.')
        else:
            self.uidTextEdit.append(f'Failed to restore original value at address h\'{addr:X}\': {message}')

def main():
    app = QApplication(sys.argv)
    ex = SmartCardApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
