from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from patients.models import Patient, Token
from doctors.models import Doctor


@login_required(login_url="/accounts/login/")
def receptionist_register_patient(request):

    doctors = Doctor.objects.filter(
        available=True
    ).order_by(
        "specialization",
        "name"
    )

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        age = request.POST.get("age")
        gender = request.POST.get("gender")

        doctor_id = request.POST.get("doctor")
        is_emergency = request.POST.get(
            "is_emergency"
        ) == "on"

        # Get selected doctor
        doctor = get_object_or_404(
            Doctor,
            id=doctor_id,
            available=True
        )

        # Create patient without connecting
        # the patient to the receptionist's User
        patient = Patient.objects.create(
            user=None,
            name=name,
            phone=phone,
            age=age,
            gender=gender
        )

        # Find next token for this doctor
        last_token = Token.objects.filter(
            doctor=doctor
        ).order_by(
            "-token_number"
        ).first()

        if last_token:
            token_number = (
                last_token.token_number + 1
            )
        else:
            token_number = 1

        # Calculate patients ahead
        if is_emergency:

            patients_ahead = Token.objects.filter(
                doctor=doctor,
                status="Waiting",
                is_emergency=True
            ).count()

        else:

            normal_patients_ahead = Token.objects.filter(
                doctor=doctor,
                status="Waiting",
                token_number__lt=token_number,
                is_emergency=False
            ).count()

            emergency_patients_ahead = Token.objects.filter(
                doctor=doctor,
                status="Waiting",
                is_emergency=True
            ).count()

            patients_ahead = (
                normal_patients_ahead
                + emergency_patients_ahead
            )

        waiting_time = (
            patients_ahead
            * doctor.consultation_time
        )

        # Create token
        token = Token.objects.create(
            patient=patient,
            doctor=doctor,
            token_number=token_number,
            is_emergency=is_emergency
        )

        return render(
            request,
            "reception/reception_success.html",
            {
                "patient": patient,
                "doctor": doctor,
                "token": token,
                "token_number": token_number,
                "patients_ahead": patients_ahead,
                "waiting_time": waiting_time,
                "is_emergency": is_emergency
            }
        )

    return render(
        request,
        "reception/register_patient.html",
        {
            "doctors": doctors
        }
    )