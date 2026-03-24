import time
from pymavlink import mavutil
from utils.logger import setup_logger

logger = setup_logger("MAVLinkConnection")

class MAVLinkConnection:
    def __init__(self, device="/dev/ttyACM0", baudrate=115200):
        self.device = device
        self.baudrate = baudrate
        self.connection = None
        self.connected = False

    def connect(self):
        """Connects to the MAVLink serial device."""
        while not self.connected:
            try:
                logger.info(f"Connecting to MAVLink on {self.device} at {self.baudrate} baud...")
                self.connection = mavutil.mavlink_connection(self.device, baud=self.baudrate)
                # Wait for heartbeat
                logger.info("Waiting for heartbeat...")
                self.connection.wait_heartbeat(timeout=5)
                
                logger.info(f"Connected! Heartbeat from system (system {self.connection.target_system} component {self.connection.target_component})")
                self.connected = True
            except Exception as e:
                logger.error(f"MAVLink Connection failed: {e}. Retrying in 2 seconds...")
                time.sleep(2)

    def get_connection(self):
        """Returns the active MAVLink connection."""
        if not self.connected:
            self.connect()
        return self.connection

    def disconnect(self):
        """Closes the MAVLink connection."""
        if self.connection:
            self.connection.close()
            self.connected = False
            logger.info("MAVLink connection closed.")
