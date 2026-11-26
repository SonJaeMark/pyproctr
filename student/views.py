from django.http import JsonResponse
from django.shortcuts import redirect, render

from .gateway_client import (
    GatewayError,
    get_current_user,
    login_student,
    refresh_access_token,
)


def health_check(request):
    return JsonResponse({"status": "ok"})


def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not email or not password:
            return render(
                request,
                "student/login.html",
                {"error": "Please enter both email and password.", "email": email},
            )

        try:
            tokens = login_student(email=email, password=password)
        except GatewayError as exc:
            return render(
                request,
                "student/login.html",
                {"error": str(exc), "email": email},
            )

        access_token = tokens.get("accessToken")
        if not access_token:
            return render(
                request,
                "student/login.html",
                {
                    "error": "Authentication succeeded, but no access token was returned.",
                    "email": email,
                },
            )

        request.session.cycle_key()
        request.session["access_token"] = access_token
        if tokens.get("refreshToken"):
            request.session["refresh_token"] = tokens["refreshToken"]
        request.session["student_email"] = email

        return redirect("student:landing_page")

    return render(request, "student/login.html")


def landing_page(request):
    access_token = request.session.get("access_token")
    refresh_token = request.session.get("refresh_token")

    if not access_token:
        return redirect("student:login_page")

    try:
        status_code, profile = get_current_user(access_token)

        if status_code == 401 and refresh_token:
            refreshed = refresh_access_token(refresh_token)
            if refreshed and refreshed.get("accessToken"):
                access_token = refreshed["accessToken"]
                request.session["access_token"] = access_token
                status_code, profile = get_current_user(access_token)
    except GatewayError as exc:
        return render(
            request,
            "student/landing.html",
            {"profile": None, "gateway_error": str(exc)},
        )

    if status_code != 200:
        request.session.flush()
        return redirect("student:login_page")

    # Landing page remains intentionally blank for now while verified via gateway
    return render(request, "student/landing.html", {"profile": profile})
