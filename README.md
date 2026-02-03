# 🕷️ Hexapod Robot (18-DOF)

> **Autonomous Hexapod Robot with Computer Vision, Voice Control, and Real-time Video Feedback.**

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_Control-green?style=for-the-badge&logo=flask)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-red?style=for-the-badge&logo=opencv)
![Arduino](https://img.shields.io/badge/Arduino-Firmware-teal?style=for-the-badge&logo=arduino)

## 📖 Overview

This project is a fully functional **18-Degree-of-Freedom (DOF) Hexapod Robot**. It features a robust control system split between a high-level **Raspberry Pi** controller (running a Flask web server) and a low-level **Arduino** servo controller.

Users can control the robot via a responsive **Web Dashboard** that provides:
-   **Live Video Feed**: Low-latency streaming from the robot's onboard camera.
-   **Manual Controls**: Directional buttons (Forward, Backward, Left, Right, Stop).
-   **Voice Commands**: Integrated Web Speech API for hands-free control (e.g., "move forward for 5 seconds").
-   **Chat Interface**: Text-based command execution.

> [!IMPORTANT]
> **Calibration Note**: The Arduino firmware is calibrated for the specific dimensions of this Hexapod build. Minute adjustments to the movement logic or servo angles may be required if your robot has different limb lengths.

## 🚀 Features

*   **18-Servo Inverse Kinematics**: Complex gait handling for smooth movement.
*   **Real-Time Video Stream**: Optimized MJPEG streaming using OpenCV with multi-threading.
*   **Dual Control Modes**: Toggle between manual UI clicks or voice/text commands.
*   **Remote Connectivity**: Accessible from any device (globally) using **ngrok** tunneling.
*   **Secure Access**: Basic authentication enabled for the web interface.
*   **Hardware Accelerated**: Efficient serial communication between Pi and Arduino.

## 🛠️ Tech Stack

### Software
*   **Backend**: Python (Flask)
*   **Computer Vision**: OpenCV (`cv2`)
*   **Frontend**: HTML5, CSS3, JavaScript (Fetch API, Web Speech API)
*   **Firmware**: C++ (Arduino)

### Hardware Requirements
*   **Microcontroller**: Arduino Mega (or compatible board with sufficient PWM pins)
*   **SBC**: Raspberry Pi (3B/4/Zero W recommended)
*   **Actuators**: 18x Servos (MG996R / SG90 depending on scale)
*   **Camera**: USB Webcam or Pi Camera
*   **Power**: High-current 5V Power Supply (for servos)

## 🔌 Pin Configuration

The 18 servos are mapped to the following digital pins on the Arduino:

| Leg Group | Joint 1 (Coxa) | Joint 2 (Femur) | Joint 3 (Tibia) |
| :--- | :---: | :---: | :---: |
| **Left 1** | 2 | 3 | 4 |
| **Left 2** | 5 | 6 | 7 |
| **Left 3** | 8 | 9 | 10 |
| **Right 1** | 11 | 12 | 13 |
| **Right 2** | 14 | 15 | 16 |
| **Right 3** | 17 | 20 | 21 |

*> Note: Ensure your external power supply shares a common ground (GND) with the Arduino.*

## 📥 Installation

### 1. Arduino Firmware
1.  Open `Hexapod_final/Hexapod_final.ino` in the Arduino IDE.
2.  Install the standard `Servo` library if not present.
3.  Select your board and port, then upload the sketch.

### 2. Python Controller (Raspberry Pi)
Clone this repository to your Raspberry Pi:

```bash
git clone https://github.com/AtharvSc/Hexapod.git
cd Hexapod/final_flask
```

Install dependencies:
```bash
pip install flask opencv-python pyserial flask-basicauth
```

## 🎮 Usage

1.  **Connect Hardware**: Plug the Arduino into the Raspberry Pi via USB.
2.  **Start the Server**:
    ```bash
    python final.py
    ```
    *The server initializes the serial connection (`/dev/ttyUSB0`) and camera.*

3.  **Access the Dashboard**:
    Open your browser and navigate to: `http://<RASPBERRY_PI_IP>:5000`

    *   **Username**: `pi`
    *   **Password**: `pi` *(Default)*

4.  **Control**:
    *   Use the arrow buttons to move.
    *   Click "🎙️ Speak" to give voice commands like *"Turn Left"* or *"Move Forward"*.

### 5. Remote Access (Ngrok)
To allow control from any device outside the local network:
1.  Install **ngrok** and authenticate with your API key:
    ```bash
    ngrok config add-authtoken <YOUR_TOKEN>
    ```
2.  Start the tunnel on port 5000:
    ```bash
    ngrok http 5000
    ```
3.  Use the generated public URL to access the dashboard.

## 📂 Project Structure

```
├── Hexapod_final
│   └── Hexapod_final.ino    # Arduino Firmware for Servo Control
├── final_flask
│   ├── final.py             # Main Flask Application
│   ├── OpencvF.py           # Computer Vision Utilities
│   └── liveS.py             # Live Streaming Tests
└── README.md                # Project Documentation
```

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or new gait algorithms.

---
*Created by [Shreyas Dambalkar](https://github.com/ShreyasDambalkar)*
