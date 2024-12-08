import cv2
import numpy as np
from PIL import Image
from lxml import etree
import re
class Watermarkadder:
    
    def __init__(self):
        pass
    def watermark_at_top_right(self, image):
        logo = cv2.imread("static/THD_logo.jpg")
        image = np.array(image)
        image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        logo = cv2.resize(logo, None, fx=0.75, fy=0.75, interpolation=cv2.INTER_AREA)
        h1, w1, _ = image.shape
        h2, w2, _ = logo.shape
        # Calculate the position to place the smaller image on the larger image
        x_offset = w1 - w2
        y_offset = 0
        roi = image[y_offset:y_offset+h2, x_offset:x_offset+w2]
        result = cv2.addWeighted(roi, 0.8, logo, 0.2, 0)
        image[y_offset:y_offset+h2, x_offset:x_offset+w2] = result
        image  = Image.fromarray(image)
        return image
    

    def extract_numeric(self,value):
    # Ensure value is a string and remove any non-numeric characters (e.g., 'px', 'pt')
        if isinstance(value, str):
            numeric_value = re.sub(r'[^\d.]+', '', value)
            return float(numeric_value)
        return float(value)
    
    def print_watermark_info(self,file_path):
        with open(file_path, "r") as file:
            main_svg = etree.parse(file)

# Load the logo SVG file
        with open("static/logo.svg", "r") as file:
            logo_svg = etree.parse(file)

        # Get the root elements of both SVGs
            main_root = main_svg.getroot()
            logo_root = logo_svg.getroot()

            # Extract and convert the width and height of the main SVG
            main_width = self.extract_numeric(main_root.get("width", "500px"))
            main_height = self.extract_numeric(main_root.get("height", "500px"))

            # Extract and convert the width and height of the logo SVG
            logo_width = self.extract_numeric(logo_root.get("width", "100px"))
            logo_height = self.extract_numeric(logo_root.get("height", "100px"))

            # Set the position of the logo in the right corner
            logo_root.set("x", str(main_width - logo_width))
            logo_root.set("y", str(0))

            # Append the logo to the main SVG
            main_root.append(logo_root)

            # Save the combined SVG to a new file
            with open("output/combined_output.svg", "wb") as output_file:
                output_file.write(etree.tostring(main_svg, pretty_print=True))