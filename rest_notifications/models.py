from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template.loader import render_to_string
from celery.task import task
from model_utils import Choices
from manticore_django.manticore_django.models import CoreModel

__author__ = 'rudy'


class Notification(CoreModel):
    TYPES = Choices(*settings.NOTIFICATION_TYPES)
    PUSH = "push"
    EMAIL = "email"

    notification_type = models.PositiveSmallIntegerField(choices=TYPES)
    # template_override = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="notifications_received", null=True)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="notifications_sent", null=True, blank=True)

    # The object that the notification is about, not the social model related to it
    # E.g., if you Like a Post, the content_object for the notification is the Post, not the Like
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey()

    def message(self, location):
        """
        Takes our configured notifications and creates a message
        replacing the appropriate variables from the content object
        """

        # TODO: Right now assumes the content_object has identifier defined
        data = {
            'identifier': self.content_object.identifier(),
            'reporter': self.reporter.identifier()
        }

        if hasattr(self.content_object, 'extra_notification_params'):
            data.update(self.content_object.extra_notification_params())

        configured_template_name = unicode(Notification.TYPES._triples[self.notification_type][1]) + '.html'
        # template_name = self.template_override if self.template_override else configured_template_name
        return render_to_string("notifications/{}/{}".format(location, configured_template_name), data)

    def email_message(self):
        return self.message(Notification.EMAIL)

    def push_message(self):
        message = self.message(Notification.PUSH)
        if self.reporter:
            return "{0} {1}".format(self.reporter, message)
        else:
            return "{0}".format(message)

    @property
    def name(self):
        return u"{0}".format(Notification.TYPES._triples[self.notification_type][1])

    class Meta:
        ordering = ['-created']


@task
def create_notification(receiver, reporter, content_object, notification_type, template_override=None, reply_to=None):
    # If the receiver of this notification is the same as the reporter or
    # if the user has blocked this type, then don't create
    if receiver == reporter:
        return

    notification = Notification.objects.create(user=receiver,
                                               reporter=reporter,
                                               content_object=content_object,
                                               notification_type=notification_type)
    notification.save()

    notification_setting = NotificationSetting.objects.get(notification_type=notification_type, user=receiver)
    if notification_setting.allow_push:
        from .utils import send_push_notification
        send_push_notification(receiver, notification.push_message())

    if notification_setting.allow_email:
        from .utils import send_email_notification
        send_email_notification(receiver, notification.email_message(), reply_to=reply_to)


class NotificationSetting(CoreModel):
    notification_type = models.PositiveSmallIntegerField(choices=Notification.TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notification_settings')
    allow_push = models.BooleanField(default=True)
    allow_email = models.BooleanField(default=True)

    class Meta:
        unique_together = ('notification_type', 'user')

    def name(self):
        return u"{0}".format(Notification.TYPES._triples[self.notification_type][2])


def create_notification_settings(sender, **kwargs):
    sender_name = "{0}.{1}".format(sender._meta.app_label, sender._meta.object_name)
    if sender_name.lower() != settings.AUTH_USER_MODEL.lower():
        return

    if kwargs['created']:
        user = kwargs['instance']
        if not user.notification_settings.exists():
            user_settings = [NotificationSetting(user=user, notification_type=pk) for pk, name in Notification.TYPES]
            NotificationSetting.objects.bulk_create(user_settings)


class PushwooshToken(CoreModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="pushwoosh_tokens")
    token = models.CharField(max_length=120)
