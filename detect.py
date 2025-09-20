import cv2
import os
import threading
import queue
import time
from ultralytics import YOLO
from secure_comm import SecureChannel
from text_to_speech import TextToSpeech
from xai_analyzer import generate_lime_explanation
from local_llm_analyzer import LocalLlmAnalyzer

# --- CONFIGURATION ---
YOLO_MODEL_PATH = 'best.pt' 
SOURCE_VIDEO_PATH = 'local.mp4'
LLM_MODEL_PATH = os.path.join("models", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
XAI_OUTPUT_FOLDER = "xai_outputs"
NUM_ANALYSIS_WORKERS = 2 
# ---

def get_simulated_gps_location(box, frame_width, frame_height, base_coords, scale_factor=0.0001):
    """Converts a bounding box's pixel location to a simulated GPS coordinate."""
    base_lat, base_lon = base_coords
    x1, y1, x2, y2 = box.xyxy[0]
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    offset_x = center_x - (frame_width / 2)
    offset_y = (frame_height / 2) - center_y 
    lat_offset = offset_y * (scale_factor / frame_height)
    lon_offset = offset_x * (scale_factor / frame_width)
    new_lat = base_lat + lat_offset
    new_lon = base_lon + lon_offset
    lat_dir = "N" if new_lat >= 0 else "S"
    lon_dir = "E" if new_lon >= 0 else "W"
    return f"{abs(new_lat):.6f} {lat_dir}, {abs(new_lon):.6f} {lon_dir}"

def get_qualitative_confidence(score):
    """Converts a numerical confidence score to a qualitative level."""
    if score > 0.75: return "High"
    elif score > 0.4: return "Moderate"
    else: return "Low"

def analysis_worker(worker_id, alert_queue, encryptor, tts_engine, yolo_model, llm_analyzer):
    """
    A worker thread that now handles ALL slow tasks: XAI, Encryption, and Local LLM Analysis.
    This architecture ensures the main video display thread remains perfectly smooth.
    """
    print(f"--- Analysis Worker-{worker_id} Ready ---")
    while True:
        try:
            alert_data = alert_queue.get()
            if alert_data is None:
                break

            class_name = alert_data.get('class')
            print(f"\n--- [Worker-{worker_id} PROCESSING: {class_name}] ---")
            
            # XAI LIME analysis is now handled in the background to prevent video lag.
            print(f"  [Worker-{worker_id}] Generating XAI LIME Explanation for {class_name}...")
            lime_image = generate_lime_explanation(yolo_model, alert_data['frame'], alert_data['box'])
            if lime_image is not None:
                xai_path = os.path.join(XAI_OUTPUT_FOLDER, f"threat_{class_name}_{int(time.time())}_LIME.jpg")
                cv2.imwrite(xai_path, lime_image)
                print(f"  [Worker-{worker_id}] XAI plot saved to: {xai_path}")

            # --- CORRECTED ENCRYPTION STEP ---
            print(f"  [Worker-{worker_id}] STEP 2: ENCRYPTING ALERT]")
            encrypted_packet = encryptor.encrypt_message(alert_data)
            if not encrypted_packet:
                print(f"  [Worker-{worker_id} ERROR] Encryption failed.")
                alert_queue.task_done()
                continue
            
            # This print statement provides the visual confirmation that encryption is working.
            print(f"  - Encrypted Packet: {encrypted_packet[:40]}...")

            print(f"  [Worker-{worker_id}] STEP 3: SERVER PROCESSING & AI ANALYSIS]")
            decrypted_data = encryptor.decrypt_message(encrypted_packet)

            if decrypted_data:
                tactical_profile = llm_analyzer.run_analysis(decrypted_data)
                print(f"\n  [Worker-{worker_id}] TACTICAL PROFILE:\n{tactical_profile}")

                speakable_response = f"New Tactical Profile. {tactical_profile}".replace('\n', ' ').replace('-', ' ')
                print(f"\n  [Worker-{worker_id}] STEP 4: VOCALIZING DIRECTIVE]")
                tts_engine.speak(speakable_response)
            else:
                print(f"  [Worker-{worker_id}] Decryption failed.")
            alert_queue.task_done()
        except Exception as e:
            print(f"[WORKER-{worker_id} ERROR] An error occurred: {e}")
            alert_queue.task_done()
    print(f"--- Analysis Worker-{worker_id} Stopped ---")

def main():
    """Main function to initialize and run the full pipeline."""
    BASE_COORDINATE = (34.5539, 76.1332) 
    os.makedirs(XAI_OUTPUT_FOLDER, exist_ok=True)

    if not all(os.path.exists(p) for p in [YOLO_MODEL_PATH, SOURCE_VIDEO_PATH, LLM_MODEL_PATH]):
        print(f"\n[FATAL ERROR] A required file (YOLO model, Video, or LLM model) was not found.")
        return
    print("All necessary files found.")

    tts_engine = None
    worker_threads = []
    try:
        yolo_model = YOLO(YOLO_MODEL_PATH)
        llm_analyzer = LocalLlmAnalyzer(model_path=LLM_MODEL_PATH)
        encryptor = SecureChannel()
        tts_engine = TextToSpeech()
        alert_queue = queue.Queue()
        processed_threat_classes = set()
        
        print("All models and modules loaded successfully.")

        for i in range(NUM_ANALYSIS_WORKERS):
            thread = threading.Thread(target=analysis_worker, args=(i + 1, alert_queue, encryptor, tts_engine, yolo_model, llm_analyzer), daemon=True)
            thread.start()
            worker_threads.append(thread)

        cap = cv2.VideoCapture(SOURCE_VIDEO_PATH)
        if not cap.isOpened(): raise IOError(f"Cannot open video file: {SOURCE_VIDEO_PATH}")
            
        print("\n--- Starting Real-Time Threat Tracking & Analysis Pipeline ---")

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            frame_height, frame_width, _ = frame.shape
            results = yolo_model(frame, stream=False, verbose=False)
            annotated_frame = results[0].plot()

            if results[0].boxes:
                for box in results[0].boxes:
                    class_name = yolo_model.names[int(box.cls[0])]
                    
                    if class_name not in processed_threat_classes:
                        processed_threat_classes.add(class_name)
                        
                        confidence = float(box.conf[0])
                        qualitative_confidence = get_qualitative_confidence(confidence)
                        location = get_simulated_gps_location(box, frame_width, frame_height, BASE_COORDINATE)
                        
                        alert_data = {
                            "class": class_name, 
                            "loc": location, 
                            "conf": confidence, 
                            "qual_conf": qualitative_confidence,
                            "frame": frame.copy(),
                            "box": box 
                        }
                        
                        alert_str = (f"ALERT! First detection of class '{alert_data['class']}' at "
                                     f"coords {alert_data['loc']} with confidence {alert_data['conf']:.2f}")

                        print(f"\n[STEP 1: NEW THREAT CLASS DETECTED] - {alert_str}")
                        alert_queue.put(alert_data)

            cv2.imshow("Sarv Drishti - Live Feed", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n'q' pressed. Shutting down gracefully...")
                break

    except Exception as e:
        print(f"\n[FATAL ERROR IN MAIN] An unexpected error occurred: {e}")

    finally:
        print("\n--- Cleaning up... ---")
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        
        if 'alert_queue' in locals():
            for _ in worker_threads:
                alert_queue.put(None) 
            for thread in worker_threads:
                thread.join()

        if tts_engine is not None:
            tts_engine.stop()
        
        print("--- Pipeline Finished ---")

if __name__ == "__main__":
    main()

