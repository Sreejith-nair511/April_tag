from utils.logger import setup_logger

logger = setup_logger("StateManager")

class SystemState:
    def __init__(self):
        self.camera_ok = False
        self.mavlink_ok = False
        self.tracking_active = False
        
    def summary(self):
        return (
            f"CAM: {'OK' if self.camera_ok else 'ERR'} | "
            f"MAV: {'OK' if self.mavlink_ok else 'ERR'} | "
            f"TRK: {'YES' if self.tracking_active else 'NO'}"
        )

class StateManager:
    def __init__(self):
        self.state = SystemState()

    def update_camera_status(self, is_ok):
        if self.state.camera_ok != is_ok:
            self.state.camera_ok = is_ok
            logger.info(f"Camera state changed: {is_ok}")

    def update_mavlink_status(self, is_ok):
        if self.state.mavlink_ok != is_ok:
            self.state.mavlink_ok = is_ok
            logger.info(f"MAVLink state changed: {is_ok}")

    def update_tracking_status(self, is_active):
        if self.state.tracking_active != is_active:
            self.state.tracking_active = is_active
            logger.info(f"Tracking state changed: {is_active}")

    def print_status(self):
        logger.info(f"System Status: {self.state.summary()}")
