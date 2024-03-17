import json
import sys
from card_reader import SmartCardApp  # Import your main class or functions from card_reader.py
from PyQt5.QtWidgets import QApplication  
from PyQt5.QtWidgets import QTextEdit  


def read_json_data(file_path):
    """Reads data from a JSON file and returns it."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def write_and_verify_data_on_card(app, data):
    """Writes data to the AT24C64 chip, updates the GUI, and verifies the write operation."""
    # Convert the entire data dictionary to a formatted string for display and writing
    text_data = json.dumps(data, indent=4)
    
    print("Updating the GUI with data...")
    if hasattr(app, 'basicTextInput') and isinstance(app.basicTextInput, QTextEdit):
        app.basicTextInput.setText(text_data)  # Update the widget's text
        print(text_data)
    else:
        print("The basicTextInput field is not accessible.")
    
    # Write data to card
    app.writeAsciiToCard()  

    # Read back data from card for verification
    app.readAsciiFromCard()  
    read_back_data = app.readDataTextArea.toPlainText()

    #print("Data read back from the card:", read_back_data)

    # Verify if the written data matches the read back data
    if read_back_data.strip() == text_data.strip():
        print("Data verification successful: Data written matches data read back.")
    else:
        print("Data verification failed: Written data does not match read back data.")

def main(file_path):
    applic = QApplication(sys.argv)
    app = SmartCardApp()
    #app.show()
    
    data = read_json_data(file_path)
    print(type(data))
    
    try:
        print("Writing data to the card...")

        app.set_chip_family("AT24C64")
        
        write_and_verify_data_on_card(app, data)

    except Exception as e:
        print(f"An error occurred: {e}")

    #sys.exit(applic.exec_())

if __name__ == '__main__':
    
    json_file_path = "user_data.json"
    main(json_file_path)
