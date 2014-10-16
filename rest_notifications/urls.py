from django.conf.urls import patterns, url, include
from rest_framework import routers
from rest_notifications.rest_notifications.views import NotificationSettingViewSet


router = routers.DefaultRouter()

router.register(r'notification_settings', NotificationSettingViewSet, base_name='notification_settings')

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
)
