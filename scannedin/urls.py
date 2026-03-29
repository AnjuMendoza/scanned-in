from django.urls import path
from .views import (
    home,
    register_view,
    login_view,
    dashboard,
    logout_view,
    start_quick_attendance,
    quick_checkin,
)

urlpatterns = [
    path("", home, name="home"),
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("dashboard/", dashboard, name="dashboard"),
    path("logout/", logout_view, name="logout"),

    # Quick attendance
    path("quick-attendance/start/", start_quick_attendance, name="start_quick_attendance"),
    path("quick-attendance/checkin/<uuid:token>/", quick_checkin, name="quick_checkin"),
]