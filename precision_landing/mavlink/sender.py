import threading
import time
from queue import Queue
from utils.logger import setup_logger
from control.landing_controller import LandingState

logger = setup_logger("MAVLinkSender")

class MAVLinkSender:
    def __init__(self, mav_connection):
        self.mav_connection = mav_connection
        self.command_queue = Queue(maxsize=10)
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._send_loop, name="MAVLinkSenderWorker")
        self.thread.daemon = True
        self.thread.start()
        logger.info("MAVLink Sender thread started.")

    def send_target_pose(self, tvec, state):
        """
        Enqueues a target pose and state to be sent to the drone.
        """
        if self.command_queue.full():
            # Drop older commands if saturated
            try:
                self.command_queue.get_nowait()
            except:
                pass
        self.command_queue.put((tvec, state))

    def _send_loop(self):
        conn = self.mav_connection.get_connection()
        while self.running:
            try:
                # Wait for data or timeout
                data = self.command_queue.get(timeout=0.1)
                tvec, state = data
            except:
                data = None
            
            if data is not None and tvec is not None:
                x, y, z = tvec[0], tvec[1], tvec[2]
                
                # Send LANDING_TARGET message
                # Fields: time_boot_ms, target_num, frame, angle_x, angle_y, distance, size_x, size_y, x, y, z, q, type, position_valid
                
                # We'll use MAV_FRAME_BODY_NED (8) or MAV_FRAME_LOCAL_NED (1)
                # Using MAVLink2 required for extensions like position
                try:
                    conn.mav.landing_target_send(
                        0,                  # time_boot_ms (not used)
                        0,                  # target num
                        8,                  # frame (MAV_FRAME_BODY_NED)
                        0.0,                # angle_x (radians)
                        0.0,                # angle_y (radians)
                        float(z),           # distance to target
                        0.0, 0.0,           # size x, size y
                        float(x),           # x
                        float(y),           # y
                        float(z),           # z
                        (1.0, 0.0, 0.0, 0.0), # q
                        2,                  # type 2 = Vision
                        1                   # position_valid flag
                    )
                except Exception as e:
                    logger.error(f"Failed to send LANDING_TARGET: {e}")
                    # Trigger reconnect logic in main logic if repeated failures
            
            # Simple heartbeat or keep-alive can be handled here if needed
            elif state == LandingState.SEARCH:
                # Nothing to track
                pass
            
            time.sleep(0.01)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("MAVLink Sender thread stopped.")
