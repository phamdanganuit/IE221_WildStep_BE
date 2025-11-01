"""
Admin URLs for orders and customers management
"""
from django.urls import path
from .admin_views import (
    OrderListView, OrderDetailView, OrderStatusUpdateView,
    CustomerListView, CustomerDetailView, CustomerStatusUpdateView,
)
from .dashboard_views import DashboardStatsView, AnalyticsView

urlpatterns = [
    # Dashboard
    path("dashboard/stats", DashboardStatsView.as_view(), name="admin_dashboard_stats"),
    path("analytics", AnalyticsView.as_view(), name="admin_analytics"),
    
    # Orders
    path("orders", OrderListView.as_view(), name="admin_orders"),
    path("orders/<str:order_id>", OrderDetailView.as_view(), name="admin_order_detail"),
    path("orders/<str:order_id>/status", OrderStatusUpdateView.as_view(), name="admin_order_status"),
    
    # Customers
    path("customers", CustomerListView.as_view(), name="admin_customers"),
    path("customers/<str:customer_id>", CustomerDetailView.as_view(), name="admin_customer_detail"),
    path("customers/<str:customer_id>/status", CustomerStatusUpdateView.as_view(), name="admin_customer_status"),
]

