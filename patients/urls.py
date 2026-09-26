from django.urls import path
from . import views


urlpatterns = [

    path(
        "token/",
        views.generate_token,
        name="generate_token"
    ),

    path(
        "my-token/",
        views.view_token,
        name="view_token"
    ),

    path(
        "queue/",
        views.queue_display,
        name="queue_display"
    ),

    path(
        "manage/",
        views.queue_management,
        name="queue_management"
    ),

    path(
        "start-serving/<int:token_id>/",
        views.start_serving,
        name="start_serving"
    ),

    path(
        "complete/<int:token_id>/",
        views.complete_token,
        name="complete_token"
    ),

path(
    "live-display/",
    views.live_display,
    name="live_display"
), 
]