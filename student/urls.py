from django.urls import path

from . import views

app_name = "student"

urlpatterns = [
    path("health/", views.health_check, name="health"),
    path("health", views.health_check),
    path("", views.login_page, name="login_page"),
    path("login/", views.login_page, name="login_page_alt"),
    path("landing/", views.landing_page, name="landing_page"),
    path("logout/", views.logout_view, name="logout"),
]