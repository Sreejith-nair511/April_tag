import cv2
import numpy as np

class ArUcoDetector:
    def __init__(self, dictionary_name=cv2.aruco.DICT_4X4_50):
        try:
            # For newer OpenCV versions (4.7+)
            self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_name)
            self.parameters = cv2.aruco.DetectorParameters()
            self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)
            self._use_legacy = False
        except AttributeError:
            # Fallback for OpenCV versions < 4.7
            self._use_legacy = True
            self.dictionary = cv2.aruco.Dictionary_get(dictionary_name)
            self.parameters = cv2.aruco.DetectorParameters_create()

    def detect(self, gray_frame):
        """
        Detects ArUco markers in a grayscale frame.
        Returns corners and ids.
        """
        if self._use_legacy:
            corners, ids, rejected = cv2.aruco.detectMarkers(
                gray_frame, self.dictionary, parameters=self.parameters
            )
        else:
            corners, ids, rejected = self.detector.detectMarkers(gray_frame)

        return corners, ids

    def draw_markers(self, color_frame, corners, ids):
        if ids is not None and len(ids) > 0:
            cv2.aruco.drawDetectedMarkers(color_frame, corners, ids)
        return color_frame
