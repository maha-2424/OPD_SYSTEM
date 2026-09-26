from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache

from doctors.models import Doctor
from patients.models import Token


def signup_view(request):

    next_url = request.GET.get("next")

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        next_url = request.POST.get("next")

        # Check password
        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            if next_url:
                return redirect(
                    f"/accounts/signup/?next={next_url}"
                )

            return redirect("signup")

        # Check username
        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            if next_url:
                return redirect(
                    f"/accounts/signup/?next={next_url}"
                )

            return redirect("signup")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        messages.success(
            request,
            "Account created successfully. Please login."
        )

        if next_url:
            return redirect(
                f"/accounts/login/?next={next_url}"
            )

        return redirect("login")

    return render(
        request,
        "accounts/signup.html",
        {
            "next": next_url
        }
    )


@never_cache
def login_view(request):

    next_url = request.GET.get("next")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        next_url = request.POST.get("next")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # --------------------------------------------------
            # DOCTOR ACCOUNT
            # --------------------------------------------------

            if Doctor.objects.filter(
                user=user
            ).exists():

                messages.error(
                    request,
                    "This is a doctor account. Please use Doctor Login."
                )

                return render(
                    request,
                    "accounts/login.html",
                    {
                        "next": next_url
                    }
                )

            # --------------------------------------------------
            # PATIENT ACCOUNT
            # --------------------------------------------------

            login(request, user)

            if next_url:
                return redirect(next_url)

            return redirect("home")

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

            return render(
                request,
                "accounts/login.html",
                {
                    "next": next_url
                }
            )

    return render(
        request,
        "accounts/login.html",
        {
            "next": next_url
        }
    )


@never_cache
def doctor_logout_view(request):

    # Completely remove the current login session
    logout(request)

    # Send doctor back to Doctor Login
    return redirect("doctor_login")


@never_cache
def logout_view(request):

    # Completely remove the current login session
    logout(request)

    # Send patient back to Patient Login
    return redirect("login")


@never_cache
def dashboard(request):

    if not request.user.is_authenticated:

        return redirect("login")

    # Doctor account should never enter
    # the patient dashboard.
    if Doctor.objects.filter(
        user=request.user
    ).exists():

        return redirect("doctor_dashboard")

    return render(
        request,
        "accounts/dashboard.html"
    )


@never_cache
def home(request):

    # --------------------------------------------------
    # IMPORTANT ROLE CHECK
    # --------------------------------------------------

    if request.user.is_authenticated:

        # If this is a doctor account,
        # send the doctor to the doctor portal.
        if Doctor.objects.filter(
            user=request.user
        ).exists():

            return redirect("doctor_dashboard")

    # --------------------------------------------------
    # PATIENT HOME PAGE
    # --------------------------------------------------

    doctors = Doctor.objects.filter(
        available=True
    ).order_by(
        "specialization",
        "name"
    )

    doctor_data = []

    for doctor in doctors:

        waiting_count = Token.objects.filter(
            doctor=doctor,
            status="Waiting"
        ).count()

        doctor_data.append({
            "doctor": doctor,
            "waiting_count": waiting_count
        })

    return render(
        request,
        "accounts/home.html",
        {
            "doctor_data": doctor_data
        }
    )