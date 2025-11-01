"""
Dashboard and Analytics views for Admin
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.auth import require_admin
from .models import Order
from users.models import User
from products.models import Product, ParentCategory, ChildCategory
from datetime import datetime, timedelta
from bson import ObjectId


class DashboardStatsView(APIView):
    """GET /api/admin/dashboard/stats - Dashboard statistics"""
    
    @require_admin
    def get(self, request):
        # Get period from query params
        period = request.query_params.get('period', 'month')
        
        # Calculate date range
        now = datetime.utcnow()
        if period == 'week':
            start_date = now - timedelta(days=7)
            prev_start = start_date - timedelta(days=7)
        elif period == 'year':
            start_date = now - timedelta(days=365)
            prev_start = start_date - timedelta(days=365)
        else:  # month (default)
            start_date = now - timedelta(days=30)
            prev_start = start_date - timedelta(days=30)
        
        # Current period orders
        current_orders = Order.objects(created_at__gte=start_date)
        completed_orders = current_orders.filter(status='completed')
        
        # Previous period orders (for comparison)
        prev_orders = Order.objects(created_at__gte=prev_start, created_at__lt=start_date)
        prev_completed_orders = prev_orders.filter(status='completed')
        
        # Calculate revenue
        total_revenue = sum(order.total_price for order in completed_orders)
        prev_revenue = sum(order.total_price for order in prev_completed_orders)
        revenue_change = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        # Calculate orders count
        total_orders = current_orders.count()
        prev_total_orders = prev_orders.count()
        orders_change = ((total_orders - prev_total_orders) / prev_total_orders * 100) if prev_total_orders > 0 else 0
        
        # Calculate customers
        total_customers = User.objects(role='user').count()
        # New customers in period
        new_customers = User.objects(role='user', created_at__gte=start_date).count()
        prev_new_customers = User.objects(role='user', created_at__gte=prev_start, created_at__lt=start_date).count()
        customers_change = ((new_customers - prev_new_customers) / prev_new_customers * 100) if prev_new_customers > 0 else 0
        
        # Calculate products
        total_products = Product.objects.count()
        new_products = Product.objects(created_at__gte=start_date).count()
        prev_new_products = Product.objects(created_at__gte=prev_start, created_at__lt=start_date).count()
        products_change = ((new_products - prev_new_products) / prev_new_products * 100) if prev_new_products > 0 else 0
        
        # Get recent orders
        recent_orders = Order.objects.all().order_by('-created_at')[:10]
        recent_orders_data = []
        for order in recent_orders:
            recent_orders_data.append({
                "id": str(order.id),
                "orderNumber": order.order_number,
                "customer": order.user.displayName or order.user.email if order.user else "Unknown",
                "product": order.items[0].product_name if order.items else "N/A",
                "amount": order.total_price,
                "status": order.status,
                "date": order.created_at.isoformat()
            })
        
        # Revenue chart data (by day for the period)
        revenue_chart = []
        days_in_period = 7 if period == 'week' else 30 if period == 'month' else 12
        
        for i in range(days_in_period):
            if period == 'year':
                # Monthly data for year
                month_start = now.replace(day=1) - timedelta(days=30 * i)
                month_end = month_start + timedelta(days=30)
                orders_in_period = Order.objects(
                    status='completed',
                    created_at__gte=month_start,
                    created_at__lt=month_end
                )
                period_revenue = sum(o.total_price for o in orders_in_period)
                revenue_chart.insert(0, {
                    "month": month_start.strftime("T%m"),
                    "revenue": period_revenue,
                    "orders": orders_in_period.count()
                })
            else:
                # Daily data for week/month
                day_start = now.replace(hour=0, minute=0, second=0) - timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                orders_in_day = Order.objects(
                    status='completed',
                    created_at__gte=day_start,
                    created_at__lt=day_end
                )
                day_revenue = sum(o.total_price for o in orders_in_day)
                revenue_chart.insert(0, {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "revenue": day_revenue,
                    "orders": orders_in_day.count()
                })
        
        # Category distribution
        category_distribution = []
        parent_categories = ParentCategory.objects.all()
        for parent in parent_categories:
            children = ChildCategory.objects(parent=parent)
            product_count = Product.objects(category__in=children).count()
            if product_count > 0:
                category_distribution.append({
                    "name": parent.name,
                    "value": product_count,
                    "count": product_count
                })
        
        return Response({
            "summary": {
                "totalRevenue": total_revenue,
                "revenueChange": round(revenue_change, 1),
                "totalOrders": total_orders,
                "ordersChange": round(orders_change, 1),
                "totalCustomers": total_customers,
                "customersChange": round(customers_change, 1),
                "totalProducts": total_products,
                "productsChange": round(products_change, 1)
            },
            "recentOrders": recent_orders_data,
            "revenueChart": revenue_chart[:12],  # Limit to 12 data points
            "categoryDistribution": category_distribution
        })


class AnalyticsView(APIView):
    """GET /api/admin/analytics - Detailed analytics"""
    
    @require_admin
    def get(self, request):
        # Get period from query params
        period = request.query_params.get('period', 'month')
        
        # Calculate date range
        now = datetime.utcnow()
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:  # month
            start_date = now - timedelta(days=30)
        
        # Get orders in period
        period_orders = Order.objects(created_at__gte=start_date)
        completed_orders = period_orders.filter(status='completed')
        
        # Calculate summary
        total_revenue = sum(order.total_price for order in completed_orders)
        total_orders = period_orders.count()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # New customers
        new_customers = User.objects(role='user', created_at__gte=start_date).count()
        
        # Top products
        product_sales = {}
        for order in completed_orders:
            for item in order.items:
                pid = str(item.product_id)
                if pid not in product_sales:
                    product_sales[pid] = {
                        "productId": pid,
                        "productName": item.product_name,
                        "sales": 0,
                        "revenue": 0
                    }
                product_sales[pid]["sales"] += item.quantity
                product_sales[pid]["revenue"] += item.total
        
        top_products = sorted(product_sales.values(), key=lambda x: x["revenue"], reverse=True)[:10]
        
        # Customer segments
        all_users = User.objects(role='user')
        vip_count = 0
        active_count = 0
        inactive_count = 0
        
        thirty_days_ago = now - timedelta(days=30)
        for user in all_users:
            user_orders = Order.objects(user=user).count()
            if user_orders > 10:
                vip_count += 1
            else:
                recent_order = Order.objects(user=user, created_at__gte=thirty_days_ago).first()
                if recent_order:
                    active_count += 1
                else:
                    inactive_count += 1
        
        total_users = all_users.count()
        
        return Response({
            "summary": {
                "totalRevenue": total_revenue,
                "totalOrders": total_orders,
                "newCustomers": new_customers,
                "averageOrderValue": round(avg_order_value, 0)
            },
            "topProducts": top_products,
            "customerSegments": [
                {
                    "segment": "new",
                    "name": "Khách mới",
                    "count": new_customers,
                    "percentage": round(new_customers / total_users * 100, 1) if total_users > 0 else 0
                },
                {
                    "segment": "regular",
                    "name": "Khách thường xuyên",
                    "count": active_count,
                    "percentage": round(active_count / total_users * 100, 1) if total_users > 0 else 0
                },
                {
                    "segment": "vip",
                    "name": "Khách VIP",
                    "count": vip_count,
                    "percentage": round(vip_count / total_users * 100, 1) if total_users > 0 else 0
                },
                {
                    "segment": "inactive",
                    "name": "Không hoạt động",
                    "count": inactive_count,
                    "percentage": round(inactive_count / total_users * 100, 1) if total_users > 0 else 0
                }
            ]
        })

