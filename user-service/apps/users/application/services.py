"""
apps/users/application/services.py
Application Service layer (use-cases that coordinate domain + infrastructure).
"""
from __future__ import annotations
import logging
import uuid

logger = logging.getLogger(__name__)


class UserApplicationService:
    """
    Thin application service that orchestrates domain + side-effects.
    No business logic here – delegated to domain model.
    """

    @staticmethod
    def send_verification_email(user) -> None:
        """
        Trigger email verification.
        In production: replaced with Celery task + email backend.
        """
        # Token generation (simple UUID – replace with signed token in prod)
        token = str(uuid.uuid4())
        # Cache token → user mapping (replace with Redis/DB)
        # cache.set(f"email_verify:{token}", str(user.id), timeout=86400)

        logger.info(
            "Verification email queued for user=%s email=%s token=%s",
            user.id, user.email, token,
        )
        # TODO: send_mail or Celery task
        # from apps.users.tasks import send_verification_email_task
        # send_verification_email_task.delay(user.id, token)

    @staticmethod
    def verify_email_token(token: str | None):
        """
        Validate a verification token and return the User.
        Returns None if token is invalid/expired.
        """
        if not token:
            return None
        # TODO: look up from cache / DB
        # user_id = cache.get(f"email_verify:{token}")
        # return User.objects.filter(id=user_id).first()
        return None
