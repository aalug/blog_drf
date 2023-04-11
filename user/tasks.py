"""
Celery tasks for the user app.
"""
from celery import shared_task
from celery.utils.log import get_task_logger

from .celery.send_forgot_password_email import send_forgot_password_email


@shared_task
def send_forgot_password_email_task(receiver, username, link):
    """Celery task to send a forgot password email."""
    logger = get_task_logger(__name__)
    try:
        send_forgot_password_email(receiver, username, link)
    except Exception as e:
        logger.info(f'{e} error occurred while sending email to {receiver}')
