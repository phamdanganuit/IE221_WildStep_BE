from django.contrib import admin
from django.urls import path
from api.views import RegisterView, LoginView, MeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/register", RegisterView.as_view()),
    path("api/login",    LoginView.as_view()),
    path("api/me",       MeView.as_view()),
]
