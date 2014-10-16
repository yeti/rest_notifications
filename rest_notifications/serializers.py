from rest_framework import serializers
from rest_notifications.rest_notifications.models import NotificationSetting

__author__ = 'baylee'


class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = ('id', 'notification_type', 'allow_push', 'allow_email')
        read_only_fields = ('id', 'notification_type')
