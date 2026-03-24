import sys
import os

# Add parent directory to path so we can import packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pipeline import PrecisionLandingPipeline
from utils.logger import setup_logger

logger = setup_logger("RunScript")

def main():
    logger.info("Starting Precision Landing System...")
    pipeline = PrecisionLandingPipeline()
    try:
        pipeline.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        pipeline.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        pipeline.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
