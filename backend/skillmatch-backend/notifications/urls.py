from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationUnreadCountView,
    NotificationAnalyticsView,
)

urlpatterns = [
    path("",                NotificationListView.as_view(),         name="notification-list"),
    path("unread-count/",   NotificationUnreadCountView.as_view(),  name="notification-unread-count"),
    path("read-all/",       NotificationMarkAllReadView.as_view(),  name="notification-read-all"),
    path("analytics/",      NotificationAnalyticsView.as_view(),    name="notification-analytics"),
    path("<int:pk>/read/",  NotificationMarkReadView.as_view(),     name="notification-mark-read"),
]
