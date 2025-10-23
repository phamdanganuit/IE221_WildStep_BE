from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from email_validator import validate_email, EmailNotValidError
from mongoengine.errors import NotUniqueError
import os
from .models import User , Address
from .auth import hash_password, check_password, create_jwt, require_auth, require_admin


from orders.models import Cart, Wishlist
from notifications.models import Notification



ADMIN_SIGNUP_KEY = os.getenv("ADMIN_SIGNUP_KEY", "")


from rest_framework.views import APIView
from .social import oauth_google, oauth_facebook

class GoogleOAuthView(APIView):
    def post(self, request):
        return oauth_google(request)

class FacebookOAuthView(APIView):
    def post(self, request):
        return oauth_facebook(request)
# -------- Register --------
class RegisterView(APIView):
    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        
        # --- SỬA Ở ĐÂY ---
        # Lấy 'displayName' từ request thay vì 'full_name'
        display_name = request.data.get("displayName") or ""
        
        admin_key = request.data.get("admin_key")
        if not email or not password:
            return Response({"detail": "email and password are required"}, status=400)

        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return Response({"detail": "invalid email"}, status=400)

        if len(password) < 6:
            return Response({"detail": "password must be at least 6 characters"}, status=400)

        if User.objects(email=email).first():
            return Response({"detail": "Email already registered"}, status=409)
        
        role="user"
        if admin_key and ADMIN_SIGNUP_KEY and admin_key==ADMIN_SIGNUP_KEY:
            role="admin"
        
        try:
            # --- VÀ SỬA Ở ĐÂY ---
            # Tạo User với trường `displayName`
            user = User(
                email=email, 
                password_hash=hash_password(password), 
                displayName=display_name, # <-- Sửa từ full_name
                role=role
            ).save()
        except NotUniqueError:
            return Response({"detail": "Email already registered"}, status=409)

        # Hàm to_safe_dict không còn, trả về thông tin cơ bản
        return Response({
            "id": str(user.id),
            "email": user.email,
            "displayName": user.displayName,
            "role": user.role
        }, status=201)

# -------- Login --------
class LoginView(APIView):
    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""

        user = User.objects(email=email).first()
        if not user or not check_password(password, user.password_hash):
            return Response({"detail": "Invalid credentials"}, status=401)

        token = create_jwt({"sub": str(user.id), "email": user.email,"role": user.role})
        return Response({"access_token": token, "token_type": "Bearer"}, status=200)

# -------- Me --------
class MeView(APIView):
    @require_auth
    # @require_admin
    def get(self, request):
        return Response({"user": request.user_claims}, status=200)



# -------- Profile --------
class ProfileView(APIView):
    @require_auth
    def get(self, request):
        try:
            # Lấy user_id từ payload của token (đã được decorator @require_auth giải mã)
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # --- Bắt đầu các truy vấn phụ ---

        # Truy vấn 1: Đếm số lượng sản phẩm trong giỏ hàng
        cart = Cart.objects.filter(user=user).first()
        cart_count = len(cart.products) if cart else 0

        # Truy vấn 2: Đếm số lượng sản phẩm trong wishlist
        wishlist = Wishlist.objects.filter(user=user).first()
        wishlist_count = len(wishlist.product_ids) if wishlist else 0

        # Truy vấn 3: Đếm số thông báo chưa đọc
        notification_doc = Notification.objects.filter(user=user).first()
        if notification_doc:
            # Dùng generator expression để đếm cho hiệu quả
            unread_notification_count = sum(1 for notif in notification_doc.notifications if not notif.read)
        else:
            unread_notification_count = 0
        
        # --- Xây dựng đối tượng JSON để trả về ---
        response_data = {
            "_id": str(user.id),
            "username": user.username,
            "displayName": user.displayName,
            "email": user.email,
            "phone": user.phone,
            "sex": user.sex,
            "birth": user.birth.isoformat() if user.birth else None,
            "avatar": user.avatar,
            "role": user.role,

            # Kiểm tra sự tồn tại của provider trong danh sách
            "google": any(p.provider == 'google' for p in user.providers),
            "facebook": any(p.provider == 'facebook' for p in user.providers),
            # Lấy danh sách địa chỉ của user bằng cách query ngược
            "addresses": [str(addr.id) for addr in Address.objects(user=user)],
            "vouchers": [str(v_id) for v_id in user.vouchers],
            "createdAt": user.created_at.isoformat(),
            # --- Dữ liệu đếm được ---
            "cartCount": cart_count,
            "wishlistCount": wishlist_count,
            "notificationCount": unread_notification_count
        }

        return Response(response_data, status=status.HTTP_200_OK)