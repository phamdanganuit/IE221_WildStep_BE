from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Shoe Shop API",
      default_version='v1',
      description="""
# Shoe Shop API Documentation

API backend cho ứng dụng bán giày trực tuyến.

## Xác thực (Authentication)

Hầu hết các endpoint yêu cầu JWT token trong header:
```
Authorization: Bearer <your_jwt_token>
```

Để lấy token:
1. **Đăng ký**: POST `/api/register`
2. **Đăng nhập**: POST `/api/login`
3. Sử dụng token nhận được trong response

## Phân quyền (Authorization)

- **Public APIs**: Không yêu cầu xác thực
- **User APIs**: Yêu cầu JWT token của user
- **Admin APIs**: Yêu cầu JWT token của admin (role='admin')

## Các nhóm API chính

### 1. Authentication & User Management
- Đăng ký, đăng nhập (email/password, Google, Facebook)
- Quản lý profile, avatar
- Quản lý địa chỉ giao hàng

### 2. Products & Categories
- Danh sách sản phẩm, tìm kiếm, lọc
- Chi tiết sản phẩm
- Danh mục, thương hiệu

### 3. Cart & Checkout
- Giỏ hàng
- Voucher
- Đặt hàng

### 4. Orders & Reviews
- Lịch sử đơn hàng
- Đánh giá sản phẩm

### 5. Admin Management
- Quản lý sản phẩm, danh mục, thương hiệu
- Quản lý đơn hàng, khách hàng
- Quản lý voucher
- Dashboard & Analytics
      """,
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@shoeshop.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Swagger Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    path("admin/", admin.site.urls),
    path("api/", include("users.urls")),
    path("api/", include("products.public_urls")),
    path("api/", include("orders.urls")),
    
    # Admin APIs
    path("api/admin/", include("products.admin_urls")),
    path("api/admin/", include("orders.admin_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)