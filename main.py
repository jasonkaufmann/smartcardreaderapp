import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit
from smartcard.System import readers
from smartcard.util import toHexString

class SmartCardApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 200, 150)
        self.setWindowTitle('Smart Card Reader')

        # Layout
        layout = QVBoxLayout()

        # Text Edit
        self.uidTextEdit = QTextEdit()
        self.uidTextEdit.setReadOnly(True)
        layout.addWidget(self.uidTextEdit)

        # Read Button
        self.readButton = QPushButton('Read UID')
        self.readButton.clicked.connect(self.readCardUID)
        layout.addWidget(self.readButton)

        self.setLayout(layout)

    def readCardUID(self):
        try:
            # Get list of available readers and select the first one
            r = readers()
            reader = r[0]
            connection = reader.createConnection()
            connection.connect()

            # APDU command for getting UID
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

def main():
    app = QApplication(sys.argv)
    ex = SmartCardApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
