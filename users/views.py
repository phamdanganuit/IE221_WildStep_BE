from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from email_validator import validate_email, EmailNotValidError
from mongoengine.errors import NotUniqueError, ValidationError as MEValidationError
from datetime import datetime
import os
from django.core.files.storage import default_storage
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
            user = User(
                email=email, 
                password_hash=hash_password(password), 
                displayName=display_name,
                role=role
            ).save()
        except NotUniqueError:
            return Response({"detail": "Email already registered"}, status=409)

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
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        cart = Cart.objects.filter(user=user).first()
        cart_count = len(cart.products) if cart else 0

        wishlist = Wishlist.objects.filter(user=user).first()
        wishlist_count = len(wishlist.product_ids) if wishlist else 0

        notification_doc = Notification.objects.filter(user=user).first()
        if notification_doc:
            unread_notification_count = sum(1 for notif in notification_doc.notifications if not notif.read)
        else:
            unread_notification_count = 0
        
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
            "google": any(p.provider == 'google' for p in user.providers),
            "facebook": any(p.provider == 'facebook' for p in user.providers),
            "addresses": [str(addr.id) for addr in Address.objects(user=user)],
            "vouchers": [str(v_id) for v_id in user.vouchers],
            "createdAt": user.created_at.isoformat(),
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

        if 'displayName' in request.data:
            user.displayName = request.data['displayName']
        if 'email' in request.data:
            user.email = request.data['email']
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
                    user.birth = datetime.fromisoformat(birth_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return Response({"detail": "Invalid birth date format. Use ISO 8601 format"}, 
                                  status=status.HTTP_400_BAD_REQUEST)
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

        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if file_obj.content_type not in allowed_types:
            return Response({"detail": "Invalid file type. Only JPEG and PNG are allowed"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        if file_obj.size > 1 * 1024 * 1024:
            return Response({"detail": "File too large. Maximum size is 1MB"}, 
                          status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        if user.avatar:
            try:
                old_path = user.avatar
                if old_path.startswith('/media/'):
                    old_path = old_path.replace('/media/', '')
                elif old_path.startswith('https://'):
                    from urllib.parse import urlparse
                    from django.conf import settings
                    parsed = urlparse(old_path)
                    container = getattr(settings, 'AZURE_STORAGE_CONTAINER', 'media')
                    old_path = parsed.path.lstrip('/').replace(f'{container}/', '')
                
                if default_storage.exists(old_path):
                    default_storage.delete(old_path)
            except Exception:
                pass

        import uuid
        ext = file_obj.name.split('.')[-1] if '.' in file_obj.name else 'jpg'
        filename = f"avatars/avatar_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        from django.conf import settings
        import logging
        logger = logging.getLogger(__name__)
        
        azure_conn = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', '') or os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
        azure_account = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', '') or os.getenv('AZURE_STORAGE_ACCOUNT_NAME', '')
        
        if azure_conn and azure_account:
            from storages.backends.azure_storage import AzureStorage
            storage = AzureStorage()
        else:
            storage = default_storage
        
        try:
            saved_path = storage.save(filename, file_obj)
            if not saved_path:
                return Response({"detail": "Failed to save file"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to save file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            azure_conn = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', '')
            if azure_conn:
                account_name = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', '')
                container = getattr(settings, 'AZURE_STORAGE_CONTAINER', 'media')
                
                blob_path = saved_path
                if blob_path.startswith(container + '/'):
                    blob_path = blob_path[len(container) + 1:]
                elif blob_path.startswith('/' + container + '/'):
                    blob_path = blob_path[len('/' + container) + 1:]
                
                avatar_url = f"https://{account_name}.blob.core.windows.net/{container}/{blob_path}"
                
                if azure_conn and azure_account:
                    try:
                        storage_url = storage.url(saved_path)
                        if storage_url and storage_url.startswith('http'):
                            avatar_url = storage_url
                    except Exception:
                        pass
            else:
                avatar_url = default_storage.url(saved_path)
                if not avatar_url.startswith('http') and not avatar_url.startswith('/media/'):
                    avatar_url = f"/media/{avatar_url}"
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get URL: {str(e)}")
            # Fallback
            azure_conn = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', '')
            if azure_conn:
                account_name = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', '')
                container = getattr(settings, 'AZURE_STORAGE_CONTAINER', 'media')
                blob_path = saved_path
                if blob_path.startswith(container + '/'):
                    blob_path = blob_path[len(container) + 1:]
                avatar_url = f"https://{account_name}.blob.core.windows.net/{container}/{blob_path}"
            else:
                avatar_url = f"/media/{saved_path}"
        
        user.avatar = avatar_url
        user.save()

        return Response({"avatarUrl": avatar_url}, status=status.HTTP_200_OK)


class DeleteAccountView(APIView):
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

        if not user.password_hash:
            return Response({"detail": "This account does not have a password. Please use social login."}, 
                          status=status.HTTP_400_BAD_REQUEST)

        if not check_password(old_password, user.password_hash):
            return Response({"detail": "Old password is incorrect"}, 
                          status=status.HTTP_401_UNAUTHORIZED)

        if len(new_password) < 6:
            return Response({"detail": "New password must be at least 6 characters"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        user.password_hash = hash_password(new_password)
        user.save()

        return Response({"message": "Password changed"}, status=status.HTTP_200_OK)


# -------- Address CRUD --------
class AddressListView(APIView):
    @require_auth
    def get(self, request):
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
        
        if is_default:
            Address.objects(user=user, is_default=True).update(is_default=False)

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

        Address.objects(user=user, is_default=True).update(is_default=False)
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
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        google_linked = any(p.provider == 'google' for p in user.providers)
        facebook_linked = any(p.provider == 'facebook' for p in user.providers)

        return Response({
            "google": google_linked,
            "facebook": facebook_linked
        }, status=status.HTTP_200_OK)


class LinkGoogleView(APIView):
    @require_auth
    def post(self, request):
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
            if access_token:
                userinfo_response = requests.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    params={"access_token": access_token},
                    timeout=10
                )
            else:
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

        already_linked = any(p.provider == 'google' and p.provider_user_id == google_id 
                           for p in user.providers)
        
        if not already_linked:
            from .models import ProviderLink
            user.providers.append(ProviderLink(provider="google", provider_user_id=google_id))
            user.save()

        return Response({"google": True}, status=status.HTTP_200_OK)

    @require_auth
    def delete(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.providers = [p for p in user.providers if p.provider != 'google']
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class LinkFacebookView(APIView):
    @require_auth
    def post(self, request):
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

        already_linked = any(p.provider == 'facebook' and p.provider_user_id == fb_id 
                           for p in user.providers)
        
        if not already_linked:
            from .models import ProviderLink
            user.providers.append(ProviderLink(provider="facebook", provider_user_id=fb_id))
            user.save()

        return Response({"facebook": True}, status=status.HTTP_200_OK)

    @require_auth
    def delete(self, request):
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.providers = [p for p in user.providers if p.provider != 'facebook']
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


# -------- Notification Settings --------
class NotificationSettingsView(APIView):
    @require_auth
    def get(self, request):
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
        try:
            user_id = request.user_claims['sub']
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

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