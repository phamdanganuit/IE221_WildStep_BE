from django.urls import path
from .views import (
    CartView,
    CartItemAddView,
    CartItemDetailView,
    CartCountView,
    VoucherValidateView,
    OrderCreateView,
    OrderListView,
    OrderDetailView,
    OrderStatusUpdateView,
    OrderReviewableItemsView,
    OrderReviewCreateView,
    OrderReviewUpdateView,
    UserVoucherListView,
    AddVoucherView,
    RemoveVoucherView,
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
    path("vouchers", UserVoucherListView.as_view(), name="user-vouchers"),  # GET: list user vouchers
    path("vouchers/validate", VoucherValidateView.as_view(), name="voucher-validate"),
    path("addVoucher", AddVoucherView.as_view(), name="add-voucher"),  # POST: add voucher by code
    path("removeVoucher", RemoveVoucherView.as_view(), name="remove-voucher"),  # DELETE: remove voucher
    
    # Order endpoints
    # OrderListView handles both GET (list) and POST (create) for /orders
    path("orders", OrderListView.as_view(), name="order-list"),  # GET: list orders, POST: create order
    path("orders/<str:orderId>", OrderDetailView.as_view(), name="order-detail"),  # GET: get order detail
    path("orders/<str:orderId>/status", OrderStatusUpdateView.as_view(), name="order-status-update"),  # PATCH: update order status
    path("orders/<str:orderId>/reviewable-items", OrderReviewableItemsView.as_view(), name="order-reviewable-items"),
    path("orders/<str:orderId>/reviews", OrderReviewCreateView.as_view(), name="order-review-create"),
    path("orders/<str:orderId>/reviews/<str:reviewId>", OrderReviewUpdateView.as_view(), name="order-review-update"),
]

