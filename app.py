from flask import Flask, Response, send_file, render_template,request
from flask import Flask, render_template, request, jsonify
from picamera2 import Picamera2, Preview
from io import BytesIO
import cv2
from linedrawer import ImageSketcher
import numpy as np
import base64
from io import BytesIO
from PIL import Image,ImageDraw
from watermark_adder import Watermarkadder
from background_remover import Backgroundremover
from rembg import remove

sketcher = ImageSketcher()

app = Flask(__name__)

bg_remover = Backgroundremover()
watermark_adder = Watermarkadder()
# Initialize the camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

@app.route('/')
def index():
    """Serve the HTML page."""
    return render_template('index.html')  # Map to the HTML file

@app.route('/video_feed')
def video_feed():
    """Stream the live video feed from the camera."""
    def generate():
        while True:
            frame = picam2.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_image')
def capture_image():
    """Capture an image from the camera."""
    frame = picam2.capture_array()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    _, buffer = cv2.imencode('.jpg', rgb_frame)
    image_io = BytesIO(buffer)
    return send_file(image_io, mimetype='image/jpeg')



@app.route('/convert', methods=['POST'])
def convert():
    data_url = request.json.get('image')
    header, encoded = data_url.split(",", 1)
    image_data = base64.b64decode(encoded)
    image = Image.open(BytesIO(image_data)).convert("RGBA")
    image = bg_remover.remove_background(image)
    #image = watermark_adder.watermark_at_top_right(image)
    sketcher = ImageSketcher()
    lines = sketcher.sketch(image)  # Directly pass the image to the sketch method
    # Create a new image to draw the lines on, based on the resolution from ImageSketcher
    disp = Image.new("RGB", (sketcher.resolution, sketcher.resolution * image.height // image.width), (255, 255, 255))
    draw = ImageDraw.Draw(disp)
    for l in lines:
        draw.line(l, (0, 0, 0), 5)

    # Save the image to a buffer
    buffered = BytesIO()
    disp.save(buffered, format="PNG")
    sketch_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    watermark_adder.print_watermark_info("output/out.svg")  # Print watermark information to console
    
    return jsonify({'linedraw': f"data:image/png;base64,{sketch_image_base64}",
                    'image': f"data:image/png;base64,{image}",})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
