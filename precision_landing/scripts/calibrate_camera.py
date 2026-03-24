import cv2
import numpy as np
import glob
import os
from utils.logger import setup_logger

logger = setup_logger("CameraCalibrator")

# Checkerboard dimensions (inner corner count)
CHECKERBOARD = (6, 9)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

def calibrate(image_dir='calibration_images', save_file='calibration.npz'):
    objpoints = []
    imgpoints = []

    objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[0, :, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

    images = glob.glob(os.path.join(image_dir, '*.jpg'))
    if not images:
        logger.error("No images found in directory. Capture checkerboard images first.")
        return

    gray = None
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ret, corners = cv2.findChessboardCorners(
            gray, CHECKERBOARD, 
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
        else:
            logger.warning(f"Checkerboard not found in {fname}")

    if gray is not None and len(objpoints) > 0:
        logger.info("Computing camera matrix...")
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        
        logger.info("Calibration successful!")
        logger.info(f"Camera Matrix:\n{mtx}")
        logger.info(f"Distortion Coefficients:\n{dist}")
        
        np.savez(save_file, camera_matrix=mtx, dist_coeffs=dist)
        logger.info(f"Saved to {save_file}")
        logger.info("Please update config/camera.yaml with these parameters.")
    else:
        logger.error("Calibration failed. Insufficient valid images.")

if __name__ == '__main__':
    os.makedirs('calibration_images', exist_ok=True)
    logger.info("Running calibration using images from 'calibration_images' folder.")
    calibrate()
