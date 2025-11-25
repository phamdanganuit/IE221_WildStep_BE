from django.urls import path
from .views import (
    CartView,
    CartItemAddView,
    CartItemDetailView,
    CartCountView,
    VoucherValidateView,
    OrderCreateView
)

urlpatterns = [
    # Cart endpoints
    path("cart", CartView.as_view(), name="cart"),
    path("cart/count", CartCountView.as_view(), name="cart-count"),
    # Note: cart/items without param must come before cart/items/<str:cartItemId>
    # to handle DELETE /api/cart/items (clear all) vs DELETE /api/cart/items/:id (delete one)
    path("cart/items", CartItemAddView.as_view(), name="cart-item-add"),  # POST: add, DELETE: clear all
    path("cart/items/<str:cartItemId>", CartItemDetailView.as_view(), name="cart-item-detail"),  # PUT: update, DELETE: delete one
    
    # Voucher endpoints
    path("vouchers/validate", VoucherValidateView.as_view(), name="voucher-validate"),
    
    # Order endpoints
    path("orders", OrderCreateView.as_view(), name="order-create"),
]

