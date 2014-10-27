from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from pypushwoosh.client import PushwooshClient
from pypushwoosh.command import CreateTargetedMessageCommand
from pypushwoosh.filter import ApplicationFilter


def send_push_notification(receiver, message):
    command = CreateTargetedMessageCommand()
    command.auth = 'AUTH_TOKEN'
    command.devices_filter = ApplicationFilter('APP-CODE')
    command.content = "Hello world!"

    client = PushwooshClient()
    print client.invoke(command)


def send_email_notification(receiver, message, reply_to=None):
    headers = {}
    if reply_to:
        headers['Reply-To'] = reply_to

    text_content = strip_tags(message)
    msg = EmailMultiAlternatives(settings.EMAIL_NOTIFICATION_SUBJECT, text_content, settings.DEFAULT_FROM_EMAIL,
                                 [receiver.email], headers=headers)
    msg.attach_alternative(message, "text/html")
    msg.send()
