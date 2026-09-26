from django.urls import path

from . import views


urlpatterns = [

    path(
        "register-patient/",
        views.receptionist_register_patient,
        name="receptionist_register_patient"
    ),

]