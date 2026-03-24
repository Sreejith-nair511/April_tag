import sys
import os
import time

# Ensure the project root is on the path for package resolution
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import cv2  # type: ignore[import]
import yaml  # type: ignore[import]
import numpy as np  # type: ignore[import]

from utils.logger import setup_logger  # pyre-ignore[21]
from vision.camera import CameraStream  # pyre-ignore[21]
from vision.aruco_detector import ArUcoDetector  # pyre-ignore[21]
from vision.apriltag_detector import AprilTagDetector  # pyre-ignore[21]
from vision.pose_estimator import PoseEstimator  # pyre-ignore[21]
from control.filters import PoseFilter  # pyre-ignore[21]
from control.landing_controller import LandingController  # pyre-ignore[21]
from mavlink.connection import MAVLinkConnection  # pyre-ignore[21]
from mavlink.sender import MAVLinkSender  # pyre-ignore[21]
from core.state_manager import StateManager  # pyre-ignore[21]
from web.server import WebMonitorServer, update_status as web_update  # pyre-ignore[21]

logger = setup_logger("Pipeline")

class PrecisionLandingPipeline:
    def __init__(self):
        logger.info("Initializing Precision Landing Pipeline...")
        self.running = False
        self.state_manager = StateManager()

        # Load configurations
        with open("config/camera.yaml", "r") as f:
            self.cam_config = yaml.safe_load(f)
        with open("config/landing.yaml", "r") as f:
            self.land_config = yaml.safe_load(f)

        # Vision Setup
        self.camera = CameraStream(
            device_id=self.cam_config['device_id'],
            width=self.cam_config['resolution']['width'],
            height=self.cam_config['resolution']['height'],
            fps=self.cam_config['fps']
        )
        
        marker_type = self.land_config['marker']['type']
        if marker_type == 'aruco':
            dict_name = getattr(cv2.aruco, self.land_config['marker']['dictionary'], cv2.aruco.DICT_4X4_50)
            self.detector = ArUcoDetector(dictionary_name=dict_name)
        elif marker_type == 'apriltag':
            self.detector = AprilTagDetector()
        else:
            raise ValueError(f"Unknown marker type: {marker_type}")

        # Pose Estimation Setup
        calib = self.cam_config.get('calibration', {})
        self.pose_estimator = PoseEstimator(
            camera_matrix=calib.get('camera_matrix'),
            dist_coeffs=calib.get('dist_coeffs'),
            marker_size=self.land_config['marker']['real_size']
        )

        # Control Setup
        self.pose_filter = PoseFilter()
        self.controller = LandingController(self.land_config)

        # MAVLink Setup
        self.mav_conn = MAVLinkConnection(
            device=self.land_config['mavlink']['device'],
            baudrate=self.land_config['mavlink']['baudrate']
        )
        self.mav_sender = MAVLinkSender(self.mav_conn)

        # Web dashboard
        self.web_server = WebMonitorServer(port=8080)

    def start(self):
        self.running = True
        
        # Start web dashboard first so user can monitor startup
        self.web_server.start()

        # Start Threads
        self.mav_conn.connect()
        self.state_manager.update_mavlink_status(self.mav_conn.connected)
        self.mav_sender.start()
        
        self.camera.start()
        self.state_manager.update_camera_status(self.camera.running)

        logger.info("Pipeline fully started. Entering main loop.")
        self._run_main_loop()

    def _run_main_loop(self):
        fps_timer = time.time()
        frames_processed = 0
        
        while self.running:
            try:
                frame = self.camera.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                # Detect
                if isinstance(self.detector, ArUcoDetector):
                    corners, ids = self.detector.detect(frame)
                    detected = (ids is not None) and (len(ids) > 0)  # type: ignore[arg-type]
                    target_corners = corners[0] if detected else None
                else:
                    # AprilTags
                    tags = self.detector.detect(frame)
                    detected = len(tags) > 0
                    target_corners = tags[0].corners if detected else None
                
                self.state_manager.update_tracking_status(detected)

                tvec_filtered = None
                
                if detected:
                    # Pose Estimation
                    rvec, tvec = self.pose_estimator.estimate_pose_single_marker(target_corners)
                    
                    if tvec is not None:
                        # Filter pose
                        tvec_filtered = self.pose_filter.filter(tvec)

                # Control Logic
                landing_state = self.controller.process_pose(tvec_filtered)
                
                # Send MAVLink commands
                if tvec_filtered is not None:
                    self.mav_sender.send_target_pose(tvec_filtered, landing_state)
                
                # Performance metrics
                frames_processed += 1
                elapsed = time.time() - fps_timer
                if elapsed > 2.0:
                    fps = frames_processed / elapsed
                    logger.info(f"Processing FPS: {fps:.1f} | State: {landing_state.name}")
                    self.state_manager.print_status()
                    frames_processed = 0
                    fps_timer = time.time()

                    # Push live data to web dashboard
                    mx = tvec_filtered[0] if tvec_filtered is not None else 0.0
                    my = tvec_filtered[1] if tvec_filtered is not None else 0.0
                    mz = tvec_filtered[2] if tvec_filtered is not None else 0.0
                    web_update({
                        "fps": float(int(fps * 10)) / 10.0,
                        "landing_state": landing_state.name,
                        "camera_ok": self.state_manager.state.camera_ok,
                        "mavlink_ok": self.state_manager.state.mavlink_ok,
                        "tracking_active": detected,
                        "marker_x": float(mx),
                        "marker_y": float(my),
                        "marker_z": float(mz),
                    })

                time.sleep(0.005) # Yield CPU
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested.")
                self.stop()
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)

    def stop(self):
        logger.info("Stopping pipeline...")
        self.running = False
        self.camera.stop()
        self.mav_sender.stop()
        self.mav_conn.disconnect()
        self.web_server.stop()
        logger.info("Pipeline stopped clean.")
