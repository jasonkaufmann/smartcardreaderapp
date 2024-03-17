import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit, QLineEdit, QLabel, QHBoxLayout, QComboBox, QStackedLayout
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
import smartcard
import random

class SmartCardApp(QWidget):
    def __init__(self):
        super().__init__()
        self.memorySize = 256  # Default memory size for SLE5542
        self.chipOptions = {
            "AT24C01": (128, 8),
            "AT24C02": (256, 8),
            "AT24C04": (512, 16),
            "AT24C08": (1024, 16),
            "AT24C16": (2048, 16),
            "AT24C32": (4096, 32),
            "AT24C64": (8192, 32),
            "AT24C128": (16384, 64),
            "AT24C256": (32768, 64),
            "AT24C512": (65536, 128),
            "AT24C1024": (131072, 256),
            "SLE5542": (256, 1)
        }
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 1000, 750)
        self.setWindowTitle('Smart Card Reader and Writer')

        self.layout = QVBoxLayout(self)

        self.readerComboBox = QComboBox()
        self.updateAvailableReaders()
        self.makeNewReadConnection()
        self.layout.addWidget(QLabel('Select Reader:'))
        self.layout.addWidget(self.readerComboBox)
        self.readerComboBox.currentIndexChanged.connect(self.makeNewReadConnection)
        self.updateReadersButton = QPushButton('Update Available Readers')
        self.updateReadersButton.clicked.connect(self.updateAvailableReaders)
        self.layout.addWidget(self.updateReadersButton)

        self.currentView = 'ADVANCED'
        # Toggle View Button
        self.toggleViewButton = QPushButton('Switch to ADVANCED View')
        self.toggleViewButton.clicked.connect(self.toggleView)
        self.layout.addWidget(self.toggleViewButton)
    

        # Stacked Layout for switching views
        self.stackedLayout = QStackedLayout()
        self.layout.addLayout(self.stackedLayout)


        # Advanced View Widget
        self.advancedViewWidget = QWidget()
        self.advancedLayout = QVBoxLayout(self.advancedViewWidget)
        self.setupAdvancedView()
        self.stackedLayout.addWidget(self.advancedViewWidget)

        
        # Basic View Widget
        self.basicViewWidget = QWidget()
        self.basicLayout = QVBoxLayout(self.basicViewWidget)
        self.setupBasicView()
        self.stackedLayout.addWidget(self.basicViewWidget)

        self.toggleView()

    def set_chip_family(self, chip_name):
        index = self.chipFamilyComboBox.findText(chip_name, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.chipFamilyComboBox.setCurrentIndex(index)


    def setupBasicView(self):

        # Dropdown for chip family selection
        self.chipFamilyComboBox = QComboBox()
        for chip, (size, _) in self.chipOptions.items():
            self.chipFamilyComboBox.addItem(chip, size)
        self.chipFamilyComboBox.currentIndexChanged.connect(self.updateCharacterCount)
        self.basicLayout.addWidget(QLabel('Select Chip:'))
        self.basicLayout.addWidget(self.chipFamilyComboBox)

        # Byte Offset and Data Length Inputs
        self.byteOffsetInput = QLineEdit()
        self.byteOffsetInput.setPlaceholderText("Byte Offset (e.g., 0)")
        self.basicLayout.addWidget(QLabel('Byte Offset:'))
        self.basicLayout.addWidget(self.byteOffsetInput)

        self.dataLengthInput = QLineEdit()
        self.dataLengthInput.setPlaceholderText("Length of data to read (bytes)")
        self.basicLayout.addWidget(QLabel('Data Length:'))
        self.basicLayout.addWidget(self.dataLengthInput)
        
        # Read and Write Buttons
        self.readDataButton = QPushButton('Read Data')
        self.readDataButton.clicked.connect(self.readAsciiFromCard)
        self.basicLayout.addWidget(self.readDataButton)

        self.basicWriteButton = QPushButton('Write ASCII to Card')
        self.basicWriteButton.clicked.connect(self.writeAsciiToCard)
        self.basicLayout.addWidget(self.basicWriteButton)

        # Text Areas for Writing and Reading
        self.basicTextInput = QTextEdit()
        self.basicTextInput.setPlaceholderText("Type here to write...")
        self.basicLayout.addWidget(self.basicTextInput)
        self.basicTextInput.textChanged.connect(self.updateCharacterCount)

        self.readDataTextArea = QTextEdit()
        self.readDataTextArea.setPlaceholderText("Read data will appear here...")
        self.readDataTextArea.setReadOnly(True)  # Make read-only if just for display
        self.basicLayout.addWidget(self.readDataTextArea)

        # Characters Left Label and Success Notification
        self.charactersLeftLabel = QLabel("0/0")
        self.basicLayout.addWidget(self.charactersLeftLabel)

        # Read and Write Buttons
        self.clearReadDataButton = QPushButton('Clear Read Data')
        self.clearReadDataButton.clicked.connect(self.clearReadData)
        self.basicLayout.addWidget(self.clearReadDataButton)
        
        self.successNotificationLabel = QLabel('')
        self.basicLayout.addWidget(self.successNotificationLabel)
        self.successNotificationLabel.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self.successNotificationLabel.setStyleSheet("color: green;")

        self.updateCharacterCount()  # Update the validator for dataLengthInput

    def clearReadData(self):
        self.readDataTextArea.clear()
        
    def makeNewReadConnection(self):
        try:
            selectedReaderName = self.readerComboBox.currentText()
            # Find the reader object that matches the selected name
            availableReaders = readers()
            reader = next((r for r in availableReaders if str(r) == selectedReaderName), None)
            if reader is None:
                #print('No readers found. Plese check the connection and try again.')
                return
            
            self.connection = reader.createConnection()
            #print(self.connection)
            self.connection.connect()
            print(f'Connected to reader: {selectedReaderName}')
        except Exception as e:
            print(f'Error connecting to reader: {str(e)}')
        try:
            if self.currentView == 'ADVANCED':
                self.updateUIBasedOnChipType()
            elif self.currentView == 'BASIC':
                self.checkCardPresence()
        except:
            pass
            
    def showTemporaryMessage(self, message):
        self.successNotificationLabel.setText(message)
        QTimer.singleShot(1000, self.clearTemporaryMessage)  # Clear after 1000ms
    
    def clearTemporaryMessage(self):
        self.successNotificationLabel.clear()

    def updateCharacterCount(self):
        memorySize = self.chipFamilyComboBox.currentData()  # Get the memory size for the selected chip
        currentCharacters = len(self.basicTextInput.toPlainText())
        remainingCharacters = memorySize - currentCharacters  # Calculate the remaining characters
        self.charactersLeftLabel.setText(f"{currentCharacters}/{memorySize}")
        # Update the Write button enabled state based on the character count
        self.basicWriteButton.setEnabled(currentCharacters <= memorySize)
        self.dataLengthInput.setValidator(QIntValidator(1, memorySize))
        self.checkCardPresence()
        
    def checkCardPresence(self):
        chipType = self.chipFamilyComboBox.currentText()
        if chipType == 'SLE5542':
            status = self.select_card_type()
        elif chipType.startswith('AT24'):
            status = self.select_card_type_atmel()
            if status:
                self.select_page_size()    
        return status
    
    def writeAsciiToCard(self):
        status = self.checkCardPresence()
        if not status:
            self.readDataTextArea.setText('Error: Card not found. Please check the connection and try again.')
            return
        text = self.basicTextInput.toPlainText()
        asciiData = [ord(c) for c in text]  # Convert text to ASCII values

        # Retrieve the chip type, memory size, and associated page size
        chipType = self.chipFamilyComboBox.currentText()
        memorySize, pageSize = self.chipOptions[chipType]

        # Retrieve the byte offset from the input field
        byteOffsetText = self.byteOffsetInput.text()
        if byteOffsetText == "":
            byteOffset = 0
        else:
            try:
                byteOffset = int(byteOffsetText)
            except ValueError:
                self.uidTextEdit.append('Error: Invalid byte offset. Please enter a valid number.')
                return
        
        # Default to the maximum memory size if no length is specified
        try:
            dataLength = int(self.dataLengthInput.text()) if self.dataLengthInput.text() else memorySize - byteOffset
        except ValueError:
            self.uidTextEdit.append('Error: Invalid data length. Please enter a valid number.')
            return

        # Ensure byteOffset and dataLength are within memory bounds
        if byteOffset >= memorySize:
            self.uidTextEdit.append('Error: Byte offset exceeds chip memory size.')
            return
        if byteOffset + dataLength > memorySize or dataLength < 0:
            dataLength = memorySize - byteOffset  # Adjust dataLength to not exceed memorySize

        # Write the ASCII data
        totalWrittenBytes = 0
        for i in range(0, len(asciiData), pageSize):
            address = byteOffset + i
            dataChunk = asciiData[i:i+pageSize]
            
            if chipType.startswith('AT24'):
                writeStatus, message = self.writeCardDataAtmel(address, dataChunk)
            elif chipType == 'SLE5542':
                (addr, length_written, message), writeStatus = self.write_memory(address, dataChunk)
            
            if not writeStatus:
                self.uidTextEdit.append(f'Failed to write data chunk: {message}')
                return
            totalWrittenBytes += len(dataChunk)

        # Fill the rest of the specified length with FF, if applicable
        remainingBytes = dataLength - totalWrittenBytes
        if remainingBytes > 0:
            fillData = [0xFF] * remainingBytes
            for i in range(0, remainingBytes, pageSize):
                address = byteOffset + totalWrittenBytes + i
                dataChunk = fillData[i:i+pageSize]

                if chipType.startswith('AT24'):
                    writeStatus, message = self.writeCardDataAtmel(address, dataChunk)
                elif chipType == 'SLE5542':
                    writeStatus, message = self.write_memory(address, dataChunk)

                if not writeStatus:
                    self.uidTextEdit.append(f'Failed to fill remaining memory: {message}')
                    return

        self.showTemporaryMessage("Data written successfully.")

    def readAsciiFromCard(self):
        status = self.checkCardPresence()
        if not status:
            self.readDataTextArea.setText('Error: Card not found. Please check the connection and try again.')
            return
        # Retrieve the byte offset from the input field
        byteOffsetText = self.byteOffsetInput.text()
        if byteOffsetText == "":
            byteOffset = 0
        else:
            try:
                byteOffset = int(byteOffsetText)
            except ValueError:
                self.uidTextEdit.append('Error: Invalid byte offset. Please enter a valid number.')
                return

        chipType = self.chipFamilyComboBox.currentText()
        memorySize, pageSize = self.chipOptions[chipType]

        try:
            dataLength = int(self.dataLengthInput.text()) if self.dataLengthInput.text() else memorySize - byteOffset
        except ValueError:
            dataLength = memorySize - byteOffset

        if byteOffset + dataLength > memorySize:
            dataLength = memorySize - byteOffset
            self.uidTextEdit.append(f'Note: Adjusting read length to stay within memory bounds. Reading {dataLength} bytes.')

        readData = []
        totalReadBytes = 0

        if chipType == 'SLE5542':
            dataLength = dataLength - 1

        while totalReadBytes < dataLength:
            currentLength = min(pageSize, dataLength - totalReadBytes)
            if chipType.startswith('AT24'):
                success, chunk = self.readCardDataAtmel(byteOffset + totalReadBytes, currentLength)
            elif chipType == 'SLE5542':
                (addr, length_read, chunk), success = self.read_memory(byteOffset + totalReadBytes, currentLength)
            else:
                self.uidTextEdit.append(f'Error: Unsupported chip type {chipType}.')
                return

            if success and chunk is not None:
                readData.extend(chunk)
                totalReadBytes += len(chunk)
            else:
                self.uidTextEdit.append('Failed to read data.')
                return

        readDataStr = ''.join([' ' if byte == 0xFF else chr(byte) for byte in readData])
        self.readDataTextArea.setText(readDataStr)
        self.showTemporaryMessage("Data read successfully.")


    def toggleView(self):
        if self.currentView == 'ADVANCED':
            self.stackedLayout.setCurrentIndex(1)  # Switch to Basic View
            self.toggleViewButton.setText('Switch to ADVANCED View')
            self.checkCardPresence()
            self.currentView = 'BASIC'
        else:
            self.stackedLayout.setCurrentIndex(0)  # Switch to Advanced View
            self.updateUIBasedOnChipType()
            self.toggleViewButton.setText('Switch to BASIC View')
            self.currentView = 'ADVANCED'

    def clearLayout(self, layout):
        """Recursively remove all items from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                self.clearLayout(item.layout())

    def setupAdvancedView(self):
        # Chip type selection dropdown
        self.chipTypeComboBox = QComboBox()
        self.chipTypeComboBox.addItem("SLE5542")
        self.chipTypeComboBox.addItem("AT24CXX")
        self.chipTypeComboBox.currentIndexChanged.connect(self.updateUIBasedOnChipType)
        self.advancedLayout.addWidget(self.chipTypeComboBox)
               
        # Placeholder for dynamic content based on chip type
        self.dynamicContentLayout = QVBoxLayout()
        self.advancedLayout.addLayout(self.dynamicContentLayout)
        
        #self.setLayout(self.layout)
        self.updateUIBasedOnChipType()  # Initialize UI for default selection

    def updateUIBasedOnChipType(self):
        chipType = self.chipTypeComboBox.currentText()
        
         # Clear dynamic content
        for i in reversed(range(self.dynamicContentLayout.count())): 
            layoutItem = self.dynamicContentLayout.itemAt(i)
            if layoutItem.widget():
                # If the item is a widget, remove it from the layout and set its parent to None (deletes the widget)
                widget = layoutItem.widget()
                self.dynamicContentLayout.removeWidget(widget)
                widget.setParent(None)
            elif layoutItem.layout():
                # If the item is a layout, recursively remove all items from this layout and then delete the layout
                self.clearLayout(layoutItem.layout())
                layoutItem.layout().setParent(None)

        if chipType == "SLE5542":
            self.setupUIForSLE5542()
            self.select_card_type()
        elif chipType == "AT24CXX":
            self.setupUIForAT24CXX()
            self.select_card_type_atmel()
            self.select_page_size()

    def setupUIForSLE5542(self):
        # Create a layout for read operations
        readLayout = QHBoxLayout()
        self.readAddressInput = QLineEdit()
        self.readLengthInput = QLineEdit()
        self.readAddressInput.setPlaceholderText("Hex, e.g., 0xFF")
        self.readLengthInput.setPlaceholderText("Decimal, e.g., 16")
        readLayout.addWidget(QLabel('Read Address (Hex):'))
        readLayout.addWidget(self.readAddressInput)
        readLayout.addWidget(QLabel('Length (Dec):'))
        readLayout.addWidget(self.readLengthInput)
        self.dynamicContentLayout.addLayout(readLayout)  # Add to dynamic content layout

        # Add test button
        self.testButton = QPushButton('Run Automated Test')
        self.testButton.clicked.connect(self.run_automated_test)
        self.dynamicContentLayout.addWidget(self.testButton)  # Add to dynamic content layout

        # Add UID text edit
        self.uidTextEdit = QTextEdit()
        self.uidTextEdit.setReadOnly(True)
        self.dynamicContentLayout.addWidget(self.uidTextEdit)  # Add to dynamic content layout

        # Add read button
        self.readButton = QPushButton('Read Data')
        self.readButton.clicked.connect(self.readCardData)
        self.dynamicContentLayout.addWidget(self.readButton)  # Add to dynamic content layout

        # Create a layout for write operations
        writeLayout = QHBoxLayout()
        self.writeAddressInput = QLineEdit()
        self.writeDataInput = QLineEdit()
        self.writeAddressInput.setPlaceholderText("Hex, e.g., 0xAF")
        self.writeDataInput.setPlaceholderText("Hex, e.g., 01AB")
        writeLayout.addWidget(QLabel('Write Address (Hex):'))
        writeLayout.addWidget(self.writeAddressInput)
        writeLayout.addWidget(QLabel('Data (Hex):'))
        writeLayout.addWidget(self.writeDataInput)
        self.dynamicContentLayout.addLayout(writeLayout)  # Add to dynamic content layout

        # Add write button
        self.writeButton = QPushButton('Write Data')
        self.writeButton.clicked.connect(self.writeCardData)
        self.dynamicContentLayout.addWidget(self.writeButton)  # Add to dynamic content layout

        # Add buttons for PSC reading, clearing text, and reading protection bits
        self.readPSCButton = QPushButton('Read PSC')
        self.readPSCButton.clicked.connect(self.read_psc_display)
        self.dynamicContentLayout.addWidget(self.readPSCButton)  # Add to dynamic content layout

        self.clearButton = QPushButton('Clear')
        self.clearButton.clicked.connect(self.clearText)
        self.dynamicContentLayout.addWidget(self.clearButton)  # Add to dynamic content layout

        self.readProtectionButton = QPushButton('Read Protection Bits')
        self.readProtectionButton.clicked.connect(self.read_protection_bits)
        self.dynamicContentLayout.addWidget(self.readProtectionButton)  # Add to dynamic content layout


    def setupUIForAT24CXX(self):
        # Create a layout for read operations
        readLayout = QHBoxLayout()
        self.readAddressInput = QLineEdit()
        self.readLengthInput = QLineEdit()
        self.readAddressInput.setPlaceholderText("Hex, e.g., 0xFF")
        self.readLengthInput.setPlaceholderText("Decimal, e.g., 16")
        readLayout.addWidget(QLabel('Read Address (Hex):'))
        readLayout.addWidget(self.readAddressInput)
        readLayout.addWidget(QLabel('Length (Dec):'))
        readLayout.addWidget(self.readLengthInput)
        self.dynamicContentLayout.addLayout(readLayout)  # Add to dynamic content layout

        # Add UID text edit
        self.uidTextEdit = QTextEdit()
        self.uidTextEdit.setReadOnly(True)
        self.dynamicContentLayout.addWidget(self.uidTextEdit)  # Add to dynamic content layout

        # Add read button
        self.readButton = QPushButton('Read Data')
        self.readButton.clicked.connect(self.readAtmelStart)
        self.dynamicContentLayout.addWidget(self.readButton)  # Add to dynamic content layout

        # Create a layout for write operations
        writeLayout = QHBoxLayout()
        self.writeAddressInput = QLineEdit()
        self.writeDataInput = QLineEdit()
        self.writeAddressInput.setPlaceholderText("Hex, e.g., 0xAF")
        self.writeDataInput.setPlaceholderText("Hex, e.g., 01AB")
        writeLayout.addWidget(QLabel('Write Address (Hex):'))
        writeLayout.addWidget(self.writeAddressInput)
        writeLayout.addWidget(QLabel('Data (Hex):'))
        writeLayout.addWidget(self.writeDataInput)
        self.dynamicContentLayout.addLayout(writeLayout)  # Add to dynamic content layout

        # Add write button
        self.writeButton = QPushButton('Write Data')
        self.writeButton.clicked.connect(self.writeAtmelStart)
        self.dynamicContentLayout.addWidget(self.writeButton)  # Add to dynamic content layout

        self.clearButton = QPushButton('Clear')
        self.clearButton.clicked.connect(self.clearText)
        self.dynamicContentLayout.addWidget(self.clearButton)  # Add to dynamic content layout

    def readAtmelStart(self):
        try:
            address = int(self.readAddressInput.text(), 16)
            length = int(self.readLengthInput.text())
        except ValueError:
            self.uidTextEdit.append('Error: Invalid input. Please enter valid hexadecimal address and decimal length.')
            return

        if address < 0 or length <= 0:
            self.uidTextEdit.append('Error: Address must be a positive hexadecimal number and length must be a positive decimal number.')
            return

        data, _ = self.readCardDataAtmel(address, length-1)

    def writeAtmelStart(self):
        try:
            address = int(self.writeAddressInput.text(), 16)
        except ValueError:
            self.uidTextEdit.append('Error: Invalid input. Please enter a valid hexadecimal address.')
            return

        if address < 0:
            self.uidTextEdit.append('Error: Address must be a positive hexadecimal number.')
            return

        dataToWrite = toBytes(self.writeDataInput.text())
        if not dataToWrite:
            self.uidTextEdit.append('Error: Data to write is null.')
            return

        if len(dataToWrite) > 32:
            self.uidTextEdit.append('Error: Data length exceeds page size.')
            return

        if self.writeCardDataAtmel(address, dataToWrite):
            self.uidTextEdit.append('Write Successful.')
        else:
            self.uidTextEdit.append('Failed to write data.')

    def readCardDataAtmel(self, address, length):
        try:
            # Make sure address and length are within valid range
            if address < 0 or length <= 0:
                self.uidTextEdit.append('Error: Address and length must be positive numbers.')
                return None
            
            # Construct the command for reading data
            command = [0xFF, 0xB0, address >> 8, address & 0xFF, length]
            data, sw1, sw2 = self.connection.transmit(command)
            
            if (sw1, sw2) == (0x90, 0x00):
                # Successfully read the data
                length = length + 1
                self.uidTextEdit.append(f'Read Successful: Addr: {address:X}, Length: {length}')
                self.uidTextEdit.append(toHexString(data))
                return (True, data)
            else:
                # Error in reading the data
                self.uidTextEdit.append(f"Error reading memory with SW1 SW2 = {sw1:02X} {sw2:02X}")
                return (False, None)
        except Exception as e:
            self.uidTextEdit.append(f'Exception during read: {str(e)}')
            return (False, None)

    def writeCardDataAtmel(self, address, dataToWrite):
        try:
            # Check if dataToWrite is valid
            if not dataToWrite:
                self.uidTextEdit.append('Error: Data to write is null.')
                return False
            if len(dataToWrite) > 32:
                self.uidTextEdit.append('Error: Data length exceeds page size.')
                return False
            
            # Convert the data to be written into a list of bytes if necessary
            if isinstance(dataToWrite, str):
                dataToWrite = toBytes(dataToWrite)
            
            # Construct the command for writing data
            command = [0xFF, 0xD0, address >> 8, address & 0xFF, len(dataToWrite)] + dataToWrite
            _, sw1, sw2 = self.connection.transmit(command)
            
            if (sw1, sw2) == (0x90, 0x00):
                return (True, 'Data written successfully')
            else:
                return (False, f'Failed to write data with SW1 SW2 = {sw1:02X} {sw2:02X}')
        except Exception as e:
            return (False, f'Error writing data: {str(e)}')

    def select_page_size(self):
        command = [0xFF, 0x01, 0x00, 0x00, 0x01, 0x05]  # Command to select 32-byte page size
        data, sw1, sw2 = self.connection.transmit(command)
        if (sw1, sw2) == (0x90, 0x00):
            self.uidTextEdit.append('Page size selected successfully.')
        else:
            self.uidTextEdit.append(f"Error selecting page size with SW1 SW2 = {sw1:02X} {sw2:02X}")

    def updateAvailableReaders(self):
        self.readerComboBox.clear()
        for reader in readers():
            print(reader)
            self.readerComboBox.addItem(str(reader))

    def select_card_type_atmel(self):
        try:
            selectedReaderName = self.readerComboBox.currentText()
            # Find the reader object that matches the selected name
            availableReaders = readers()
            reader = next((r for r in availableReaders if str(r) == selectedReaderName), None)
            if reader is None:
                self.uidTextEdit.append('Selected reader not found')
                return
            
            self.connection = reader.createConnection()
            self.connection.connect()
            self.uidTextEdit.append(f'Connected to reader: {selectedReaderName}')
            
            command = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x02]  # Command to select the AT24CXX card
            data, sw1, sw2 = self.connection.transmit(command)
            if (sw1, sw2) == (0x90, 0x00):
                self.uidTextEdit.append('Card type selected successfully.')
                return True
            else:
                self.uidTextEdit.append(f"Error selecting card type with SW1 SW2 = {sw1:02X} {sw2:02X}")
                return False
        except Exception as e:
            print(f"Error selecting card type: {str(e)}")
            self.uidTextEdit.append(f"Error selecting card type: {str(e)}")
            return False    

    def clearText(self):
        self.uidTextEdit.clear()

    def select_card_type(self):
        try:
            selectedReaderName = self.readerComboBox.currentText()
            # Find the reader object that matches the selected name
            availableReaders = readers()
            reader = next((r for r in availableReaders if str(r) == selectedReaderName), None)
            if reader is None:
                self.uidTextEdit.append('Selected reader not found')
                return
            
            self.connection = reader.createConnection()
            self.connection.connect()
            self.uidTextEdit.append(f'Connected to reader: {selectedReaderName}')
            
            command = [0xFF, 0xA4, 0x00, 0x00, 0x01, 0x06]  # Command for selecting card type
            data, sw1, sw2 = self.connection.transmit(command)
            
            if (sw1, sw2) == (0x90, 0x00):
                self.uidTextEdit.append('Card type selected successfully.')
                return True
            else:
                self.uidTextEdit.append(f'Select card type failed with SW1 SW2 = {sw1:02X} {sw2:02X}')
                return False
        except Exception as e:
            self.uidTextEdit.append(f'Error selecting card type: {str(e)}')
            return False

    def read_memory(self, address, length):
        if address + length > self.memorySize - 1 or address < 0 or length <= 0:
            return (address, length, 'Address or length out of bounds'), False
        try:
            command = [0xFF, 0xB0, 0x00, address, length]
            data, sw1, sw2 = self.connection.transmit(command)
            if (sw1, sw2) == (0x90, 0x00):
                return (address, length, data), True
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
        try:
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

            (addr, length_read, readData), success = self.read_memory(address, length-1)
            readData = toHexString(readData)
            hexValues = readData.split()
            if success:
                protectable_memory = []
                data_memory = []
                for i in range(len(hexValues)):
                    if i < 33:
                        protectable_memory.append(hexValues[i])
                    else:
                        data_memory.append(hexValues[i])
                
                self.uidTextEdit.append(f'Addr: {addr:X}, Length: {length_read+1}')
                if protectable_memory:
                    self.uidTextEdit.append('Protectable Memory:')
                    self.uidTextEdit.append(' '.join(protectable_memory))
                if data_memory:
                    self.uidTextEdit.append('Data Memory:')
                    self.uidTextEdit.append(' '.join(data_memory))
            else:
                self.uidTextEdit.append(f'Failed to read data: {readData}')
        except Exception as e:
            self.uidTextEdit.append(f'Error reading data: {str(e)}')

    def writeCardData(self):
        try:
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
        except Exception as e:
            self.uidTextEdit.append(f'Error writing data: {str(e)}')

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
        original_value = toHexString(original_value)
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
        read_back_value = toHexString(read_back_value)  
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
