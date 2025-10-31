from django.urls import path
from .views import (
    FacebookOAuthView, GoogleOAuthView, RegisterView, LoginView, MeView,
    ProfileView, UpdateAvatarView,
    ChangePasswordView,
    AddressListView, AddressDetailView, AddressSetDefaultView,
    SocialLinksView, LinkGoogleView, LinkFacebookView,
    NotificationSettingsView
)

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("me", MeView.as_view(), name="me"),
    path("oauth/google", GoogleOAuthView.as_view(), name="oauth_google"),
    path("oauth/facebook", FacebookOAuthView.as_view(), name="oauth_facebook"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("profile/avatar", UpdateAvatarView.as_view(), name="update_avatar"),
    path("change-password", ChangePasswordView.as_view(), name="change_password"),
    path("addresses", AddressListView.as_view(), name="addresses"),
    path("addresses/<str:address_id>", AddressDetailView.as_view(), name="address_detail"),
    path("addresses/<str:address_id>/default", AddressSetDefaultView.as_view(), name="address_set_default"),
    path("links", SocialLinksView.as_view(), name="social_links"),
    path("links/google", LinkGoogleView.as_view(), name="link_google"),
    path("links/facebook", LinkFacebookView.as_view(), name="link_facebook"),
    path("notification-settings", NotificationSettingsView.as_view(), name="notification_settings"),
]