from rest_framework import mixins, generics
from rest_framework.viewsets import GenericViewSet
from rest_core.rest_core.permissions import IsAuthorOrReadOnly
from rest_notifications.rest_notifications.models import NotificationSetting, Notification, create_notification
from rest_notifications.rest_notifications.serializers import NotificationSettingSerializer, NotificationSerializer
from rest_social.rest_social.views import CommentViewSet, FollowViewSet, ShareViewSet, LikeViewSet

__author__ = 'baylee'


class NotificationSettingViewSet(mixins.UpdateModelMixin,
                                 mixins.ListModelMixin,
                                 GenericViewSet):
    queryset = NotificationSetting.objects.all()
    serializer_class = NotificationSettingSerializer
    permission_classes = (IsAuthorOrReadOnly,)

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
