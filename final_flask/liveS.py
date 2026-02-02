import cv2
import time
from threading import Thread, Lock
from flask import Flask, Response
from flask_basicauth import BasicAuth

# Optimized Webcam class with minimal buffering and latency
class WebcamVideoStream:
    def __init__(self, src=0):
        print("Initializing camera...")
        self.stream = cv2.VideoCapture(src)
        
        # Aggressive camera optimization settings
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)      # Minimum buffer size
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Reasonable resolution
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  
        self.stream.set(cv2.CAP_PROP_FPS, 30)            # Target FPS
        
        # Try to disable auto focus which can cause periodic delays
        self.stream.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        
        # For some cameras, lower quality can reduce latency
        self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        self.lock = Lock()  # Thread synchronization
        
        # Start the thread to read frames
        Thread(target=self.update, daemon=True).start()
        
    def update(self):
        last_frame_time = time.time()
        while not self.stopped:
            # Skip frames if we're running behind (helps reduce latency)
            current_time = time.time()
            if current_time - last_frame_time < 0.01:  # Max ~100fps internal processing
                continue
                
            # Get the latest frame and clear the buffer
            for _ in range(2):  # Try to clear any buffered frames
                if self.stream.isOpened():
                    grabbed, frame = self.stream.read()
                    if grabbed:
                        with self.lock:
                            self.grabbed, self.frame = grabbed, frame
            
            last_frame_time = current_time
            
    def read(self):
        with self.lock:
            return self.frame.copy() if self.grabbed else None
            
    def stop(self):
        print("Stopping camera stream...")
        self.stopped = True
        self.stream.release()

app = Flask(__name__)

# Basic Auth config
app.config['BASIC_AUTH_USERNAME'] = 'pi'
app.config['BASIC_AUTH_PASSWORD'] = 'pi'
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)

# Global camera instance
camera = None

def get_camera():
    global camera
    if camera is None or camera.stopped:
        camera = WebcamVideoStream()
        time.sleep(0.5)  # Short delay to ensure camera is initialized
    return camera

@app.route('/')
@basic_auth.required
def index():
    return '''
    <html>
    <head>
        <title>Low-Latency Camera Stream</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { color: green; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Live Low-Latency Camera Stream</h1>
            <img src="/video_feed" width="640" height="480">
            <p class="status">Optimized for minimal latency</p>
        </div>
    </body>
    </html>
    '''

def gen():
    cam = get_camera()
    jpeg_quality = 70  # Lower quality = faster encoding (adjust as needed)
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
    
    while True:
        frame = cam.read()
        if frame is None:
            time.sleep(0.01)  # Short sleep if frame not available
            continue
            
        # Apply a resize to reduce encoding time if needed
        # frame = cv2.resize(frame, (640, 480))
            
        # Encode with optimized parameters
        ret, jpeg = cv2.imencode('.jpg', frame, encode_params)
        if not ret:
            continue
            
        # Send frame immediately
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

@app.route('/video_feed')
@basic_auth.required
def video_feed():
    return Response(gen(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Run with minimal overhead
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True,
           use_reloader=False)  # Disable reloader for production
           
    # Cleanup
    if camera is not None:
        camera.stop()