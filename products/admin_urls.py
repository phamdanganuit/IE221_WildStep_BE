"""
Admin URLs for products management
"""
from django.urls import path
from .admin_views import (
    BrandListView, BrandDetailView,
    # CategoryListView, CategoryDetailView,
    # ProductListView, ProductDetailView,
)

urlpatterns = [
    # Brands
    path("brands", BrandListView.as_view(), name="admin_brands"),
    path("brands/<str:brand_id>", BrandDetailView.as_view(), name="admin_brand_detail"),
    
    # Categories - TODO
    # path("categories", CategoryListView.as_view(), name="admin_categories"),
    # path("categories/<str:category_id>", CategoryDetailView.as_view(), name="admin_category_detail"),
    
    # Products - TODO
    # path("products", ProductListView.as_view(), name="admin_products"),
    # path("products/<str:product_id>", ProductDetailView.as_view(), name="admin_product_detail"),
]

