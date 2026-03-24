# Precision Landing System

A production-grade, modular Python repository for a drone precision landing system using ArUco/AprilTag detection, designed specifically for the Raspberry Pi 5.

This system achieves real-time (20-30 FPS) performance using multithreading to separate camera capture, vision processing, and MAVLink communication workloads.

## Project Structure

```text
precision_landing/
├── vision/
│   ├── camera.py             # Threaded camera capture
│   ├── aruco_detector.py     # OpenCV ArUco detector
│   ├── apriltag_detector.py  # pupil_apriltags detector (optional fallback)
│   └── pose_estimator.py     # solvePnP pose estimation
├── control/
│   ├── landing_controller.py # State machine for alignment and descent
│   └── filters.py            # Kalman filter for coordinate smoothing
├── mavlink/
│   ├── connection.py         # Serial connection handler
│   └── sender.py             # Threaded MAVLink LANDING_TARGET sender
├── core/
│   ├── pipeline.py           # Main orchestration loop
│   └── state_manager.py      # System health and status tracker
├── config/
│   ├── camera.yaml           # Camera intrinsic and resolution config
│   └── landing.yaml          # Drone alignment and descent thresholds
├── scripts/
│   ├── run.py                # Main entry point
│   └── calibrate_camera.py   # Checkerboard camera calibration script
├── utils/
│   └── logger.py             # Thread-safe rotating logger
└── requirements.txt
```

## Setup Instructions (Raspberry Pi 5)

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Python and System Dependencies
```bash
sudo apt install -y python3-pip python3-opencv python3-dev libatlas-base-dev
```

### 3. Install PIP Packages
```bash
pip3 install numpy pymavlink opencv-contrib-python pyyaml
```

*(Optional) For AprilTag support:*
```bash
pip3 install pupil-apriltags
```

*(Optional) For RealSense camera support:*
```bash
sudo apt install -y librealsense2-dev librealsense2-utils
```

### 4. Enable Camera Interface
If using a Raspberry Pi camera interface:
```bash
sudo raspi-config
# Navigate to Interfacing Options -> Camera -> Enable
# Reboot the Pi
```

## Running the System

Navigate to the project and run the entry script:
```bash
cd precision_landing
pip3 install -r requirements.txt
python3 scripts/run.py
```

## Debugging and Troubleshooting Commands

### Check Connect Hardware
```bash
# Check camera is connected
ls /dev/video*

# Check Cube Orange connection
ls /dev/ttyACM*
```

### Fix Serial Permissions
```bash
sudo usermod -a -G dialout $USER
# Must reboot after this to take effect
sudo reboot
```

### Test MAVLink manually
```bash
screen /dev/ttyACM0 115200
```
*(Exit screen using `Ctrl+a`, then `k`)*

## Performance Optimizations
- **Multithreading**: Separates IO-bound routines (Camera/Serial) from CPU-bound tracking processing.
- **Grayscale Processing**: Cuts down visual processing workload immediately after frame retrieval.
- **Thread Queues**: Ensures the most recent data is used without causing blocking build-ups.
- **640x480 Resolution**: Strikes a perfect balance between detection range and tracking latency.
