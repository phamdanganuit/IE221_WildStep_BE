"""
Public URLs for products/content
"""
from django.urls import path
from .views import (
    PublicBannerListView,
    PublicBrandListView,
    PublicProductsListView,
    PublicCategoriesView,
    PublicReviewsView,
    PublicHeroView,
    ProductAutocompleteView,
    ProductSearchView,
    ProductDetailView,
)


urlpatterns = [
    path("content/banners", PublicBannerListView.as_view(), name="public_banners"),
    path("brands", PublicBrandListView.as_view(), name="public_brands"),
    path("products", PublicProductsListView.as_view(), name="public_products"),
    path("products/autocomplete", ProductAutocompleteView.as_view(), name="product_autocomplete"),
    path("products/search", ProductSearchView.as_view(), name="product_search"),
    path("products/<str:id_or_slug>", ProductDetailView.as_view(), name="product_detail"),
    path("categories", PublicCategoriesView.as_view(), name="public_categories"),
    path("reviews", PublicReviewsView.as_view(), name="public_reviews"),
    path("content/hero", PublicHeroView.as_view(), name="public_hero"),
]


