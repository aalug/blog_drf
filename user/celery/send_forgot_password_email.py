"""
Function for sending forgot password emails.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template


def send_forgot_password_email(receiver, username, link):
    """Send 'reset password' email with link to reset it."""
    context = {
        'username': username,
        'link': link
    }
    mail_subject = 'Reset password to the blog app account.'

    html_message = get_template('emails/forgot_password_email.html').render(context)

    send_mail(
        subject=mail_subject,
        message=f'message',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[receiver],
        html_message=html_message
    )
