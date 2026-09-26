from django.db import models
from django.contrib.auth.models import User


class Doctor(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="doctor_profile"
    )

    name = models.CharField(max_length=100)

    specialization = models.CharField(max_length=100)

    phone = models.CharField(max_length=15)

    consultation_time = models.PositiveIntegerField(
        help_text="Average consultation time in minutes"
    )

    available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.name}"