import cv2
import json

def capture_image_with_live_view():
    # Initialize the camera
    cap = cv2.VideoCapture(0)  # 0 is usually the default camera

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Press 'SPACE' to capture the image, 'ESC' to exit...")

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # If frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # Display the resulting frame
        cv2.imshow('Press SPACE to capture, ESC to exit', frame)

        # Wait for the SPACE key to be pressed to capture the image
        key = cv2.waitKey(1)
        if key % 256 == 32:  # If SPACE key is pressed
            file_path = "captured_image.jpg"
            cv2.imwrite(file_path, frame)
            print(f"Image saved to {file_path}")
            update_user_data(file_path)
            break
        elif key % 256 == 27:  # If ESC key is pressed
            print("Exiting without capture.")
            break

    # When everything done, release the capture and destroy any OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

def update_user_data(file_name):
    user_data_file = 'user_data.json'
    new_data = {'profile_picture': file_name}

    # Check if user_data.json exists and read its content; if not, create an empty dictionary
    try:
        with open(user_data_file, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    # Update the data with the new profile picture
    data.update(new_data)

    # Write the updated data back to user_data.json
    with open(user_data_file, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Profile picture updated in {user_data_file}.")

# Start the live view and wait for the user to capture an image
capture_image_with_live_view()
