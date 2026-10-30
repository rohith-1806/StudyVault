import os
import sys
import time
import signal
import argparse
import logging
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.db_service import DBService
from services.email_service import EmailService
from services.reminder_service import ReminderService

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [ReminderWorker] %(message)s'
)
logger = logging.getLogger('ReminderWorker')

_running = True

def handle_shutdown(signum, frame):
    global _running
    logger.info("Graceful shutdown signal received. Stopping worker...")
    _running = False

def run_worker(interval_seconds: int = 60, run_once: bool = False):
    global _running

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logger.info("Initializing StudyVault Persistent Reminder Worker...")
    db_service = DBService()
    email_service = EmailService(
        api_key=Config.BREVO_API_KEY,
        sender_email=Config.BREVO_SENDER_EMAIL,
        sender_name=Config.BREVO_SENDER_NAME,
        frontend_url=Config.FRONTEND_URL,
        db_service=db_service
    )
    reminder_service = ReminderService(db_service=db_service, email_service=email_service)

    logger.info("Brevo Email Service configured: %s", "YES" if email_service.is_configured() else "NO (credentials not set or placeholder)")
    logger.info("Worker polling interval: %d seconds. Running in %s mode.", interval_seconds, "SINGLE-SHOT (--once)" if run_once else "CONTINUOUS POLLING")

    while _running:
        try:
            stats = reminder_service.check_and_send_reminders()
            if stats["eligible_found"] > 0:
                logger.info(
                    "Cycle complete: found=%d, sent=%d, already_claimed=%d, errors=%d",
                    stats["eligible_found"],
                    stats["reminders_sent"],
                    stats["already_claimed"],
                    stats["errors"]
                )
        except Exception as e:
            logger.error("Unexpected error in reminder cycle: %s", str(e), exc_info=True)

        if run_once or not _running:
            break

        # Sleep in small increments for fast shutdown response
        for _ in range(interval_seconds):
            if not _running:
                break
            time.sleep(1)

    logger.info("Reminder Worker stopped.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="StudyVault 10-Hour Expiration Reminder Worker")
    parser.add_argument(
        '--once', 
        action='store_true', 
        help="Run a single reminder check pass and exit immediately (suitable for cron jobs)."
    )
    parser.add_argument(
        '--interval', 
        type=int, 
        default=int(os.environ.get('REMINDER_CHECK_INTERVAL_SECONDS', 60)),
        help="Interval in seconds between database checks (default: 60s)."
    )
    args = parser.parse_args()

    run_worker(interval_seconds=args.interval, run_once=args.once)
