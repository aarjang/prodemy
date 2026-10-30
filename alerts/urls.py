from django.urls import path

from alerts import views

app_name = "alerts"

urlpatterns = [
    path("alerts/", views.AlertListView.as_view(), name="list"),
    path("alerts/new/", views.AlertCreateView.as_view(), name="create"),
    path("alerts/<int:pk>/edit/", views.AlertUpdateView.as_view(), name="edit"),
    path("alerts/<int:pk>/pause/", views.alert_pause, name="pause"),
    path("alerts/<int:pk>/resume/", views.alert_resume, name="resume"),
    path("alerts/<int:pk>/delete/", views.AlertDeleteView.as_view(), name="delete"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:pk>/read/", views.notification_read, name="notification_read"),
    path("notifications/read-all/", views.notifications_read_all, name="notifications_read_all"),
    path("notifications/unread-count.json", views.unread_count_json, name="unread_count_json"),
]
