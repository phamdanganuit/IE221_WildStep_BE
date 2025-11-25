from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
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