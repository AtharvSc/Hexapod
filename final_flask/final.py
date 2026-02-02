from flask import Flask, request, jsonify, Response
import serial
import time
import cv2
from threading import Thread, Lock

app = Flask(__name__)

# Basic Auth config
app.config['BASIC_AUTH_USERNAME'] = 'pi'
app.config['BASIC_AUTH_PASSWORD'] = 'pi'

try:
    from flask_basicauth import BasicAuth
    basic_auth = BasicAuth(app)
    auth_enabled = True
    print("Basic authentication enabled")
except ImportError:
    auth_enabled = False
    print("flask_basicauth not installed, authentication disabled")

# Initialize serial communication
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(2)
    print("Serial connection established.")
except serial.SerialException as e:
    print(f"Error: Could not open serial port. {e}")
    ser = None  # Still allow the app to run for camera-only usage

# Predefined commands and their mappings
COMMANDS = {
    "move forward": "F",
    "move backward": "B",
    "turn left": "L",
    "turn right": "R",
    "stop": "S",
}

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

# Global camera instance
camera = None

def get_camera():
    global camera
    if camera is None or camera.stopped:
        camera = WebcamVideoStream()
        time.sleep(0.5)  # Short delay to ensure camera is initialized
    return camera

# Route to serve the HTML interface
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hexapod Robot Control</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #111;
                color: white;
                text-align: center;
                padding: 20px;
                margin: 0;
            }
            .section {
                margin-bottom: 30px;
            }
            .controls button {
                width: 80px;
                height: 80px;
                font-size: 1.5rem;
                margin: 10px;
                border-radius: 50%;
                border: none;
                background-color: #ff5722;
                color: white;
                cursor: pointer;
                transition: transform 0.1s, background-color 0.3s;
            }
            .controls button:active {
                transform: scale(0.95);
                background-color: #e64a19;
            }
            #response, #chatResponse {
                margin-top: 10px;
                color: #ffeb3b;
                min-height: 20px;
            }
            input, button {
                font-size: 1rem;
            }
            .video-container {
                margin: 20px auto;
                max-width: 640px;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 0 20px rgba(255, 87, 34, 0.3);
            }
            video, img {
                width: 100%;
                max-width: 640px;
                border-radius: 10px;
                display: block;
            }
            h1, h2 {
                color: #ff5722;
                text-shadow: 0 0 10px rgba(255, 87, 34, 0.5);
            }
            .input-row {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
                margin: 10px 0;
            }
            .input-row input {
                padding: 10px;
                border-radius: 20px;
                border: none;
                flex: 1;
                max-width: 400px;
                background: #333;
                color: white;
            }
            .input-row button {
                padding: 10px 20px;
                border-radius: 20px;
                border: none;
                background: #ff5722;
                color: white;
                cursor: pointer;
            }
            .voice-button {
                background: #2196f3 !important;
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            .status-online {
                background-color: #4CAF50;
            }
            .status-offline {
                background-color: #F44336;
            }
        </style>
        <script>
            // Check if the camera stream is available
            function checkCameraStatus() {
                const img = document.getElementById('videoFeed');
                img.onerror = function() {
                    document.getElementById('cameraStatus').className = 'status-indicator status-offline';
                    document.getElementById('cameraStatusText').innerText = 'Offline';
                };
                img.onload = function() {
                    document.getElementById('cameraStatus').className = 'status-indicator status-online';
                    document.getElementById('cameraStatusText').innerText = 'Online';
                };
            }

            // Send control command
            async function sendCommand(command) {
                try {
                    const response = await fetch('/send_command', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ command: command })
                    });
                    const result = await response.json();
                    document.getElementById('response').innerText = result.response;
                } catch (error) {
                    console.error("Error:", error);
                    document.getElementById('response').innerText = "Error: Could not send command";
                }
            }

            // Send text/voice command
            async function sendChatCommand() {
                const userMessage = document.getElementById('chatInput').value;
                if (!userMessage.trim()) return;
                
                document.getElementById('chatInput').value = '';
                document.getElementById('chatResponse').innerText = "Processing...";
                
                try {
                    const response = await fetch('/chat_command', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ message: userMessage })
                    });
                    const result = await response.json();
                    document.getElementById('chatResponse').innerText = result.response;
                } catch (error) {
                    console.error("Error:", error);
                    document.getElementById('chatResponse').innerText = "Error: Could not process command";
                }
            }

            // Handle Enter key in text input
            function handleKeyPress(event) {
                if (event.keyCode === 13) {
                    sendChatCommand();
                }
            }

            // Voice Recognition
            function startVoiceRecognition() {
                if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
                    document.getElementById('chatResponse').innerText = "Speech recognition not supported in this browser";
                    return;
                }
                
                const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = 'en-US';
                recognition.interimResults = false;
                recognition.maxAlternatives = 1;
                
                document.getElementById('chatResponse').innerText = "Listening...";
                recognition.start();

                recognition.onresult = function(event) {
                    const voiceCommand = event.results[0][0].transcript;
                    document.getElementById('chatInput').value = voiceCommand;
                    sendChatCommand();
                };

                recognition.onerror = function(event) {
                    console.error("Voice recognition error:", event.error);
                    document.getElementById('chatResponse').innerText = "Voice recognition error: " + event.error;
                };
            }

            // Initialize on page load
            window.onload = function() {
                checkCameraStatus();
                // Refresh status every 10 seconds
                setInterval(checkCameraStatus, 10000);
            }
        </script>
    </head>
    <body>
        <h1>Hexapod Robot Control</h1>
        
        <div class="section">
            <h2>Live Video Feed</h2>
            <div class="video-container">
                <img id="videoFeed" src="/video_feed" alt="Live Camera Feed">
            </div>
            <p>
                <span id="cameraStatus" class="status-indicator"></span>
                <span id="cameraStatusText">Checking...</span>
            </p>
        </div>

        <div class="section">
            <h2>Movement Controls</h2>
            <div class="controls">
                <button onclick="sendCommand('F')" title="Forward">↑</button>
                <button onclick="sendCommand('L')" title="Left">←</button>
                <button onclick="sendCommand('S')" title="Stop">⏹</button>
                <button onclick="sendCommand('R')" title="Right">→</button>
                <button onclick="sendCommand('B')" title="Backward">↓</button>
            </div>
            <p id="response"></p>
        </div>

        <div class="section">
            <h2>Voice & Text Commands</h2>
            <div class="input-row">
                <input type="text" id="chatInput" placeholder="e.g., move forward for 5 seconds" onkeypress="handleKeyPress(event)">
                <button onclick="sendChatCommand()">Send</button>
                <button onclick="startVoiceRecognition()" class="voice-button">🎙 Speak</button>
            </div>
            <p id="chatResponse"></p>
        </div>

        <div class="section">
            <h2>GPS Navigation</h2>
            <div class="input-row">
                <input type="text" placeholder="Latitude" id="latInput">
                <input type="text" placeholder="Longitude" id="lngInput">
                <button>Navigate</button>
            </div>
            <p><small>GPS navigation feature coming soon</small></p>
        </div>
    </body>
    </html>
    '''

# Route to handle basic control commands
@app.route('/send_command', methods=['POST'])
def send_command():
    if ser is None:
        return jsonify({"response": "Serial not connected"}), 500
        
    data = request.json.get('command', '').upper()
    if data in ['F', 'B', 'L', 'R', 'S']:
        ser.write(data.encode())
        time.sleep(0.1)
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            return jsonify({"response": response})
        return jsonify({"response": "Command sent."})
    return jsonify({"response": "Unknown command"}), 400

# Route to handle chat/voice commands
@app.route('/chat_command', methods=['POST'])
def chat_command():
    if ser is None:
        return jsonify({"response": "Serial not connected"}), 500
        
    user_message = request.json.get('message', '').lower()
    
    # Parse the message for command and duration
    parts = user_message.split()
    duration = 0
    for i, word in enumerate(parts):
        if word.isdigit() and (i + 1 < len(parts)) and parts[i + 1] in ["second", "seconds"]:
            duration = int(word)

    # Match command
    command_key = None
    for key in COMMANDS:
        if key in user_message:
            command_key = key
            break
            
    if not command_key and len(parts) > 1:
        command_key = " ".join([parts[0], parts[1]])
    elif not command_key and parts:
        command_key = parts[0]
        
    command = COMMANDS.get(command_key)

    if command:
        ser.write(command.encode())
        if duration > 0:
            time.sleep(duration)
            ser.write("S".encode())
            return jsonify({"response": f"Executed '{command_key}' for {duration} seconds."})
        return jsonify({"response": f"Executed command: {command_key}."})

    return jsonify({"response": "Command not recognized. Try 'move forward for 5 seconds'."})

# Video streaming generator function
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

# Route for video streaming
@app.route('/video_feed')
def video_feed():
    # Apply authentication if enabled
    if auth_enabled:
        auth = request.authorization
        if not auth or not basic_auth.check_credentials(auth.username, auth.password):
            return Response('Authentication required', 401,
                          {'WWW-Authenticate': 'Basic realm="Login Required"'})
    
    return Response(gen(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

# Cleanup function
def cleanup():
    global camera, ser
    if camera is not None:
        camera.stop()
    if ser is not None:
        ser.close()

# Run the Flask app
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
    finally:
        cleanup()