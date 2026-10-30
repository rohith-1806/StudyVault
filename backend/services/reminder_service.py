import os
import logging
from typing import Dict, Any

logger = logging.getLogger('studyvault.reminder')
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s')

class ReminderService:
    def __init__(self, db_service, email_service, reminder_window_seconds: int = 10 * 3600):
        self.db_service = db_service
        self.email_service = email_service
        self.reminder_window_seconds = reminder_window_seconds

    def check_and_send_reminders(self) -> Dict[str, Any]:
        """
        Polls database for users whose download access expires in <= reminder_window_seconds
        (default: 10 hours), and who have not received a reminder for their current access period.
        Atomically claims each user to prevent concurrent duplicate sends across workers.
        """
        stats = {
            "eligible_found": 0,
            "reminders_sent": 0,
            "already_claimed": 0,
            "errors": 0
        }

        try:
            eligible_users = self.db_service.get_eligible_reminder_users(
                threshold_seconds=self.reminder_window_seconds
            )
        except Exception as e:
            logger.error("Failed to query eligible reminder users from database: %s", str(e))
            stats["errors"] += 1
            return stats

        stats["eligible_found"] = len(eligible_users)
        if not eligible_users:
            return stats

        logger.info("Found %d user(s) approaching 10-hour access expiration.", len(eligible_users))

        for user in eligible_users:
            user_id = user['id']
            expires_at = user.get('download_access_expires_at')
            remaining_seconds = user.get('remaining_seconds', 10 * 3600)

            # Atomic concurrency-safe reservation
            # If two workers run simultaneously, only one will successfully claim
            claimed = self.db_service.claim_reminder_for_user(user_id=user_id, expires_at=expires_at)
            if not claimed:
                logger.debug("User %s reminder already claimed by another worker.", user_id)
                stats["already_claimed"] += 1
                continue

            # Dispatch reminder email
            try:
                res = self.email_service.send_access_reminder_email(
                    user=user,
                    remaining_seconds=remaining_seconds
                )
                if res.get('success'):
                    stats["reminders_sent"] += 1
                    logger.info("Successfully processed 10-hour access reminder for user: %s", user_id)
                else:
                    logger.warning("Email delivery reported non-success for user %s: %s", user_id, res.get('error'))
                    stats["errors"] += 1
            except Exception as ex:
                logger.error("Exception while sending reminder to user %s: %s", user_id, str(ex))
                stats["errors"] += 1

        return stats
