from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Patient, Token
from doctors.models import Doctor


@login_required(login_url="/accounts/login/")
def generate_token(request):

    # Show all doctors
    doctors = Doctor.objects.all()

    # Doctor selected from homepage
    selected_doctor_id = request.GET.get("doctor")

    selected_doctor = None

    if selected_doctor_id:
        selected_doctor = Doctor.objects.filter(
            id=selected_doctor_id
        ).first()

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        age = request.POST.get("age")
        gender = request.POST.get("gender")

        doctor_id = request.POST.get("doctor")
        is_emergency = request.POST.get("is_emergency") == "on"

        # Select doctor
        doctor = get_object_or_404(
            Doctor,
            id=doctor_id
        )

        # Prevent booking with unavailable doctor
        if not doctor.available:

            return render(
                request,
                "patients/generate_token.html",
                {
                    "doctors": doctors,
                    "selected_doctor": doctor,
                    "error": (
                        "This doctor is not available today. "
                        "Please select another doctor."
                    )
                }
            )

        # Create patient and connect the patient
        # to the currently logged-in User
        patient = Patient.objects.create(
            user=request.user,
            name=name,
            phone=phone,
            age=age,
            gender=gender
        )

        # Generate next token number for this doctor
        last_token = Token.objects.filter(
            doctor=doctor
        ).order_by(
            "-token_number"
        ).first()

        if last_token:

            token_number = last_token.token_number + 1

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

        # Calculate estimated waiting time
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

        # Keep token ID in session for immediate access
        request.session["my_token_id"] = token.id

        return render(
            request,
            "patients/token_success.html",
            {
                "patient": patient,
                "doctor": doctor,
                "token_number": token_number,
                "waiting_time": waiting_time,
                "patients_ahead": patients_ahead,
                "is_emergency": is_emergency
            }
        )

    return render(
        request,
        "patients/generate_token.html",
        {
            "doctors": doctors,
            "selected_doctor": selected_doctor
        }
    )


@login_required(login_url="/accounts/login/")
def view_token(request):

    # Find the latest active token belonging
    # to the currently logged-in patient
    token = Token.objects.filter(
        patient__user=request.user
    ).exclude(
        status="Completed"
    ).select_related(
        "patient",
        "doctor"
    ).order_by(
        "-created_at"
    ).first()

    # No active token
    if not token:

        return render(
            request,
            "patients/my_token.html",
            {
                "error": (
                    "No active token found. "
                    "Please generate a token first."
                )
            }
        )

    doctor = token.doctor

    # Calculate current patients ahead
    if token.status == "Waiting":

        if token.is_emergency:

            patients_ahead = Token.objects.filter(
                doctor=doctor,
                status="Waiting",
                is_emergency=True,
                created_at__lt=token.created_at
            ).count()

        else:

            emergency_ahead = Token.objects.filter(
                doctor=doctor,
                status="Waiting",
                is_emergency=True
            ).count()

            normal_ahead = Token.objects.filter(
                doctor=doctor,
                status="Waiting",
                is_emergency=False,
                token_number__lt=token.token_number
            ).count()

            patients_ahead = (
                emergency_ahead
                + normal_ahead
            )

        waiting_time = (
            patients_ahead
            * doctor.consultation_time
        )

    elif token.status == "Serving":

        # Doctor is currently serving this patient
        patients_ahead = 0
        waiting_time = 0

    else:

        patients_ahead = 0
        waiting_time = 0

    return render(
        request,
        "patients/my_token.html",
        {
            "token": token,
            "patient": token.patient,
            "doctor": doctor,
            "patients_ahead": patients_ahead,
            "waiting_time": waiting_time
        }
    )


@login_required(login_url="/accounts/login/")
def queue_display(request):

    # Find the patient profile of the logged-in user
    patient = Patient.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    ).first()

    if not patient:

        return render(
            request,
            "patients/queue_display.html",
            {
                "doctor_queues": [],
                "error": "Patient profile not found."
            }
        )

    # Find the patient's latest token
    token = Token.objects.filter(
        patient=patient
    ).exclude(
        status="Completed"
    ).select_related(
        "doctor",
        "patient"
    ).order_by(
        "-created_at"
    ).first()

    if not token:

        return render(
            request,
            "patients/queue_display.html",
            {
                "doctor_queues": [],
                "error": "No active token found. Please generate a token first."
            }
        )

    # Get the doctor assigned to this patient's token
    doctor = token.doctor

    # Get ONLY this doctor's waiting queue
    tokens = Token.objects.filter(
        doctor=doctor,
        status="Waiting"
    ).select_related(
        "patient"
    ).order_by(
        "-is_emergency",
        "token_number"
    )

    doctor_queues = [
        {
            "doctor": doctor,
            "tokens": tokens
        }
    ]

    return render(
        request,
        "patients/queue_display.html",
        {
            "doctor_queues": doctor_queues,
            "my_token": token
        }
    )

@login_required(login_url="/accounts/login/")
def queue_management(request):

    doctors = Doctor.objects.filter(
        available=True
    )

    doctor_queues = []

    for doctor in doctors:

        waiting_tokens = Token.objects.filter(
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

        doctor_queues.append({
            "doctor": doctor,
            "tokens": waiting_tokens,
            "serving_token": serving_token
        })

    return render(
        request,
        "patients/queue_management.html",
        {
            "doctor_queues": doctor_queues
        }
    )


@login_required(login_url="/accounts/login/")
def start_serving(request, token_id):

    token = get_object_or_404(
        Token,
        id=token_id
    )

    # Make sure the token belongs to
    # the logged-in doctor
    if token.doctor.user != request.user:

        return redirect("doctor_dashboard")

    if request.method == "POST":

        token.status = "Serving"

        token.save()

    return redirect("doctor_dashboard")


@login_required(login_url="/accounts/login/")
def complete_token(request, token_id):

    token = get_object_or_404(
        Token,
        id=token_id
    )

    # Make sure the token belongs to
    # the logged-in doctor
    if token.doctor.user != request.user:

        return redirect("doctor_dashboard")

    if request.method == "POST":

        token.status = "Completed"

        token.save()

    return redirect("doctor_dashboard")