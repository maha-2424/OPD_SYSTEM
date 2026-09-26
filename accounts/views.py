from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

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


def login_view(request):

    # Get the URL the user originally wanted
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

            # Check whether this account belongs to a doctor
            if hasattr(user, "doctor_profile"):

                messages.error(
                    request,
                    "Doctor accounts cannot login through the patient portal. Please use Doctor Login."
                )

                return render(
                    request,
                    "accounts/login.html",
                    {
                        "next": next_url
                    }
                )

            # Normal patient login
            login(request, user)

            # Go back to the original page
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

def logout_view(request):

    logout(request)

    return redirect("login")


def dashboard(request):

    if not request.user.is_authenticated:

        return redirect("login")

    return render(
        request,
        "accounts/dashboard.html"
    )


def home(request):

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