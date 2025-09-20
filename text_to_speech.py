import pyttsx3
import threading
import queue

class TextToSpeech:
    """
    A robust, thread-safe Text-to-Speech engine designed for clarity and reliability.
    It runs in its own dedicated thread to prevent blocking the main application,
    ensuring smooth performance even during long announcements.
    """
    def __init__(self):
        self.speak_queue = queue.Queue()
        self.engine_thread = threading.Thread(target=self._run_engine, daemon=True)
        # Use a threading.Event for safe and clean thread termination.
        self.is_running = threading.Event()
        self.is_running.set()
        self.engine_thread.start()
        print("--- Text-to-Speech System Initialized ---")

    def _run_engine(self):
        """
        The main loop for the TTS engine thread. It initializes the engine,
        waits for text to appear in the queue, and then speaks it. This architecture
        solves the issue of the voice only playing once.
        """
        engine = None
        try:
            engine = pyttsx3.init()
            # --- IMPROVED SPEECH RATE ---
            # The rate is adjusted for a clear, understandable, and professional pace.
            # Not too fast, not too slow.
            rate = engine.getProperty('rate')
            engine.setProperty('rate', rate + 40) # Slower than previous versions for better clarity
            
            # Attempt to use a female voice if available, which can sometimes be clearer on comms.
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"[TTS INIT ERROR] Could not initialize TTS engine: {e}. Voice alerts will be disabled.")
            self.is_running.clear()
            return

        # The main loop continues as long as the is_running event is set.
        while self.is_running.is_set():
            try:
                # Wait for a message to appear in the queue.
                text = self.speak_queue.get(timeout=1) # Timeout prevents it from blocking forever.
                
                # A 'None' value in the queue is our signal to stop the thread gracefully.
                if text is None:
                    self.is_running.clear()
                    continue
                
                engine.say(text)
                engine.runAndWait()
                self.speak_queue.task_done()
            except queue.Empty:
                # This is normal, just means no one is talking. The loop continues.
                continue
            except Exception as e:
                print(f"[TTS ENGINE ERROR] An error occurred during speech: {e}")
                # Ensure the queue task is marked as done even on error to prevent deadlocks.
                if not self.speak_queue.empty():
                    try:
                        self.speak_queue.task_done()
                    except ValueError:
                        pass # Ignore errors if task_done is called multiple times

    def speak(self, text):
        """Adds a new text message to the queue to be spoken by the engine."""
        if self.is_running.is_set():
            self.speak_queue.put(text)

    def stop(self):
        """Gracefully stops the TTS engine and its background thread."""
        try:
            if self.is_running.is_set():
                print("--- TTS System shutting down ---")
                self.is_running.clear() 
                self.speak_queue.put(None) # Send the sentinel to exit the loop
                # Wait for the thread to finish processing its current task.
                self.engine_thread.join(timeout=2) 
        except Exception as e:
            print(f"[TTS STOP ERROR] {e}")

