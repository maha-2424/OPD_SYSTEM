from django.urls import path

from . import views


urlpatterns = [

    path(
        "register/",
        views.doctor_registration,
        name="doctor_registration"
    ),

    path(
        "login/",
        views.doctor_login,
        name="doctor_login"
    ),

    path(
        "manage/",
        views.doctor_management,
        name="doctor_management"
    ),

    path(
        "toggle/<int:doctor_id>/",
        views.toggle_doctor_availability,
        name="toggle_doctor_availability"
    ),

    path(
        "dashboard/",
        views.doctor_dashboard,
        name="doctor_dashboard"
    ),

    path(
        "profile/",
        views.doctor_profile,
        name="doctor_profile"
    ),

    path(
        "logout/",
        views.doctor_logout,
        name="doctor_logout"
    ),

]