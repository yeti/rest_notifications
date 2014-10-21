from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.urlresolvers import reverse
from manticore_django.manticore_django.utils import get_class
from rest_core.rest_core.test import ManticomTestCase
from rest_notifications.rest_notifications.models import create_notification, Notification, NotificationSetting
from rest_notifications.rest_notifications.utils import send_email_notification
from rest_social.rest_social.models import Comment
from rest_social.rest_social.utils import get_social_model
from rest_user.rest_user.test.factories import UserFactory

__author__ = 'baylee'


User = get_user_model()
SocialModel = get_social_model()
SocialFactory = get_class(settings.SOCIAL_MODEL_FACTORY)


class NotificationsTestCase(ManticomTestCase):
    def setUp(self):
        super(NotificationsTestCase, self).setUp()
        self.social_obj = SocialFactory()
        self.receiver = UserFactory()
        self.reporter = UserFactory()

    def test_email_notification_sent(self):
        message = "<h1>You have a notification!</h1>"
        send_email_notification(self.receiver, message)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, settings.EMAIL_NOTIFICATION_SUBJECT)
        self.assertEqual(mail.outbox[0].body, "You have a notification!")
        self.assertEqual(mail.outbox[0].alternatives, [(message, "text/html")])

    def test_push_notification_sent(self):
        pass

    def test_create_notification(self):
        notification_count = Notification.objects.count()

        # If receiver is the same as the reporter, a notification is not created
        create_notification(self.receiver, self.receiver, self.social_obj, settings.NOTIFICATION_TYPES[0][0])
        self.assertEqual(notification_count, Notification.objects.count())

        # If the receiver and reporter are different, a notification is created
        create_notification(self.receiver, self.reporter, self.social_obj, settings.NOTIFICATION_TYPES[0][0])
        self.assertEqual(notification_count + 1, Notification.objects.count())

    def test_correct_notification_type_sent(self):
        setting = NotificationSetting.objects.get(notification_type=settings.NOTIFICATION_TYPES[0][0],
                                                  user=self.receiver)

        # An email is sent if allow_email is True
        create_notification(self.receiver, self.reporter, self.social_obj, settings.NOTIFICATION_TYPES[0][0])
        self.assertEqual(len(mail.outbox), 1)
        # TODO: Add check for push notification

        # No new email is sent if allow_email is False
        setting.allow_email = False
        setting.save()
        create_notification(self.receiver, self.reporter, self.social_obj, settings.NOTIFICATION_TYPES[0][0])
        self.assertEqual(len(mail.outbox), 1)
        # TODO: A push message is still sent

        # allow_push can be False and an email will still send if allow_email is True
        setting.allow_email = True
        setting.allow_push = False
        setting.save()
        create_notification(self.receiver, self.reporter, self.social_obj, settings.NOTIFICATION_TYPES[0][0])
        self.assertEqual(len(mail.outbox), 2)
        # TODO: A push message is still sent

    def test_can_only_see_own_notifications(self):
        create_notification(self.receiver, self.reporter, self.social_obj, settings.NOTIFICATION_TYPES[0][0])
        create_notification(self.reporter, self.receiver, self.social_obj, settings.NOTIFICATION_TYPES[0][0])
        url = reverse("notifications")
        response = self.assertManticomGETResponse(url, None, "$notificationResponse", self.receiver)
        self.assertEqual(response.data["count"], self.receiver.notifications_received.count())

    def test_comment_creates_notification(self):
        url = reverse("comments-list")
        content_type = ContentType.objects.get_for_model(SocialModel)
        data = {
            "content_type": content_type.pk,
            "object_id": self.social_obj.pk,
            "description": "Yeti are cool"
        }
        self.assertManticomPOSTResponse(url, "$commentRequest", "$commentResponse", data, self.reporter)
        notification_count = Notification.objects.filter(user=self.social_obj.user,
                                                         reporter=self.reporter,
                                                         content_type=ContentType.objects.get_for_model(SocialModel),
                                                         notification_type=Notification.TYPES.comment).count()
        self.assertEquals(notification_count, 1)

    def test_follow_creates_notification(self):
        url = reverse("follows-list")
        content_type = ContentType.objects.get_for_model(User)
        data = {
            "content_type": content_type.pk,
            "object_id": self.receiver.pk,
        }
        self.assertManticomPOSTResponse(url, "$followRequest", "$followResponse", data, self.reporter)
        notification_count = Notification.objects.filter(user=self.receiver,
                                                         reporter=self.reporter,
                                                         content_type=ContentType.objects.get_for_model(User),
                                                         notification_type=Notification.TYPES.follow).count()
        self.assertEquals(notification_count, 1)

    def test_share_creates_notification(self):
        url = reverse("shares-list")
        content_type = ContentType.objects.get_for_model(SocialModel)
        data = {
            "content_type": content_type.pk,
            "object_id": self.social_obj.pk,
            "shared_with": [self.receiver.pk]
        }
        self.assertManticomPOSTResponse(url, "$shareRequest", "$shareResponse", data, self.reporter)
        notification_count = Notification.objects.filter(user=self.receiver,
                                                         reporter=self.reporter,
                                                         content_type=ContentType.objects.get_for_model(SocialModel),
                                                         notification_type=Notification.TYPES.share).count()
        self.assertEquals(notification_count, 1)

    def test_like_creates_notification(self):
        url = reverse("likes-list")
        content_type = ContentType.objects.get_for_model(SocialModel)
        data = {
            "content_type": content_type.pk,
            "object_id": self.social_obj.pk,
        }
        self.assertManticomPOSTResponse(url, "$likeRequest", "$likeResponse", data, self.reporter)
        notification_count = Notification.objects.filter(user=self.social_obj.user,
                                                         reporter=self.reporter,
                                                         content_type=ContentType.objects.get_for_model(SocialModel),
                                                         notification_type=Notification.TYPES.like).count()
        self.assertEquals(notification_count, 1)

    def comment_mention_creates_notification(self):
        """
        User receives a notification when their username is @mentioned, even if they are not the owner of the post
        """
        url = reverse("comments-list")
        content_type = ContentType.objects.get_for_model(SocialModel)
        data = {
            "content_type": content_type.pk,
            "object_id": SocialFactory().pk,
            "description": "@{} look at my cool comment!".format(self.social_obj.user.username)
        }
        self.assertManticomPOSTResponse(url, "$commentRequest", "$commentResponse", data, self.reporter)
        notification_count = Notification.objects.filter(user=self.social_obj.user,
                                                         reporter=self.reporter,
                                                         content_type=ContentType.objects.get_for_model(Comment),
                                                         notification_type=Notification.TYPES.mention).count()

        self.assertEquals(notification_count, 1)
