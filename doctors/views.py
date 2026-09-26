from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .models import Doctor
from patients.models import Token


def doctor_registration(request):

    if request.method == "POST":

        name = request.POST.get("name")
        specialization = request.POST.get("specialization")
        phone = request.POST.get("phone")
        consultation_time = request.POST.get("consultation_time")

        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Check password
        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("doctor_registration")

        # Check username
        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("doctor_registration")

        # Create Django login account
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # Create doctor profile and connect it to user
        Doctor.objects.create(
            user=user,
            name=name,
            specialization=specialization,
            phone=phone,
            consultation_time=consultation_time
        )

        messages.success(
            request,
            "Doctor registered successfully. Please login."
        )

        return redirect("doctor_login")

    return render(
        request,
        "doctors/doctor_registration.html"
    )


def doctor_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Only users connected to a Doctor profile
            # can enter the doctor portal.
            if Doctor.objects.filter(
                user=user
            ).exists():

                login(request, user)

                return redirect("doctor_dashboard")

            else:

                messages.error(
                    request,
                    "This account is not registered as a doctor."
                )

                return render(
                    request,
                    "doctors/doctor_login.html"
                )

        else:

            messages.error(
                request,
                "Invalid doctor username or password."
            )

    return render(
        request,
        "doctors/doctor_login.html"
    )


def doctor_logout(request):

    # Completely remove the current login session
    logout(request)

    # Return to Doctor Login
    return redirect("doctor_login")


def doctor_management(request):

    doctors = Doctor.objects.all().order_by(
        "specialization",
        "name"
    )

    return render(
        request,
        "doctors/doctor_management.html",
        {
            "doctors": doctors
        }
    )


def toggle_doctor_availability(request, doctor_id):

    doctor = get_object_or_404(
        Doctor,
        id=doctor_id
    )

    if request.method == "POST":

        if doctor.available:

            doctor.available = False
            doctor.save()

            transfer_waiting_patients(doctor)

        else:

            doctor.available = True
            doctor.save()

    # If the logged-in doctor is changing
    # their own availability, stay in doctor portal.
    if request.user.is_authenticated:

        if Doctor.objects.filter(
            user=request.user,
            id=doctor.id
        ).exists():

            return redirect("doctor_dashboard")

    # Otherwise, this action came from
    # Doctor Management.
    return redirect("doctor_management")


def transfer_waiting_patients(unavailable_doctor):

    waiting_tokens = list(
        Token.objects.filter(
            doctor=unavailable_doctor,
            status="Waiting"
        ).order_by(
            "-is_emergency",
            "created_at"
        )
    )

    available_doctors = list(
        Doctor.objects.filter(
            specialization=unavailable_doctor.specialization,
            available=True
        ).exclude(
            id=unavailable_doctor.id
        ).order_by(
            "id"
        )
    )

    if not available_doctors:
        return

    doctor_queues = {}

    for doctor in available_doctors:

        doctor_queues[doctor.id] = Token.objects.filter(
            doctor=doctor,
            status="Waiting"
        ).count()

    next_token_numbers = {}

    for doctor in available_doctors:

        last_token = Token.objects.filter(
            doctor=doctor
        ).order_by(
            "-token_number"
        ).first()

        if last_token:

            next_token_numbers[doctor.id] = (
                last_token.token_number + 1
            )

        else:

            next_token_numbers[doctor.id] = 1

    for token in waiting_tokens:

        smallest_queue = min(
            doctor_queues.values()
        )

        smallest_doctors = [
            doctor
            for doctor in available_doctors
            if doctor_queues[doctor.id] == smallest_queue
        ]

        selected_doctor = smallest_doctors[0]

        # Preserve original information
        token.original_doctor = unavailable_doctor
        token.original_token_number = token.token_number

        # Assign receiving doctor
        token.doctor = selected_doctor

        # New token number
        token.token_number = next_token_numbers[
            selected_doctor.id
        ]

        token.is_transferred = True

        token.save()

        next_token_numbers[
            selected_doctor.id
        ] += 1

        doctor_queues[
            selected_doctor.id
        ] += 1


@login_required(login_url="/doctor/login/")
def doctor_dashboard(request):

    try:

        doctor = request.user.doctor_profile

    except Doctor.DoesNotExist:

        return redirect("doctor_login")

    tokens = Token.objects.filter(
        doctor=doctor,
        status="Waiting"
    ).order_by(
        "-is_emergency",
        "token_number"
    )

    serving_token = Token.objects.filter(
        doctor=doctor,
        status="Serving"
    ).first()

    return render(
        request,
        "doctors/doctor_dashboard.html",
        {
            "doctor": doctor,
            "tokens": tokens,
            "serving_token": serving_token
        }
    )


@login_required(login_url="/doctor/login/")
def doctor_profile(request):

    try:

        doctor = request.user.doctor_profile

    except Doctor.DoesNotExist:

        return redirect("doctor_login")

    if request.method == "POST":

        # Toggle ONLY the logged-in doctor's availability
        doctor.available = not doctor.available

        doctor.save()

        # If doctor becomes unavailable,
        # transfer waiting patients
        if not doctor.available:

            transfer_waiting_patients(doctor)

        # Stay inside the doctor's own profile page
        return redirect("doctor_profile")

    return render(
        request,
        "doctors/doctor_profile.html",
        {
            "doctor": doctor
        }
    )