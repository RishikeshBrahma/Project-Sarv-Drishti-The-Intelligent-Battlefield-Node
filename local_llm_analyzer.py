from llama_cpp import Llama
import os

class LocalLlmAnalyzer:
    """
    A class to handle loading the local GGUF model and running inference.
    This replaces the need for an external API call for AI reasoning.
    """
    def __init__(self, model_path):
        """
        Initializes the analyzer and loads the TinyLlama model into memory.
        """
        if not os.path.exists(model_path):
            # Provides a clear error if the model file is missing.
            raise FileNotFoundError(
                f"[FATAL ERROR] LLM model file not found at '{model_path}'. "
                f"Please ensure the model has been downloaded and the path is correct in detect.py."
            )
        
        # Load the GGUF model using llama-cpp-python.
        # n_gpu_layers=0 ensures it runs on the CPU, which is best for compatibility.
        self.llm = Llama(
            model_path=model_path, 
            n_gpu_layers=0, 
            verbose=False, 
            n_ctx=2048 # Context window size
        )
        print("Local TinyLlama model loaded successfully into memory.")

    def run_analysis(self, alert_data):
        """
        Takes alert data, formats it into a professional prompt with multiple examples, 
        and gets a tactical profile from the local TinyLlama model.
        """
        # This "Few-Shot" prompt provides an example for each class, teaching the 
        # model the specific output format and tone for each threat type.
        prompt = f"""<|system|>
You are Sarv Drishti, an AI Tactical Analysis Unit. Your mission is to provide a concise intelligence report. Use direct, clear military language. State the threat classification, threat level, location, a brief assessment, and key vulnerabilities.</s>
<|user|>
GENERATE TACTICAL PROFILE FOR:
- TYPE: tank
- LOCATION: 34.553900 N, 76.133200 E
- CONFIDENCE: High</s>
<|assistant|>
THREAT PROFILE:
- CLASSIFICATION: Main Battle Tank
- THREAT LEVEL: Critical
- LOCATION: Est. 34.5539 N, 76.1332 E
- ASSESSMENT: Primary offensive armored platform, effective against ground forces and structures.
- VULNERABILITIES: Anti-armor munitions, air support, IEDs.</s>
<|user|>
GENERATE TACTICAL PROFILE FOR:
- TYPE: drone
- LOCATION: 34.554210 N, 76.133500 E
- CONFIDENCE: Moderate</s>
<|assistant|>
THREAT PROFILE:
- CLASSIFICATION: Unmanned Aerial Vehicle (UAV)
- THREAT LEVEL: Medium
- LOCATION: Est. 34.5542 N, 76.1335 E
- ASSESSMENT: Potential reconnaissance or light attack drone. Capable of loitering and providing real-time intelligence.
- VULNERABILITIES: Electronic warfare (jamming), anti-air guns, MANPADS.</s>
<|user|>
GENERATE TACTICAL PROFILE FOR:
- TYPE: helicopter
- LOCATION: 34.555000 N, 76.134000 E
- CONFIDENCE: High</s>
<|assistant|>
THREAT PROFILE:
- CLASSIFICATION: Attack Helicopter
- THREAT LEVEL: High
- LOCATION: Est. 34.5550 N, 76.1340 E
- ASSESSMENT: Air-to-ground threat posing a direct danger to ground personnel and armored units.
- VULNERABILITIES: Anti-aircraft systems (MANPADS, SAMs), heavy machine gun fire.</s>
<|user|>
GENERATE TACTICAL PROFILE FOR:
- TYPE: {alert_data['class']}
- LOCATION: {alert_data['loc']}
- CONFIDENCE: {alert_data['qual_conf']}</s>
<|assistant|>
"""
        
        # Run inference on the loaded model
        output = self.llm(
            prompt, 
            max_tokens=150, 
            echo=False, 
            stop=["</s>", "<|user|>"], 
            temperature=0.1
        )
        
        # Safely extract and return the generated text

        response = output['choices'][0]['text'].strip()

        # Send the tactical profile to Django API
        self.send_alert_to_django(alert_data, response)
        return response

    def send_alert_to_django(self, alert_data, tactical_profile):
        import requests
        payload = {
            "threat_type": alert_data.get("class"),
            "location": alert_data.get("loc"),
            "confidence": alert_data.get("qual_conf"),
            "profile": tactical_profile
        }
        try:
            response = requests.post("http://localhost:8000/api/v1/alerts/", json=payload)
            print("Alert sent:", response.status_code, response.text)
        except Exception as e:
            print("Failed to send alert:", e)

