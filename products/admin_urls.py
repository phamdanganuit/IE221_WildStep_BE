"""
Admin URLs for products management
"""
from django.urls import path
from .admin_views import (
    BrandListView, BrandDetailView, BrandLogoUploadView,
    CategoryListView, CategoryDetailView,
    ProductListView, ProductDetailView, ProductImageUploadView,
    BannerListCreateView, BannerDetailView, BannerImageUploadView,
)

urlpatterns = [
    # Brands
    path("brands", BrandListView.as_view(), name="admin_brands"),
    path("brands/<str:brand_id>", BrandDetailView.as_view(), name="admin_brand_detail"),
    path("brands/<str:brand_id>/logo", BrandLogoUploadView.as_view(), name="admin_brand_logo"),
    
    # Categories
    path("categories", CategoryListView.as_view(), name="admin_categories"),
    path("categories/<str:category_id>", CategoryDetailView.as_view(), name="admin_category_detail"),
    
    # Products
    path("products", ProductListView.as_view(), name="admin_products"),
    path("products/<str:product_id>", ProductDetailView.as_view(), name="admin_product_detail"),
    path("products/<str:product_id>/images", ProductImageUploadView.as_view(), name="admin_product_images"),

    # Banners
    path("banners", BannerListCreateView.as_view(), name="admin_banners"),
    path("banners/<str:banner_id>", BannerDetailView.as_view(), name="admin_banner_detail"),
    path("banners/<str:banner_id>/image", BannerImageUploadView.as_view(), name="admin_banner_image"),
]

