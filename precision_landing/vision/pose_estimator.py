import cv2
import numpy as np

class PoseEstimator:
    def __init__(self, camera_matrix, dist_coeffs, marker_size):
        """
        :param camera_matrix: 3x3 camera intrinsic matrix (numpy array)
        :param dist_coeffs: Distortion coefficients (numpy array)
        :param marker_size: Real-world size of the marker in meters
        """
        self.camera_matrix = np.array(camera_matrix, dtype=np.float32)
        self.dist_coeffs = np.array(dist_coeffs, dtype=np.float32)
        self.marker_size = marker_size

        # Define the exact 3D coordinates of the marker corners in its own frame
        half_size = self.marker_size / 2.0
        self.marker_points_3d = np.array([
            [-half_size,  half_size, 0],
            [ half_size,  half_size, 0],
            [ half_size, -half_size, 0],
            [-half_size, -half_size, 0]
        ], dtype=np.float32)

    def estimate_pose_single_marker(self, corners):
        """
        Estimates the pose of a single marker.
        :param corners: 4x2 array of corner points of the marker
        :return: rvec, tvec (rotation and translation vectors)
        """
        # Ensure corners are properly shaped (4, 2)
        corners = np.array(corners, dtype=np.float32).reshape(4, 2)
        
        success, rvec, tvec = cv2.solvePnP(
            self.marker_points_3d,
            corners,
            self.camera_matrix,
            self.dist_coeffs,
            flags=cv2.SOLVEPNP_IPPE_SQUARE
        )
        if success:
            return rvec, tvec
        return None, None
