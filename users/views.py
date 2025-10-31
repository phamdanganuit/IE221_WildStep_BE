from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from email_validator import validate_email, EmailNotValidError
from mongoengine.errors import NotUniqueError, ValidationError as MEValidationError
from datetime import datetime
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

    @require_auth
    def delete(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        password = request.data.get('password')
        if user.password_hash and password:
            if not check_password(password, user.password_hash):
                return Response({"detail": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



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

    @require_auth
    def put(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if 'displayName' in request.data:
            user.displayName = request.data['displayName']
        if 'phone' in request.data:
            user.phone = request.data['phone']
        if 'sex' in request.data:
            sex_value = request.data['sex']
            if sex_value not in ['male', 'female', 'other', None, '']:
                return Response({"detail": "Invalid sex value. Must be 'male', 'female', or 'other'"}, status=status.HTTP_400_BAD_REQUEST)
            user.sex = sex_value
        if 'birth' in request.data:
            birth_str = request.data['birth']
            if birth_str:
                try:
                    user.birth = datetime.fromisoformat(birth_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return Response({"detail": "Invalid birth date format. Use ISO 8601 format"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                user.birth = None

        user.save()

        return Response({
            "id": str(user.id),
            "email": user.email,
            "displayName": user.displayName,
            "phone": user.phone,
            "sex": user.sex,
            "birth": user.birth.isoformat() if user.birth else None,
            "avatar": user.avatar
        }, status=status.HTTP_200_OK)


# -------- Update Profile --------
class UpdateProfileView(APIView):
    @require_auth
    def put(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Cập nhật các trường tùy chọn
        if 'displayName' in request.data:
            user.displayName = request.data['displayName']
        
        if 'phone' in request.data:
            user.phone = request.data['phone']
        
        if 'sex' in request.data:
            sex_value = request.data['sex']
            if sex_value not in ['male', 'female', 'other', None, '']:
                return Response({"detail": "Invalid sex value. Must be 'male', 'female', or 'other'"}, 
                              status=status.HTTP_400_BAD_REQUEST)
            user.sex = sex_value
        
        if 'birth' in request.data:
            birth_str = request.data['birth']
            if birth_str:
                try:
                    # Parse ISO format datetime
                    user.birth = datetime.fromisoformat(birth_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return Response({"detail": "Invalid birth date format. Use ISO 8601 format"}, 
                                  status=status.HTTP_400_BAD_REQUEST)
            else:
                user.birth = None

        user.save()

        # Trả về thông tin đã cập nhật
        return Response({
            "id": str(user.id),
            "email": user.email,
            "displayName": user.displayName,
            "phone": user.phone,
            "sex": user.sex,
            "birth": user.birth.isoformat() if user.birth else None,
            "avatar": user.avatar
        }, status=status.HTTP_200_OK)


# -------- Update Avatar --------
class UpdateAvatarView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    
    @require_auth
    def put(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra định dạng file
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if file_obj.content_type not in allowed_types:
            return Response({"detail": "Invalid file type. Only JPEG and PNG are allowed"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra kích thước file (≤ 1MB)
        if file_obj.size > 1 * 1024 * 1024:  # 1MB
            return Response({"detail": "File too large. Maximum size is 1MB"}, 
                          status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Tạo tên file unique
        import uuid
        ext = file_obj.name.split('.')[-1] if '.' in file_obj.name else 'jpg'
        filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        # Lưu file (tạm thời lưu local, sau này có thể upload lên cloud storage)
        upload_dir = os.path.join('media', 'avatars')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
        
        # Cập nhật URL avatar trong database
        avatar_url = f"/media/avatars/{filename}"  # URL tương đối
        user.avatar = avatar_url
        user.save()

        return Response({"avatarUrl": avatar_url}, status=status.HTTP_200_OK)


# -------- Delete Account --------
class DeleteAccountView(APIView):
    @require_auth
    def delete(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra mật khẩu nếu được cung cấp (cho user có password)
        password = request.data.get('password')
        if user.password_hash and password:
            if not check_password(password, user.password_hash):
                return Response({"detail": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)

        # Xóa user (cascade sẽ tự động xóa các related documents)
        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# -------- Change Password --------
class ChangePasswordView(APIView):
    @require_auth
    def post(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        old_password = request.data.get('oldPassword')
        new_password = request.data.get('newPassword')

        if not old_password or not new_password:
            return Response({"detail": "oldPassword and newPassword are required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra user có password hay không (có thể là OAuth-only user)
        if not user.password_hash:
            return Response({"detail": "This account does not have a password. Please use social login."}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra mật khẩu cũ
        if not check_password(old_password, user.password_hash):
            return Response({"detail": "Old password is incorrect"}, 
                          status=status.HTTP_401_UNAUTHORIZED)

        # Validate mật khẩu mới
        if len(new_password) < 6:
            return Response({"detail": "New password must be at least 6 characters"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Cập nhật mật khẩu
        user.password_hash = hash_password(new_password)
        user.save()

        return Response({"message": "Password changed"}, status=status.HTTP_200_OK)


# -------- Address CRUD --------
class AddressListView(APIView):
    @require_auth
    def get(self, request):
        """Lấy danh sách địa chỉ của user"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        addresses = Address.objects(user=user).order_by('-is_default', '-created_at')
        
        result = []
        for addr in addresses:
            result.append({
                "id": str(addr.id),
                "receiver": addr.receiver,
                "detail": addr.detail,
                "ward": addr.ward,
                "district": addr.district,
                "province": addr.province,
                "phone": addr.phone,
                "is_default": addr.is_default,
                "createdAt": addr.created_at.isoformat()
            })

        return Response(result, status=status.HTTP_200_OK)

    @require_auth
    def post(self, request):
        """Thêm địa chỉ mới"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Validate required fields
        required_fields = ['receiver', 'detail', 'ward', 'district', 'province', 'phone']
        for field in required_fields:
            if not request.data.get(field):
                return Response({"detail": f"{field} is required"}, 
                              status=status.HTTP_400_BAD_REQUEST)

        is_default = request.data.get('is_default', False)
        
        # Nếu đặt làm mặc định, bỏ default của các địa chỉ khác
        if is_default:
            Address.objects(user=user, is_default=True).update(is_default=False)

        # Tạo địa chỉ mới
        address = Address(
            user=user,
            receiver=request.data['receiver'],
            detail=request.data['detail'],
            ward=request.data['ward'],
            district=request.data['district'],
            province=request.data['province'],
            phone=request.data['phone'],
            is_default=is_default
        ).save()

        return Response({
            "id": str(address.id),
            "receiver": address.receiver,
            "detail": address.detail,
            "ward": address.ward,
            "district": address.district,
            "province": address.province,
            "phone": address.phone,
            "is_default": address.is_default,
            "createdAt": address.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)


class AddressDetailView(APIView):
    @require_auth
    def put(self, request, address_id):
        """Cập nhật địa chỉ"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
            address = Address.objects.get(id=address_id, user=user)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except MEValidationError:
            return Response({"detail": "Invalid address id"}, status=status.HTTP_400_BAD_REQUEST)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        # Cập nhật các trường
        if 'receiver' in request.data:
            address.receiver = request.data['receiver']
        if 'detail' in request.data:
            address.detail = request.data['detail']
        if 'ward' in request.data:
            address.ward = request.data['ward']
        if 'district' in request.data:
            address.district = request.data['district']
        if 'province' in request.data:
            address.province = request.data['province']
        if 'phone' in request.data:
            address.phone = request.data['phone']
        if 'is_default' in request.data:
            is_default = request.data['is_default']
            if is_default:
                # Bỏ default của các địa chỉ khác
                Address.objects(user=user, is_default=True).update(is_default=False)
            address.is_default = is_default

        address.save()

        return Response({
            "id": str(address.id),
            "receiver": address.receiver,
            "detail": address.detail,
            "ward": address.ward,
            "district": address.district,
            "province": address.province,
            "phone": address.phone,
            "is_default": address.is_default,
            "createdAt": address.created_at.isoformat()
        }, status=status.HTTP_200_OK)

    @require_auth
    def delete(self, request, address_id):
        """Xóa địa chỉ"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
            address = Address.objects.get(id=address_id, user=user)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except MEValidationError:
            return Response({"detail": "Invalid address id"}, status=status.HTTP_400_BAD_REQUEST)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddressSetDefaultView(APIView):
    @require_auth
    def patch(self, request, address_id):
        """Thiết lập địa chỉ mặc định"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
            address = Address.objects.get(id=address_id, user=user)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except MEValidationError:
            return Response({"detail": "Invalid address id"}, status=status.HTTP_400_BAD_REQUEST)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        # Bỏ default của tất cả địa chỉ khác
        Address.objects(user=user, is_default=True).update(is_default=False)
        
        # Set địa chỉ này làm default
        address.is_default = True
        address.save()

        return Response({
            "id": str(address.id),
            "is_default": True
        }, status=status.HTTP_200_OK)


# -------- Social Links --------
class SocialLinksView(APIView):
    @require_auth
    def get(self, request):
        """Lấy trạng thái liên kết MXH"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra provider nào đã được link
        google_linked = any(p.provider == 'google' for p in user.providers)
        facebook_linked = any(p.provider == 'facebook' for p in user.providers)

        return Response({
            "google": google_linked,
            "facebook": facebook_linked
        }, status=status.HTTP_200_OK)


class LinkGoogleView(APIView):
    @require_auth
    def post(self, request):
        """Liên kết tài khoản Google"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        access_token = request.data.get('access_token')
        id_token = request.data.get('id_token')
        
        if not access_token and not id_token:
            return Response({"detail": "access_token or id_token is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            import requests
            # Verify token bằng Google API
            if access_token:
                userinfo_response = requests.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    params={"access_token": access_token},
                    timeout=10
                )
            else:
                # Verify id_token
                userinfo_response = requests.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
                    timeout=10
                )
            
            if userinfo_response.status_code != 200:
                return Response({"detail": "Invalid Google token"}, 
                              status=status.HTTP_401_UNAUTHORIZED)
            
            user_data = userinfo_response.json()
            google_id = user_data.get("id") or user_data.get("sub")
            
            if not google_id:
                return Response({"detail": "Cannot fetch Google user ID"}, 
                              status=status.HTTP_400_BAD_REQUEST)
                
        except Exception:
            return Response({"detail": "Invalid Google token"}, 
                          status=status.HTTP_401_UNAUTHORIZED)

        # Kiểm tra xem đã link chưa
        already_linked = any(p.provider == 'google' and p.provider_user_id == google_id 
                           for p in user.providers)
        
        if not already_linked:
            from .models import ProviderLink
            user.providers.append(ProviderLink(provider="google", provider_user_id=google_id))
            user.save()

        return Response({"google": True}, status=status.HTTP_200_OK)

    @require_auth
    def delete(self, request):
        """Hủy liên kết tài khoản Google"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Xóa provider Google
        user.providers = [p for p in user.providers if p.provider != 'google']
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class LinkFacebookView(APIView):
    @require_auth
    def post(self, request):
        """Liên kết tài khoản Facebook"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        access_token = request.data.get('access_token')
        
        if not access_token:
            return Response({"detail": "access_token is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            import requests
            # Verify token
            FB_APP_ID = os.getenv("FB_APP_ID", "") or os.getenv("FACEBOOK_APP_ID", "")
            FB_APP_SECRET = os.getenv("FB_APP_SECRET", "") or os.getenv("FACEBOOK_APP_SECRET", "")
            
            app_token = f"{FB_APP_ID}|{FB_APP_SECRET}"
            dbg = requests.get(
                "https://graph.facebook.com/debug_token",
                params={"input_token": access_token, "access_token": app_token},
                timeout=10
            ).json()
            
            if not dbg.get("data", {}).get("is_valid"):
                return Response({"detail": "Invalid Facebook token"}, 
                              status=status.HTTP_401_UNAUTHORIZED)

            # Lấy profile
            me = requests.get(
                "https://graph.facebook.com/me",
                params={"fields": "id", "access_token": access_token},
                timeout=10
            ).json()

            fb_id = me.get("id")
            if not fb_id:
                return Response({"detail": "Cannot fetch Facebook profile"}, 
                              status=status.HTTP_400_BAD_REQUEST)
                
        except Exception:
            return Response({"detail": "Invalid Facebook token"}, 
                          status=status.HTTP_401_UNAUTHORIZED)

        # Kiểm tra xem đã link chưa
        already_linked = any(p.provider == 'facebook' and p.provider_user_id == fb_id 
                           for p in user.providers)
        
        if not already_linked:
            from .models import ProviderLink
            user.providers.append(ProviderLink(provider="facebook", provider_user_id=fb_id))
            user.save()

        return Response({"facebook": True}, status=status.HTTP_200_OK)

    @require_auth
    def delete(self, request):
        """Hủy liên kết tài khoản Facebook"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Xóa provider Facebook
        user.providers = [p for p in user.providers if p.provider != 'facebook']
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


# -------- Notification Settings --------
class NotificationSettingsView(APIView):
    @require_auth
    def get(self, request):
        """Lấy cài đặt thông báo"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "emailNotif": user.emailNotif,
            "emailUpdate": user.emailUpdate,
            "emailSale": user.emailSale,
            "emailSurvey": user.emailSurvey,
            "smsNotif": user.smsNotif,
            "smsSale": user.smsSale
        }, status=status.HTTP_200_OK)

    @require_auth
    def put(self, request):
        """Cập nhật cài đặt thông báo"""
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Cập nhật các trường boolean nếu có trong request
        boolean_fields = ['emailNotif', 'emailUpdate', 'emailSale', 'emailSurvey', 'smsNotif', 'smsSale']
        
        for field in boolean_fields:
            if field in request.data:
                value = request.data[field]
                if not isinstance(value, bool):
                    return Response({"detail": f"{field} must be a boolean"}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                setattr(user, field, value)

        user.save()

        return Response({
            "emailNotif": user.emailNotif,
            "emailUpdate": user.emailUpdate,
            "emailSale": user.emailSale,
            "emailSurvey": user.emailSurvey,
            "smsNotif": user.smsNotif,
            "smsSale": user.smsSale
        }, status=status.HTTP_200_OK)