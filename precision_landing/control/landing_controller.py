from enum import Enum
from utils.logger import setup_logger

logger = setup_logger("LandingController")

class LandingState(Enum):
    SEARCH = 1
    ALIGN = 2
    DESCEND = 3

class LandingController:
    def __init__(self, config):
        self.state = LandingState.SEARCH
        
        # Thresholds
        align_cfg = config.get('alignment', {})
        self.x_threshold = align_cfg.get('x_threshold', 0.1)
        self.y_threshold = align_cfg.get('y_threshold', 0.1)
        
        descend_cfg = config.get('descent', {})
        self.min_altitude = descend_cfg.get('min_altitude', 0.2)

    def process_pose(self, tvec):
        """
        State machine logic to determine landing state based on filtered pose.
        :param tvec: numpy array [X, Y, Z] translation vector
        :return: LandingState
        """
        if tvec is None:
            # Marker lost
            if self.state != LandingState.SEARCH:
                logger.warning("Marker lost! Reverting to SEARCH.")
            self.state = LandingState.SEARCH
            return self.state

        x, y, z = tvec[0], tvec[1], tvec[2]

        # Check if we are aligned
        aligned = (abs(x) < self.x_threshold) and (abs(y) < self.y_threshold)

        if self.state == LandingState.SEARCH:
            logger.info("Marker detected, moving to ALIGN state.")
            self.state = LandingState.ALIGN

        elif self.state == LandingState.ALIGN:
            if aligned:
                logger.info(f"Aligned! Moving to DESCEND. Altitude: {z:.2f}m")
                self.state = LandingState.DESCEND
            
        elif self.state == LandingState.DESCEND:
            if not aligned:
                logger.info("Lost alignment. Moving back to ALIGN.")
                self.state = LandingState.ALIGN
            elif z <= self.min_altitude:
                logger.info(f"Reached minimum altitude ({z:.2f}m). Ready to land!")
                # Normally we might issue a final land command here
            
        return self.state
