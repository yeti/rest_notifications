from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_core.rest_core.permissions import IsAuthorOrReadOnly
from rest_notifications.rest_notifications.models import NotificationSetting
from rest_notifications.rest_notifications.serializers import NotificationSettingSerializer

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
