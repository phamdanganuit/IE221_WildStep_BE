"""
Admin views for Orders and Customers management
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.auth import require_admin
from .models import Order
from users.models import User
from bson import ObjectId
from datetime import datetime, timedelta


class OrderListView(APIView):
    """GET /api/admin/orders - List orders"""
    @require_admin
    def get(self, request):
        # TODO: Implement pagination, search, filters
        orders = Order.objects.all().order_by('-created_at')[:20]
        
        result = []
        for order in orders:
            result.append({
                "id": str(order.id),
                "orderNumber": order.order_number,
                "customer": {
                    "id": str(order.user.id),
                    "name": order.user.displayName or order.user.email,
                    "email": order.user.email,
                    "phone": order.user.phone
                } if order.user else None,
                "total": order.total_price,
                "status": order.status,
                "paymentStatus": order.payment_status,
                "orderDate": order.created_at.isoformat(),
                "completedDate": order.completed_date.isoformat() if order.completed_date else None
            })
        
        return Response({
            "data": result,
            "pagination": {
                "page": 1,
                "limit": 20,
                "total": Order.objects.count(),
                "totalPages": (Order.objects.count() + 19) // 20
            }
        })


class OrderDetailView(APIView):
    """GET /api/admin/orders/:id - Get order detail"""
    @require_admin
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=ObjectId(order_id))
        except (Order.DoesNotExist, Exception):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Order not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build full order response
        return Response({
            "id": str(order.id),
            "orderNumber": order.order_number,
            "customer": {
                "id": str(order.user.id),
                "name": order.user.displayName or order.user.email,
                "email": order.user.email,
                "phone": order.user.phone
            } if order.user else None,
            "items": [
                {
                    "product": {
                        "id": str(item.product_id),
                        "name": item.product_name,
                        "image": item.product_image
                    },
                    "quantity": item.quantity,
                    "price": item.price,
                    "total": item.total
                }
                for item in order.items
            ],
            "subtotal": order.subtotal,
            "shippingFee": order.shipping_fee,
            "discount": order.discount,
            "total": order.total_price,
            "status": order.status,
            "paymentMethod": order.payment_method,
            "paymentStatus": order.payment_status,
            "shippingAddress": {
                "receiver": order.address.receiver,
                "detail": order.address.detail,
                "ward": order.address.ward,
                "district": order.address.district,
                "province": order.address.province,
                "phone": order.address.phone
            } if order.address else None,
            "orderDate": order.created_at.isoformat(),
            "completedDate": order.completed_date.isoformat() if order.completed_date else None,
            "notes": order.notes
        })


class OrderStatusUpdateView(APIView):
    """PATCH /api/admin/orders/:id/status - Update order status"""
    @require_admin
    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=ObjectId(order_id))
        except (Order.DoesNotExist, Exception):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Order not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {"error": {"code": "MISSING_FIELD", "message": "Status is required"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status transitions
        current_status = order.status
        
        # Cannot change from completed or cancelled
        if current_status in ['completed', 'cancelled']:
            return Response(
                {"error": {"code": "INVALID_STATUS_TRANSITION", 
                          "message": f"Cannot change status from {current_status}"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        order.status = new_status
        order.save()
        
        return Response({
            "id": str(order.id),
            "orderNumber": order.order_number,
            "status": order.status,
            "completedDate": order.completed_date.isoformat() if order.completed_date else None
        })


class CustomerListView(APIView):
    """GET /api/admin/customers - List customers with stats"""
    @require_admin
    def get(self, request):
        # Get all users (exclude admins)
        users = User.objects(role="user")[:20]
        
        result = []
        for user in users:
            # Calculate stats from orders
            orders = Order.objects(user=user)
            total_orders = orders.count()
            
            # Calculate isVip and status
            is_vip = total_orders > 10
            
            # Check recent orders for status
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_order = orders.filter(created_at__gte=thirty_days_ago).order_by('-created_at').first()
            
            if user.blocked:
                customer_status = "blocked"
            elif is_vip:
                customer_status = "vip"
            elif recent_order:
                customer_status = "active"
            else:
                customer_status = "inactive"
            
            # Calculate spending
            completed_orders = orders.filter(status="completed")
            total_spent = sum(order.total_price for order in completed_orders)
            avg_order_value = total_spent / total_orders if total_orders > 0 else 0
            
            result.append({
                "id": str(user.id),
                "name": user.displayName or user.username or user.email,
                "displayName": user.displayName,
                "email": user.email,
                "phone": user.phone,
                "avatar": user.avatar,
                "totalOrders": total_orders,
                "totalSpent": total_spent,
                "averageOrderValue": avg_order_value,
                "lastOrder": recent_order.created_at.isoformat() if recent_order else None,
                "status": customer_status,
                "isVip": is_vip,
                "joinDate": user.created_at.isoformat()
            })
        
        return Response({
            "data": result,
            "pagination": {
                "page": 1,
                "limit": 20,
                "total": User.objects(role="user").count(),
                "totalPages": 1
            }
        })


# TODO: Implement CustomerDetailView, DashboardStatsView

