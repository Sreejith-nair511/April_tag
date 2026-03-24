from utils.logger import setup_logger

logger = setup_logger("AprilTagDetector")

class AprilTagDetector:
    def __init__(self, family='tag36h11'):
        try:
            from pupil_apriltags import Detector
            self.detector = Detector(families=family)
            self.available = True
        except ImportError:
            logger.warning("pupil-apriltags is not installed. AprilTag detection unavailable.")
            self.available = False

    def detect(self, gray_frame, camera_matrix=None):
        """
        Detects AprilTags in a grayscale frame.
        Returns a list of tags. Returns empty list if unavailable.
        """
        if not self.available:
            return []
            
        # pupil_apriltags can optionally compute pose if intrinsics are provided
        if camera_matrix is not None:
            fx = camera_matrix[0, 0]
            fy = camera_matrix[1, 1]
            cx = camera_matrix[0, 2]
            cy = camera_matrix[1, 2]
            camera_params = (fx, fy, cx, cy)
            # tag_size should ideally be passed in if estimate_tag_pose=True
            return self.detector.detect(gray_frame)
        else:
            return self.detector.detect(gray_frame)
