import cv2
import time
import numpy as np
from threading import Thread, Lock
from flask import Flask, Response, request, jsonify
from flask_basicauth import BasicAuth

# Optimized Webcam class with face detection
class WebcamVideoStream:
    def __init__(self, src=0, detect_faces=True):
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
        
        # Face detection settings
        self.detect_faces = detect_faces
        self.face_cascade = None
        self.face_detection_frame = None
        self.face_detection_active = False
        self.face_count = 0
        self.last_detection_time = 0
        self.detection_interval = 0.1  # Run detection every 100ms
        
        if self.detect_faces:
            # Initialize face detection (load once, not in the loop)
            self._initialize_face_detection()
        
        # Start the thread to read frames
        self.processing_thread = Thread(target=self.update, daemon=True)
        self.processing_thread.start()
    
    def _initialize_face_detection(self):
        # Load the face detection cascade classifier
        try:
            # First try to load the more accurate but slower model
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if self.face_cascade.empty():
                # If that fails, try the faster but less accurate model
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
                if self.face_cascade.empty():
                    print("Warning: Could not load face cascade classifier")
                    self.detect_faces = False
                else:
                    print("Loaded alternate face detection model")
            else:
                print("Face detection initialized")
        except Exception as e:
            print(f"Error initializing face detection: {e}")
            self.detect_faces = False
    
    def toggle_face_detection(self, active):
        """Enable or disable face detection"""
        with self.lock:
            self.face_detection_active = active
        return self.face_detection_active
        
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
                            
                            # Check if face detection is enabled and it's time to run detection
                            if (self.detect_faces and self.face_detection_active and 
                                current_time - self.last_detection_time >= self.detection_interval):
                                self._detect_faces(frame)
                                self.last_detection_time = current_time
            
            last_frame_time = current_time
    
    def _detect_faces(self, frame):
        """Detect faces in the frame"""
        if self.face_cascade is None:
            return
            
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Optimize detection by using a smaller scale factor
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Create a copy of the frame to draw on
            detection_frame = frame.copy()
            
            # Draw rectangles around faces
            self.face_count = len(faces)
            for (x, y, w, h) in faces:
                cv2.rectangle(detection_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
            # Update the face detection frame
            self.face_detection_frame = detection_frame
        except Exception as e:
            print(f"Error in face detection: {e}")
            
    def read(self):
        """Return the current frame with or without face detection"""
        with self.lock:
            if self.face_detection_active and self.face_detection_frame is not None:
                return self.face_detection_frame.copy()
            elif self.grabbed:
                return self.frame.copy()
            else:
                return None
                
    def get_face_count(self):
        """Return the number of faces detected in the last frame"""
        return self.face_count
            
    def stop(self):
        print("Stopping camera stream...")
        self.stopped = True
        if self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
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
        camera = WebcamVideoStream(detect_faces=True)
        camera.toggle_face_detection(True)  # Enable face detection by default
        time.sleep(0.5)  # Short delay to ensure camera is initialized
    return camera

@app.route('/')
@basic_auth.required
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Face Detection Camera Stream</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                margin: 20px;
                background-color: #f5f5f5;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .video-container {
                position: relative;
                margin: 20px auto;
                border-radius: 5px;
                overflow: hidden;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .controls {
                margin: 15px 0;
                padding: 10px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
            .btn {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
                transition: background-color 0.3s;
            }
            .btn:hover {
                background-color: #45a049;
            }
            .btn-off {
                background-color: #f44336;
            }
            .btn-off:hover {
                background-color: #d32f2f;
            }
            .status {
                margin-top: 10px;
                padding: 10px;
                background-color: #e8f5e9;
                border-radius: 5px;
                font-weight: bold;
            }
            .face-count {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
            }
            #faceDetectionStatus {
                display: inline-block;
                width: 15px;
                height: 15px;
                background-color: #4CAF50;
                border-radius: 50%;
                margin-right: 5px;
            }
        </style>
        <script>
            let faceDetectionEnabled = true;
            
            function toggleFaceDetection() {
                fetch('/toggle_face_detection', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        'enabled': !faceDetectionEnabled
                    })
                })
                .then(response => response.json())
                .then(data => {
                    faceDetectionEnabled = data.enabled;
                    updateUI();
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }
            
            function updateUI() {
                const btn = document.getElementById('toggleBtn');
                const status = document.getElementById('faceDetectionStatus');
                
                if (faceDetectionEnabled) {
                    btn.textContent = 'Disable Face Detection';
                    btn.className = 'btn btn-off';
                    status.style.backgroundColor = '#4CAF50';
                } else {
                    btn.textContent = 'Enable Face Detection';
                    btn.className = 'btn';
                    status.style.backgroundColor = '#f44336';
                }
            }
            
            function updateFaceCount() {
                fetch('/face_count')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('faceCount').textContent = data.count;
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }
            
            // Update face count every second
            window.onload = function() {
                updateUI();
                setInterval(updateFaceCount, 1000);
            };
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Face Detection Camera Stream</h1>
            
            <div class="video-container">
                <img src="/video_feed" width="640" height="480">
            </div>
            
            <div class="controls">
                <div>
                    <span id="faceDetectionStatus"></span>
                    <span>Face Detection: </span>
                    <button id="toggleBtn" class="btn btn-off" onclick="toggleFaceDetection()">
                        Disable Face Detection
                    </button>
                </div>
            </div>
            
            <div class="status">
                Faces Detected: <span id="faceCount" class="face-count">0</span>
            </div>
            
            <p>
                <small>Optimized for low-latency streaming with real-time face detection</small>
            </p>
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

@app.route('/toggle_face_detection', methods=['POST'])
@basic_auth.required
def toggle_face_detection():
    data = request.json
    enabled = data.get('enabled', False)
    
    cam = get_camera()
    result = cam.toggle_face_detection(enabled)
    
    return jsonify({'enabled': result})

@app.route('/face_count')
@basic_auth.required
def face_count():
    cam = get_camera()
    count = cam.get_face_count()
    return jsonify({'count': count})

if __name__ == '__main__':
    try:
        # Run with minimal overhead
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True,
               use_reloader=False)  # Disable reloader for production
    finally:
        # Cleanup
        if camera is not None:
            camera.stop()