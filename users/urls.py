# users/urls.py (File mới)

from django.urls import path
from .views import (
    # Auth & OAuth
    FacebookOAuthView, GoogleOAuthView, RegisterView, LoginView, MeView,
    # Profile
    ProfileView, UpdateAvatarView,
    # Password
    ChangePasswordView,
    # Addresses
    AddressListView, AddressDetailView, AddressSetDefaultView,
    # Social Links
    SocialLinksView, LinkGoogleView, LinkFacebookView,
    # Notification Settings
    NotificationSettingsView
)

urlpatterns = [
    # ========== Auth & OAuth (đã có) ==========
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("me", MeView.as_view(), name="me"),
    path("oauth/google", GoogleOAuthView.as_view(), name="oauth_google"),
    path("oauth/facebook", FacebookOAuthView.as_view(), name="oauth_facebook"),
    
    # ========== Profile (mới) ==========
    path("profile", ProfileView.as_view(), name="profile"),  # GET, PUT
    path("profile/avatar", UpdateAvatarView.as_view(), name="update_avatar"),  # PUT - update avatar
    
    # ========== Account Management (mới) ==========
    path("me", MeView.as_view(), name="me"),  # GET, DELETE
    path("change-password", ChangePasswordView.as_view(), name="change_password"),  # POST
    
    # ========== Addresses (mới) ==========
    path("addresses", AddressListView.as_view(), name="addresses"),  # GET, POST
    path("addresses/<str:address_id>", AddressDetailView.as_view(), name="address_detail"),  # PUT, DELETE
    path("addresses/<str:address_id>/default", AddressSetDefaultView.as_view(), name="address_set_default"),  # PATCH
    
    # ========== Social Links (mới) ==========
    path("links", SocialLinksView.as_view(), name="social_links"),  # GET
    path("links/google", LinkGoogleView.as_view(), name="link_google"),  # POST, DELETE
    path("links/facebook", LinkFacebookView.as_view(), name="link_facebook"),  # POST, DELETE
    
    # ========== Notification Settings (mới) ==========
    path("notification-settings", NotificationSettingsView.as_view(), name="notification_settings"),  # GET, PUT
]