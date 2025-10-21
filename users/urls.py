# users/urls.py (File mới)

from django.urls import path
# Giả sử các view của bạn nằm trong users/views.py
from .views import RegisterView, LoginView, MeView 

urlpatterns = [
    # Lưu ý: Tiền tố 'api/' đã được xử lý ở file urls chính
    # nên ở đây chúng ta chỉ cần định nghĩa phần còn lại.
    path("register", RegisterView.as_view(), name="register"),
    path("login",    LoginView.as_view(), name="login"),
    path("me",       MeView.as_view(), name="me"),
]