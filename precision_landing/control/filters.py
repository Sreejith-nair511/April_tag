import numpy as np
import time

class SimpleKalmanFilter:
    """A basic 1D Kalman filter for smoothing coordinates."""
    def __init__(self, process_variance, estimated_measurement_variance):
        self.process_variance = process_variance
        self.estimated_measurement_variance = estimated_measurement_variance
        self.posteri_estimate = 0.0
        self.posteri_error_estimate = 1.0

    def update(self, measurement):
        priori_estimate = self.posteri_estimate
        priori_error_estimate = self.posteri_error_estimate + self.process_variance

        blending_factor = priori_error_estimate / (priori_error_estimate + self.estimated_measurement_variance)
        self.posteri_estimate = priori_estimate + blending_factor * (measurement - priori_estimate)
        self.posteri_error_estimate = (1 - blending_factor) * priori_error_estimate

        return self.posteri_estimate

class PoseFilter:
    """Filters X, Y, Z translation vectors using Kalman filter."""
    def __init__(self):
        # Tuning parameters: Q (process noise), R (measurement noise)
        self.kx = SimpleKalmanFilter(1e-4, 1e-2)
        self.ky = SimpleKalmanFilter(1e-4, 1e-2)
        self.kz = SimpleKalmanFilter(1e-4, 1e-2)
        self.last_update_time = 0

    def filter(self, tvec):
        """
        Applies filter to current tvec.
        If tvec is None, resets or ignores.
        """
        if tvec is None:
            return None
        
        # tvec is typically shape (3, 1) -> flattening to (3,)
        tvec = tvec.flatten()
        
        fx = self.kx.update(tvec[0])
        fy = self.ky.update(tvec[1])
        fz = self.kz.update(tvec[2])
        
        self.last_update_time = time.time()
        
        return np.array([fx, fy, fz])
