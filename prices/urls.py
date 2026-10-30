from django.urls import path

from prices import views

app_name = "prices"

urlpatterns = [
    path("latest.json", views.latest_json, name="latest_json"),
]
