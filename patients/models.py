from django.db import models
from django.contrib.auth.models import User
from doctors.models import Doctor


class Patient(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_profiles"
    )

    name = models.CharField(max_length=100)

    phone = models.CharField(max_length=15)

    age = models.PositiveIntegerField()

    gender = models.CharField(max_length=10)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Token(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )

    token_number = models.PositiveIntegerField()

    is_emergency = models.BooleanField(
        default=False
    )

    status = models.CharField(
        max_length=20,
        default="Waiting"
    )

    # Transfer information
    is_transferred = models.BooleanField(
        default=False
    )

    original_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="original_tokens"
    )

    original_token_number = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Token {self.token_number} - {self.patient.name}"