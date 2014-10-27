from django.conf import settings
from rest_framework import mixins, generics
from rest_framework.exceptions import APIException
from rest_framework.viewsets import GenericViewSet
from pypushwoosh import client, constants
from pypushwoosh.command import RegisterDeviceCommand
from rest_core.rest_core.permissions import IsOwner
from rest_notifications.rest_notifications.models import NotificationSetting, Notification, create_notification, \
    PushwooshToken
from rest_notifications.rest_notifications.serializers import NotificationSettingSerializer, NotificationSerializer, \
    PushwooshTokenSerializer
from rest_social.rest_social.views import CommentViewSet, FollowViewSet, ShareViewSet, LikeViewSet

__author__ = 'baylee'


class PushwooshTokenView(generics.CreateAPIView):
    queryset = PushwooshToken.objects.all()
    serializer_class = PushwooshTokenSerializer
    permission_classes = (IsOwner,)

    def pre_save(self, obj):
        obj.user = self.request.user

        push_client = client.PushwooshClient()
        command = RegisterDeviceCommand(settings.PUSHWOOSH_APP_CODE, obj.hwid, constants.PLATFORM_IOS, obj.language,
                                        obj.token)
        response = push_client.invoke(command)

        if response["status_code"] != 200:
            raise APIException("Authentication with notification service failed")


class NotificationSettingViewSet(mixins.UpdateModelMixin,
                                 mixins.ListModelMixin,
                                 GenericViewSet):
    queryset = NotificationSetting.objects.all()
    serializer_class = NotificationSettingSerializer
    permission_classes = (IsOwner,)

    def pre_save(self, obj):
        obj.user = self.request.user

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class NotificationView(generics.ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class NotificationCommentViewSet(CommentViewSet):
    def post_save(self, obj, created=False):
        if created:
            create_notification(obj.content_object.user, obj.user, obj.content_object, Notification.TYPES.comment)


class NotificationFollowViewSet(FollowViewSet):
    def post_save(self, obj, created=False):
        if created:
            create_notification(obj.content_object, obj.user, obj.content_object, Notification.TYPES.follow)


class NotificationShareViewSet(ShareViewSet):
    def post_save(self, obj, created=False):
        if created:
            for receiver in obj.shared_with.all():
                create_notification(receiver, obj.user, obj.content_object, Notification.TYPES.share)


class NotificationLikeViewSet(LikeViewSet):
    def post_save(self, obj, created=False):
        if created:
            create_notification(obj.content_object.user, obj.user, obj.content_object, Notification.TYPES.like)
