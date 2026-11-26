from django.urls import path

from . import views

app_name = "student"

urlpatterns = [
    path("", views.login_page, name="login_page"),
    path("login/", views.login_page, name="login_page_alt"),
    path("landing/", views.landing_page, name="landing_page"),
]
