"""
Public URLs for products/content
"""
from django.urls import path
from .views import PublicBannerListView


urlpatterns = [
    path("content/banners", PublicBannerListView.as_view(), name="public_banners"),
]


