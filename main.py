import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit
from smartcard.System import readers
from smartcard.util import toHexString, toBytes

class SmartCardApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Increased window size
        self.setGeometry(100, 100, 400, 300)  # Width and height increased
        self.setWindowTitle('Smart Card Reader and Writer')

        # Layout
        layout = QVBoxLayout()

        # Text Edit for UID
        self.uidTextEdit = QTextEdit()
        self.uidTextEdit.setReadOnly(True)
        layout.addWidget(self.uidTextEdit)

        # Read Button
        self.readButton = QPushButton('Read UID')
        self.readButton.clicked.connect(self.readCardUID)
        layout.addWidget(self.readButton)

        # Text Edit for writing data
        self.writeTextEdit = QTextEdit()
        layout.addWidget(self.writeTextEdit)

        # Write Button
        self.writeButton = QPushButton('Write Data')
        self.writeButton.clicked.connect(self.writeCardData)
        layout.addWidget(self.writeButton)

        self.setLayout(layout)

    def readCardUID(self):
        try:
            r = readers()
            reader = r[0]
            connection = reader.createConnection()
            connection.connect()

            command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            data, sw1, sw2 = connection.transmit(command)

            if sw1 == 0x90 and sw2 == 0x00:
                uid = toHexString(data)
                self.uidTextEdit.setText(f'Card UID: {uid}')
            else:
                self.uidTextEdit.setText('Failed to read card')

        except Exception as e:
            self.uidTextEdit.setText(f'Error: {str(e)}')

        finally:
            try:
                connection.disconnect()
            except:
                pass

    def writeCardData(self):
        try:
            r = readers()
            reader = r[0]
            connection = reader.createConnection()
            connection.connect()

            # Replace with the APDU command for your specific card type
            # Here is an example command to write data, adjust accordingly
            # APDU command structure: CLA, INS, P1, P2, Lc, Data, Le
            dataToWrite = self.writeTextEdit.toPlainText()
            command = [0xFF, 0xD6, 0x00, 0x00, len(dataToWrite)] + toBytes(dataToWrite) + [0x00]
            data, sw1, sw2 = connection.transmit(command)

            if sw1 == 0x90 and sw2 == 0x00:
                self.uidTextEdit.setText('Data written successfully')
            else:
                self.uidTextEdit.setText('Failed to write data')

        except Exception as e:
            self.uidTextEdit.setText(f'Error: {str(e)}')

        finally:
            try:
                connection.disconnect()
            except:
                pass

def main():
    app = QApplication(sys.argv)
    ex = SmartCardApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
