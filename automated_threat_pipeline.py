# automated_threat_pipeline.py
# A fully automated script that detects threats, encrypts the alerts,
# and simulates sending them to a server for decryption and LLM processing in real-time.

import cv2
from ultralytics import YOLO
from secure_comm import SecureChannel # We import our existing encryption module
import os

# --- 1. KEY MANAGEMENT ---
# In a real application, this key would be securely stored and distributed.
KEY_FILE = "secret.key"

def load_or_generate_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    else:
        key = SecureChannel.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    return key

# --- 2. LLM PROCESSING (SIMULATION) ---
def process_for_llm(decrypted_alert: str):
    """
    Simulates sending a decrypted alert to a Large Language Model for analysis.
    """
    print("      >> Sending to LLM for analysis...")
    # This is where you would make an API call to your LLM.
    llm_response = f"ACTIONABLE INTEL: A {decrypted_alert.split(' ')[1]} has been confirmed. Threat level assessed."
    print(f"      >> LLM Response: '{llm_response}'")


# --- 3. SERVER-SIDE PROCESSING (SIMULATION) ---
def simulate_server_processing(encrypted_packet: bytes, decryptor: SecureChannel):
    """
    Simulates the server receiving an encrypted packet, decrypting it,
    and passing it on for further processing.
    """
    print("   -> Server received encrypted packet. Decrypting...")
    decrypted_message = decryptor.decrypt_message(encrypted_packet)

    if decrypted_message:
        print(f"   -> Decryption SUCCESSFUL. Original Alert: '{decrypted_message}'")
        # Now that the message is clean, send it to the LLM.
        process_for_llm(decrypted_message)
    else:
        print("   -> Decryption FAILED.")


# --- 4. MAIN DETECTION AND ENCRYPTION PIPELINE ---
def run_automated_pipeline():
    # Setup the encryption/decryption channel with a shared key
    secret_key = load_or_generate_key()
    encryptor = SecureChannel(key=secret_key)
    decryptor = SecureChannel(key=secret_key) # The server would have the same key
    print(f"Secure channel established using key from '{KEY_FILE}'.")

    # Load your custom-trained YOLO model
    model_path = os.path.join('runs', 'detect', 'SarvDrishti_Threat_Detector_v13', 'weights', 'best.pt')
    model = YOLO(model_path)
    print(f"YOLO model loaded from '{model_path}'.")

    # Open the video file
    video_path = "local.mp4"
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file '{video_path}'.")
        return
    
    print("\n--- Starting Automated Threat Detection Pipeline ---")
    print("Press 'q' in the video window to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("\n--- End of video stream. ---")
            break

        # Perform object detection on the frame
        results = model.predict(frame, verbose=False, conf=0.4)
        annotated_frame = results[0].plot()

        # Iterate through detected objects
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])
            
            # --- THE AUTOMATED WORKFLOW ---
            print("\n[STEP 1: THREAT DETECTED]")
            alert_message = f"ALERT! {class_name} detected with confidence {confidence:.2f}"
            print(f"   - Original Alert: '{alert_message}'")

            print("[STEP 2: ENCRYPTING ALERT]")
            encrypted_packet = encryptor.encrypt_message(alert_message)
            print(f"   - Encrypted Packet (sent over network): {encrypted_packet[:60]}...")

            print("[STEP 3: SERVER PROCESSING]")
            # This function call simulates the entire server-side process automatically
            simulate_server_processing(encrypted_packet, decryptor)
            
        # Display the live video feed with detections
        cv2.imshow("Automated Threat Pipeline", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Pipeline finished.")

if __name__ == "__main__":
    run_automated_pipeline()
    video_path = "local.mp4"
    model_path = os.path.join('runs', 'detect', 'SarvDrishti_Threat_Detector_v13', 'weights', 'best.pt')
    TARGET_OBJECTS = ["drone","tank","missile"]
    run_object_detection(video_path, model_path)
from detect import run_object_detection