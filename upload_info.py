import json
import requests
from pathlib import Path
import re

# Assuming the same constants as before for the API endpoints
FORM_ENDPOINT = 'http://www.oneasysolution.com/terminal.php'
PROFILE_PICTURE_ENDPOINT = 'http://www.oneasysolution.com/terminal.php'
PROFILE_VIDEO_ENDPOINT = 'http://www.oneasysolution.com/terminal.php'
FINGERPRINT_ENDPOINT = 'http://www.oneasysolution.com/terminal.php'


def submit_file(endpoint, action, file_field_name, file_path, additional_payload=None):
    if additional_payload is None:
        additional_payload = {}
    
    # Ensure the file exists
    file_path_obj = Path(file_path)
    if not file_path_obj.is_file():
        print(f"File not found: {file_path}")
        return None

    payload = {'action': action}
    payload.update(additional_payload)
    files = {file_field_name: open(file_path, 'rb')}

    response = requests.post(endpoint, data=payload, files=files)
    return response.json()

def submit_profile_picture(data):
    return submit_file(
        PROFILE_PICTURE_ENDPOINT, 
        'submitProfilePicture', 
        'profile_picture', 
        data['profile_picture']
    )

def submit_profile_video(data):
    return submit_file(
        PROFILE_VIDEO_ENDPOINT, 
        'submitProfileVideo', 
        'profile_video', 
        data['profile_video']
    )

def extract_finger_number(filename):
    # Use regular expression to find digits in the filename
    match = re.search(r'(\d+)', filename)
    if match:
        return match.group(1)  # Return the first group of digits found
    else:
        return None  # No digits found
    
def submit_fingerprints(data):
    # Assuming data['fingerprint_images'] contains the list of filenames
    fingerprints_info = data['fingerprint_images']
    responses = []

    for fingerprint_path in fingerprints_info:
        finger_number = extract_finger_number(fingerprint_path)
        if finger_number is not None:
            response = submit_file(
                FINGERPRINT_ENDPOINT, 
                'submitFingerprint', 
                'fingerprint_image', 
                fingerprint_path,
                {'finger': finger_number}  # Use the extracted finger number
            )
            responses.append(response)
        else:
            print(f"Could not extract finger number from {fingerprint_path}")

    return responses

def submit_form(data):
    # Map the gender to the appropriate numeric value
    gender_mapping = {'Female': '0', 'Male': '1', 'Other': '2'}
    data['gender'] = gender_mapping.get(data['gender'], '')

    # Add the action to the payload
    payload = data.copy()
    payload['action'] = 'submitForm'

    response = requests.post(FORM_ENDPOINT, data=payload)
    print(response)
    return response.json()

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def main():
    # Read data from JSON file
    data = read_json_file('user_data.json')

    # Submit the form data
    form_response = submit_form(data)
    print(form_response)
    handle_response(form_response, "Form")

    # Submit the profile picture
    picture_response = submit_profile_picture(data)
    handle_response(picture_response, "Profile Picture")

   
    # Submit the profile video
    video_response = submit_profile_video(data)
    handle_response(video_response, "Profile Video")

    # Submit the fingerprints
    fingerprint_responses = submit_fingerprints(data)
    # Variable to count successful submissions
    successful_submissions = 0

    for fingerprint_response in fingerprint_responses:
        # Assuming handle_response processes each response and determines if it was successful
        if handle_response(fingerprint_response, "Fingerprint Image"):  # Update this condition based on your actual success criteria
            successful_submissions += 1

    # Print the total number of fingerprints submitted
    print(f"Total fingerprints submitted: {successful_submissions}")
    
def handle_response(response, item_name):
    if response and response.get('success'):
        print(f"{item_name} submitted successfully.")
        return True
    else:
        error = response.get('error') if response else "No response received."
        print(f"{item_name} submission failed. Error: {error}")
        return False

if __name__ == "__main__":
    main()
