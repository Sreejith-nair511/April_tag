import cv2
import threading
import time
from queue import Queue
from utils.logger import setup_logger

logger = setup_logger("CameraThread")

class CameraStream:
    def __init__(self, device_id=0, width=640, height=480, fps=30):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.running = False
        self.frame_queue = Queue(maxsize=2)  # Keep it small to ensure fresh frames
        self.thread = None

    def start(self):
        """Starts the camera capture thread."""
        logger.info(f"Connecting to camera {self.device_id}...")
        self.cap = cv2.VideoCapture(self.device_id)
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.device_id}")
            raise RuntimeError(f"Camera {self.device_id} not available")

        # Set resolutions
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, name="CameraWorker")
        self.thread.daemon = True
        self.thread.start()
        logger.info("Camera capture started.")

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to grab frame. Attempting recovery...")
                time.sleep(1)
                self._reconnect()
                continue
            
            # Convert to grayscale for performance optimization
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Keep queue fresh by dropping old frames if full
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            self.frame_queue.put(gray_frame)
            
            # Small sleep to yield CPU
            time.sleep(0.005)

    def _reconnect(self):
        """Attempts to reconnect to the camera."""
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.device_id)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            logger.info("Camera reconnected successfully.")

    def get_frame(self):
        """Retrieves the latest frame from the queue."""
        if not self.frame_queue.empty():
            return self.frame_queue.get()
        return None

    def stop(self):
        """Stops the camera stream."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
        logger.info("Camera capture stopped.")
