from django.urls import path
from .views import (
    CartView,
    CartItemAddView,
    CartItemDetailView,
    VoucherValidateView,
    OrderCreateView
)

urlpatterns = [
    # Cart endpoints
    path("cart", CartView.as_view(), name="cart"),
    path("cart/items", CartItemAddView.as_view(), name="cart-item-add"),
    path("cart/items/<str:cartItemId>", CartItemDetailView.as_view(), name="cart-item-detail"),
    
    # Voucher endpoints
    path("vouchers/validate", VoucherValidateView.as_view(), name="voucher-validate"),
    
    # Order endpoints
    path("orders", OrderCreateView.as_view(), name="order-create"),
]

