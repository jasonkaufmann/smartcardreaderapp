import cv2
import subprocess
import datetime
import os
import threading

def capture_audio(start_event, stop_event, output_file="output_audio.wav", duration=10):
    start_event.wait()  # Waits for the signal to start recording
    if stop_event.is_set():
        return  # Exit if stop event is set before starting
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'dshow',
        '-i', 'audio=Microphone Array (Intel® Smart Sound Technology for Digital Microphones)',
        '-t', str(duration),
        '-y',  # Overwrite output files without asking
        output_file
    ]
    subprocess.run(ffmpeg_command, check=True)
    print(f"Audio successfully saved to {output_file}")

def capture_video_with_audio(video_file="output_video.mp4", audio_file="output_audio.wav", duration=10):
    start_event = threading.Event()
    stop_event = threading.Event()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_file, fourcc, 20.0, (640, 480))
    
    # Wait for SPACE bar press to start recording or ESC to exit
    print("Press SPACE to start recording or ESC to exit...")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to get video frame.")
            break
        cv2.imshow('Press SPACE to start recording or ESC to exit', frame)
        key = cv2.waitKey(1)
        if key == ord(' '):
            break
        elif key == 27:  # ESC key
            cap.release()
            cv2.destroyAllWindows()
            stop_event.set()
            return
    
    if not stop_event.is_set():
        # Start audio recording in a separate thread
        audio_thread = threading.Thread(target=capture_audio, args=(start_event, stop_event, audio_file, duration))
        audio_thread.start()

        print("Recording started...")
        start_event.set()  # Signals the audio recording to start
        start_time = datetime.datetime.now()

        while (datetime.datetime.now() - start_time).seconds < duration:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            cv2.imshow('Press SPACE to start recording or ESC to exit', frame)
            if cv2.waitKey(1) == 27:  # ESC key
                stop_event.set()
                break
        
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        audio_thread.join()  # Wait for audio recording to finish
        if stop_event.is_set():
            print("Recording stopped early.")
        else:
            merge_audio_video(video_file, audio_file, "final_output.mp4")
            print("Recording finished. Video and audio have been merged.")

def merge_audio_video(video_file, audio_file, output_file="final_output.mp4"):
    ffmpeg_command = [
        'ffmpeg',
        '-i', video_file,
        '-i', audio_file,
        '-shortest',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-strict', 'experimental',
        '-y',
        output_file
    ]
    subprocess.run(ffmpeg_command, check=True)
    print(f"Video and audio successfully merged into {output_file}")

# Set the duration for recording here
duration = 10  # 10 seconds
capture_video_with_audio(duration=duration)
