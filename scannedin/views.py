import base64
from datetime import timedelta
from io import BytesIO

import qrcode
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .forms import RegisterForm, LoginForm
from .models import UserProfile, AttendanceSession
from .forms import RegisterForm, LoginForm, QuickAttendanceSetupForm


def home(request):
    # Existing landing page
    return render(request, "scannedin/home.html")


def register_view(request):
    # Dedicated register page (not side-by-side with login)
    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        # Create base auth user using email as username for easy login
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
        )

        # Create related profile for phone + role
        UserProfile.objects.create(
            user=user,
            phone_number=form.cleaned_data.get("phone_number", "").strip(),
            role=form.cleaned_data["role"],
        )

        messages.success(request, "Account created! You can now log in.")
        return redirect("login")

    return render(request, "scannedin/register.html", {"form": form})


def login_view(request):
    # Dedicated login page with prompt to create account
    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            messages.success(request, "Welcome back!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "scannedin/login.html", {"form": form})


@login_required
def dashboard(request):
    # Basic post-login page for now
    role = getattr(request.user.profile, "role", "unknown")
    return render(request, "scannedin/dashboard.html", {"role": role})


@login_required
def logout_view(request):
    # Standard logout flow
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")

@login_required
def quick_attendance_setup(request):
    form = QuickAttendanceSetupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        request.session["quick_attendance_setup"] = {
            "course_name": form.cleaned_data["course_name"],
            "class_name": form.cleaned_data["class_name"],
            "duration_minutes": form.cleaned_data["duration_minutes"],
        }
        return redirect("start_quick_attendance")

    return render(request, "scannedin/quick_attendance_setup.html", {"form": form})

# Initialize attendance scanning session
@login_required
def start_quick_attendance(request):
    setup_data = request.session.get("quick_attendance_setup")
    if not setup_data:
        messages.error(request, "Please complete attendance setup first.")
        return redirect("quick_attendance_setup")

    duration_minutes = setup_data.get("duration_minutes", 5)
    expiry_time = timezone.now() + timedelta(minutes=duration_minutes)

    session = AttendanceSession.objects.create(
        professor=request.user,
        expires_at=expiry_time,
        course_name=setup_data.get("course_name", "").strip(),
        class_name=setup_data.get("class_name", "").strip(),
        duration_minutes=duration_minutes,
    )

    # Clear one-time setup data after creating the session
    request.session.pop("quick_attendance_setup", None)

    checkin_url = request.build_absolute_uri(
        reverse("quick_checkin", args=[session.token])
    )

    qr_img = qrcode.make(checkin_url)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render(
        request,
        "scannedin/session_created.html",
        {
            "session": session,
            "checkin_url": checkin_url,
            "qr_code": qr_code_base64,
        },
    )

def quick_checkin(request, token):
    session = get_object_or_404(AttendanceSession, token=token, is_active=True)

    if session.expires_at and timezone.now() > session.expires_at:
        return HttpResponse("This attendance session has expired.")

    return render(
        request,
        "scannedin/quick_checkin.html",
        {"session": session},
    )