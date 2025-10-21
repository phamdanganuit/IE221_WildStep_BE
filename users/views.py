from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from email_validator import validate_email, EmailNotValidError
from mongoengine.errors import NotUniqueError
import os
from .models import User
from .auth import hash_password, check_password, create_jwt, require_auth, require_admin
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
        full_name = request.data.get("full_name") or ""
        admin_key= request.data.get("admin_key")
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
            user = User(email=email, password_hash=hash_password(password), full_name=full_name, role=role).save()
        except NotUniqueError:
            return Response({"detail": "Email already registered"}, status=409)

        return Response(user.to_safe_dict(), status=201)

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
