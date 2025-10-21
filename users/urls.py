# users/urls.py (File mới)

from django.urls import path
# Giả sử các view của bạn nằm trong users/views.py
from .views import FacebookOAuthView, GoogleOAuthView, RegisterView, LoginView, MeView 

urlpatterns = [
    
    path("register", RegisterView.as_view(), name="register"),
    path("login",    LoginView.as_view(), name="login"),
    path("me",       MeView.as_view(), name="me"),
    path("oauth/google",   GoogleOAuthView.as_view(), name="oauth_google"),
    path("oauth/facebook", FacebookOAuthView.as_view(), name="oauth_facebook"),


    
]