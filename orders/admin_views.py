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
from mongoengine.queryset.visitor import Q


class OrderListView(APIView):
    """GET /api/admin/orders - List orders"""
    @require_admin
    def get(self, request):
        # Query params
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
        search = (request.query_params.get("search") or "").strip()
        status_filter = (request.query_params.get("status") or "").strip().lower()
        payment_status = (request.query_params.get("paymentStatus") or "").strip().lower()
        start_date = (request.query_params.get("startDate") or "").strip()
        end_date = (request.query_params.get("endDate") or "").strip()
        sort = (request.query_params.get("sort") or "createdAt").strip()
        order_dir = (request.query_params.get("order") or "desc").strip().lower()

        # Build base query
        q = Q()

        # Filter by date range
        if start_date:
            try:
                dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                q = q & Q(created_at__gte=dt)
            except Exception:
                pass
        if end_date:
            try:
                dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                q = q & Q(created_at__lte=dt)
            except Exception:
                pass

        if status_filter:
            q = q & Q(status=status_filter)
        if payment_status:
            q = q & Q(payment_status=payment_status)

        # Execute initial query
        qs = Order.objects(q)

        # Search by orderNumber or customer info
        if search:
            # First, filter by order number contains
            candidate_orders = list(qs.filter(order_number__icontains=search))
            # Then, search by customer name/email/phone
            user_q = (
                Q(email__icontains=search) |
                Q(displayName__icontains=search) |
                Q(username__icontains=search) |
                Q(phone__icontains=search)
            )
            matched_users = list(User.objects(user_q))
            if matched_users:
                user_ids = {u.id for u in matched_users}
                candidate_orders += list(qs.filter(user__in=list(user_ids)))
            # Deduplicate
            seen = set()
            orders = []
            for o in candidate_orders:
                if o.id not in seen:
                    seen.add(o.id)
                    orders.append(o)
            qs_list = orders
        else:
            qs_list = list(qs)

        # Sorting
        reverse = (order_dir != "asc")
        if sort == "total":
            qs_list.sort(key=lambda x: x.total_price or 0, reverse=reverse)
        elif sort == "status":
            qs_list.sort(key=lambda x: x.status or "", reverse=reverse)
        elif sort == "paymentStatus":
            qs_list.sort(key=lambda x: x.payment_status or "", reverse=reverse)
        else:  # createdAt default
            qs_list.sort(key=lambda x: x.created_at or datetime.min, reverse=reverse)

        # Pagination
        total = len(qs_list)
        start = (page - 1) * limit
        end = start + limit
        page_items = qs_list[start:end]

        # Build response
        result = []
        for order in page_items:
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
                "orderDate": order.created_at.isoformat() if order.created_at else None,
                "completedDate": order.completed_date.isoformat() if order.completed_date else None
            })

        return Response({
            "data": result,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit,
                "hasNext": end < total,
                "hasPrev": start > 0
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
        # Query params
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
        search = (request.query_params.get("search") or "").strip()
        status_filter = (request.query_params.get("status") or "").strip().lower()  # active|inactive|vip|blocked
        sort = (request.query_params.get("sort") or "").strip()  # name|totalOrders|totalSpent|joinDate
        order_dir = (request.query_params.get("order") or "desc").strip().lower()  # asc|desc

        # Base query: users only
        query = Q(role="user")
        if search:
            query = query & (
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(displayName__icontains=search) |
                Q(phone__icontains=search)
            )
        if status_filter == "blocked":
            query = query & Q(blocked=True)

        users_qs = User.objects(query)

        # Compute stats
        results_with_stats = []
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        for user in users_qs:
            orders_qs = Order.objects(user=user)
            total_orders = orders_qs.count()
            is_vip = total_orders > 10
            recent_order = orders_qs.filter(created_at__gte=thirty_days_ago).order_by('-created_at').first()

            if user.blocked:
                customer_status = "blocked"
            elif is_vip:
                customer_status = "vip"
            elif recent_order:
                customer_status = "active"
            else:
                customer_status = "inactive"

            completed_orders = orders_qs.filter(status="completed")
            total_spent = sum(o.total_price for o in completed_orders)
            avg_order_value = total_spent / total_orders if total_orders > 0 else 0

            if status_filter and status_filter != "blocked" and customer_status != status_filter:
                continue

            results_with_stats.append({
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

        # Sorting
        reverse = (order_dir != "asc")
        if sort == "name":
            results_with_stats.sort(key=lambda x: (x["name"] or "").lower(), reverse=reverse)
        elif sort == "totalOrders":
            results_with_stats.sort(key=lambda x: x["totalOrders"], reverse=reverse)
        elif sort == "totalSpent":
            results_with_stats.sort(key=lambda x: x["totalSpent"], reverse=reverse)
        elif sort == "joinDate":
            results_with_stats.sort(key=lambda x: x["joinDate"] or "", reverse=reverse)

        # Pagination
        total = len(results_with_stats)
        start = (page - 1) * limit
        end = start + limit
        paged = results_with_stats[start:end]

        return Response({
            "data": paged,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit,
                "hasNext": end < total,
                "hasPrev": start > 0
            }
        })


class CustomerDetailView(APIView):
    """GET /api/admin/customers/:id - Customer detail with order history"""
    @require_admin
    def get(self, request, customer_id):
        try:
            user = User.objects.get(id=ObjectId(customer_id), role="user")
        except (User.DoesNotExist, Exception):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Customer not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get customer orders
        orders = Order.objects(user=user).order_by('-created_at')
        total_orders = orders.count()
        
        # Calculate stats
        completed_orders = orders.filter(status='completed')
        total_spent = sum(order.total_price for order in completed_orders)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Get first and last order
        first_order = orders.order_by('created_at').first()
        last_order = orders.order_by('-created_at').first()
        
        # Calculate status
        is_vip = total_orders > 10
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_order = orders.filter(created_at__gte=thirty_days_ago).first()
        
        if user.blocked:
            customer_status = "blocked"
        elif is_vip:
            customer_status = "vip"
        elif recent_order:
            customer_status = "active"
        else:
            customer_status = "inactive"
        
        # Get recent orders (last 10)
        recent_orders_data = []
        for order in orders[:10]:
            recent_orders_data.append({
                "id": str(order.id),
                "orderNumber": order.order_number,
                "total": order.total_price,
                "status": order.status,
                "orderDate": order.created_at.isoformat()
            })
        
        # Get addresses
        from users.models import Address
        addresses = Address.objects(user=user)
        addresses_data = [
            {
                "id": str(addr.id),
                "receiver": addr.receiver,
                "detail": addr.detail,
                "ward": addr.ward,
                "district": addr.district,
                "province": addr.province,
                "phone": addr.phone,
                "is_default": addr.is_default
            }
            for addr in addresses
        ]
        
        return Response({
            "id": str(user.id),
            "name": user.displayName or user.username or user.email,
            "displayName": user.displayName,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "addresses": addresses_data,
            "totalOrders": total_orders,
            "totalSpent": total_spent,
            "averageOrderValue": avg_order_value,
            "lastOrder": last_order.created_at.isoformat() if last_order else None,
            "status": customer_status,
            "isVip": is_vip,
            "joinDate": user.created_at.isoformat(),
            "orders": recent_orders_data,
            "orderHistory": {
                "totalOrders": total_orders,
                "totalSpent": total_spent,
                "averageOrderValue": avg_order_value,
                "firstOrderDate": first_order.created_at.isoformat() if first_order else None,
                "lastOrderDate": last_order.created_at.isoformat() if last_order else None
            }
        })


class CustomerStatusUpdateView(APIView):
    """PATCH /api/admin/customers/:id/status - Update customer status (block/unblock)"""
    @require_admin
    def patch(self, request, customer_id):
        try:
            user = User.objects.get(id=ObjectId(customer_id), role="user")
        except (User.DoesNotExist, Exception):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Customer not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {"error": {"code": "MISSING_FIELD", "message": "Status is required"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only allow blocked status to be set manually
        if new_status == 'blocked':
            user.blocked = True
        elif new_status in ['active', 'inactive', 'vip']:
            # These are calculated, unblock user
            user.blocked = False
        else:
            return Response(
                {"error": {"code": "INVALID_STATUS", 
                          "message": "Invalid status. Only 'blocked' can be set manually"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.save()
        
        return Response({
            "id": str(user.id),
            "blocked": user.blocked,
            "message": "Customer status updated"
        })

