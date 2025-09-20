import numpy as np
import cv2
from lime import lime_image
from skimage.segmentation import mark_boundaries
import time

def generate_lime_explanation(model, frame, target_box):
    """
    Generates a LIME explanation for a given frame and target detection.
    This method is faster than SHAP and better suited for near real-time feedback.

    Args:
        model: The loaded YOLOv8 model (for context).
        frame (np.ndarray): The input image/frame of the detection.
        target_box: The specific bounding box of the detected threat.

    Returns:
        np.ndarray: An image of the LIME explanation plot, or the original frame on failure.
    """
    try:
        # A simplified prediction function for LIME. A real-world implementation
        # would run model.predict() on perturbed images and extract confidence scores.
        def predict_fn_simulator(images):
            num_images = images.shape[0]
            # Simulate a binary classification (e.g., threat vs. not-threat)
            probabilities = np.random.rand(num_images, 2)
            probabilities[:, 1] = 1 - probabilities[:, 0]  # Ensure probabilities sum to 1
            return probabilities

        # Initialize the LIME explainer
        explainer = lime_image.LimeImageExplainer(verbose=False)

        # Generate the explanation for the specific image frame
        # The 'progress_bar' argument is removed for broader compatibility with different library versions.
        explanation = explainer.explain_instance(
            frame,
            predict_fn_simulator,
            top_labels=1,
            hide_color=0,
            num_samples=150
        )

        # Create the visual explanation image
        # Get the parts of the image (superpixels) that LIME found most important
        temp, mask = explanation.get_image_and_mask(
            explanation.top_labels[0],
            positive_only=True,
            num_features=5, # Highlight the top 5 most important areas
            hide_rest=True  # Hide the rest of the image to focus the explanation
        )

        # Use skimage to draw the boundaries of these important areas on the image
        lime_image_plot = mark_boundaries(temp / 2 + 0.5, mask)
        
        # Convert the plot to a standard image format (BGR) for saving with OpenCV
        lime_image_plot = (lime_image_plot * 255).astype(np.uint8)
        lime_image_plot = cv2.cvtColor(lime_image_plot, cv2.COLOR_RGB2BGR)
        
        return lime_image_plot

    except Exception as e:
        print(f"[XAI LIME ERROR] Could not generate LIME explanation: {e}")
        return None

