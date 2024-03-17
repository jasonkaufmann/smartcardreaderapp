import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFormLayout, QLineEdit, QLabel, QPushButton, QRadioButton, 
    QButtonGroup, QVBoxLayout, QHBoxLayout, QComboBox
)
import pycountry
import pytz

class InformationForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Information Form')
        self.resize(400, 600)

        # Create layout
        layout = QFormLayout()

        # Gender
        self.gender_group = QButtonGroup(self)
        male_rb = QRadioButton("Male")
        female_rb = QRadioButton("Female")
        other_rb = QRadioButton("Other")
        self.gender_group.addButton(male_rb)
        self.gender_group.addButton(female_rb)
        self.gender_group.addButton(other_rb)

        gender_layout = QHBoxLayout()
        gender_layout.addWidget(male_rb)
        gender_layout.addWidget(female_rb)
        gender_layout.addWidget(other_rb)

        # Input Fields
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.other_names_input = QLineEdit()
        self.email_input = QLineEdit()
        # Input Fields for Country and State as QLineEdit instead of QComboBox
        # Country dropdown list with pycountry
         # Country dropdown list with pycountry
        self.country_input = QComboBox()
        self.countries = {country.name: country.alpha_2 for country in pycountry.countries}
        self.country_input.addItems(sorted(self.countries.keys()))  # Sort countries alphabetically
        self.country_input.currentIndexChanged.connect(self.update_state_province_dropdown)

        # State/Province/Territory dropdown list
        self.state_input = QComboBox()


        # Initialize the state dropdown for the first selected country
        self.update_state_province_dropdown()

          # Timezone dropdown list with pytz
        self.timezone_input = QComboBox()
        self.timezone_input.addItems(sorted(pytz.all_timezones))  # Add all timezones from pytz



        # Separation line 1
        separator_1 = QLabel("-----------")

        # Contact Information
        self.country_phone_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_line1_input = QLineEdit()
        self.address_line2_input = QLineEdit()
        self.city_input = QLineEdit()
        self.postal_code_input = QLineEdit()

        # Separation line 2
        separator_2 = QLabel("-----------")

        # Account Information
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.retype_password_input = QLineEdit()
        self.retype_password_input.setEchoMode(QLineEdit.Password)
        self.passcode_input = QLineEdit()
        self.passcode_input.setEchoMode(QLineEdit.Password)
        self.retype_passcode_input = QLineEdit()
        self.retype_passcode_input.setEchoMode(QLineEdit.Password)

        # Load Button
        load_button = QPushButton('Load from JSON')
        load_button.clicked.connect(self.load_from_json)
        
        # Save Button
        save_button = QPushButton('Save to JSON')
        save_button.clicked.connect(self.save_to_json)

         # Add widgets to layout
        layout.addRow('Gender:', gender_layout)
        layout.addRow('First Name:', self.first_name_input)
        layout.addRow('Last Name:', self.last_name_input)
        layout.addRow('Other Names:', self.other_names_input)
        layout.addRow('Email:', self.email_input)
        layout.addRow('Country:', self.country_input)
        layout.addRow('Timezone:', self.timezone_input)
        layout.addRow(separator_1)
        layout.addRow('Country Phone Code:', self.country_phone_input)
        layout.addRow('Phone:', self.phone_input)
        layout.addRow('Address Line 1:', self.address_line1_input)
        layout.addRow('Address Line 2:', self.address_line2_input)
        layout.addRow('City:', self.city_input)
        layout.addRow('State/Province/Territory:', self.state_input)
        layout.addRow('Postal Code:', self.postal_code_input)
        layout.addRow(separator_2)
        layout.addRow('Username:', self.username_input)
        layout.addRow('Password:', self.password_input)
        layout.addRow('Retype Password:', self.retype_password_input)
        layout.addRow('Passcode:', self.passcode_input)
        layout.addRow('Retype Passcode:', self.retype_passcode_input)
        # Layout adjustments to add the load button
        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(load_button)
        layout.addRow(button_layout)
        self.setLayout(layout)

    def load_from_json(self):
        try:
            with open('user_data.json', 'r') as json_file:
                data = json.load(json_file)
                
            # Populate the fields with loaded data
            # Assuming gender options are Male, Female, Other as per your setup
            gender_buttons = self.gender_group.buttons()
            for button in gender_buttons:
                if button.text() == data.get('gender', ''):
                    button.setChecked(True)
                    
            self.first_name_input.setText(data.get('first_names', ''))
            self.last_name_input.setText(data.get('last_names', ''))
            self.other_names_input.setText(data.get('other_names', ''))
            self.email_input.setText(data.get('email', ''))
            self.country_input.setCurrentText(data.get('country', ''))
            self.timezone_input.setCurrentText(data.get('timezone', ''))
            self.country_phone_input.setText(data.get('country_phone', ''))
            self.phone_input.setText(data.get('phone', ''))
            self.address_line1_input.setText(data.get('address_line_1', ''))
            self.address_line2_input.setText(data.get('address_line_2', ''))
            self.city_input.setText(data.get('city', ''))
            # Ensure the state dropdown is updated based on the loaded country
            self.update_state_province_dropdown()
            self.state_input.setCurrentText(data.get('state_province_territory', ''))
            self.postal_code_input.setText(data.get('postal_code', ''))
            self.username_input.setText(data.get('username', ''))
            self.password_input.setText(data.get('password', ''))
            self.retype_password_input.setText(data.get('password', ''))  # Assuming you want to autofill this for display
            self.passcode_input.setText(data.get('passcode', ''))
            self.retype_passcode_input.setText(data.get('passcode', ''))  # Assuming you want to autofill this for display
            
            print("Data loaded from user_data.json")
        except FileNotFoundError:
            print("user_data.json file not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON from file.")

    def update_state_province_dropdown(self):
        # Clear current items
        self.state_input.clear()

        # Get selected country code
        country_code = self.countries.get(self.country_input.currentText())
        if not country_code:
            return

        # Find subdivisions for the selected country
        subdivisions = list(pycountry.subdivisions.get(country_code=country_code))

        # Update the state/province/territory dropdown
        self.state_input.addItems(sorted([subdivision.name for subdivision in subdivisions]))

    def save_to_json(self):
        # Load existing data from the file
        existing_data = {}
        try:
            with open('user_data.json', 'r') as json_file:
                existing_data = json.load(json_file)
        except FileNotFoundError:
            print("user_data.json file not found. A new file will be created.")
        except json.JSONDecodeError:
            print("Error decoding JSON from the existing file. Overwriting with new data.")

        # Retrieve information from the form and update existing data
        existing_data.update({
            'gender': self.gender_group.checkedButton().text() if self.gender_group.checkedButton() else '',
            'first_names': self.first_name_input.text(),
            'last_names': self.last_name_input.text(),
            'other_names': self.other_names_input.text(),
            'email': self.email_input.text(),
            'country': self.country_input.currentText(),
            'timezone': self.timezone_input.currentText(),
            'phone': self.phone_input.text(),
            'address_line_1': self.address_line1_input.text(),
            'address_line_2': self.address_line2_input.text(),
            'city': self.city_input.text(),
            'state_province_territory': self.state_input.currentText(),
            'postal_code': self.postal_code_input.text(),
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'passcode': self.passcode_input.text()
        })

        # Validate passwords and passcodes
        if existing_data['password'] != self.retype_password_input.text():
            print("Passwords do not match.")
            return  # You might want to add a user-visible error message here
        
        if existing_data['passcode'] != self.retype_passcode_input.text():
            print("Passcodes do not match.")
            return  # You might want to add a user-visible error message here

        # Save the updated data back to the JSON file
        with open('user_data.json', 'w') as json_file:
            json.dump(existing_data, json_file, indent=4)

        print("Data saved to user_data.json")
# The rest of your application code, including instantiation of the app and form
def main():
    app = QApplication(sys.argv)
    form = InformationForm()
    form.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
