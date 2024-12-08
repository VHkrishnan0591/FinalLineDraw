from rembg import remove
import numpy as np
from PIL import Image

class Backgroundremover:
    def __init__(self):
        pass
    
    def remove_background(self, image):
        print("into remove background")
        
        output = remove(image)
        
        # Convert output to numpy array to work with OpenCV functions
        output_np = np.array(output)

        height, width = output_np.shape[:2]
        # Create a white background (255, 255, 255 for RGB white)
        background = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Extract RGB and Alpha channels
        rgb = output_np[:, :, :3]
        alpha = output_np[:, :, 3] / 255.0  # Normalize alpha to 0-1 range

        # Overlay the RGB array onto the white background using alpha transparency
        for c in range(3):
            background[:, :, c] = (alpha * rgb[:, :, c] + (1 - alpha) * background[:, :, c]).astype(np.uint8)
        
        # Convert the numpy array back to a PIL image
        image = Image.fromarray(background)
        return image
