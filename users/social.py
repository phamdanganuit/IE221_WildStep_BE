# api/social.py
import os
import requests
from rest_framework.response import Response
from rest_framework import status

from .models import User, ProviderLink
from .auth import create_jwt

# --------- GOOGLE ----------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

def oauth_google(request):
    """
    Body FE: { "access_token": "<GOOGLE_ACCESS_TOKEN>" }
    """
    access_token = request.data.get("access_token")
    if not access_token:
        return Response({"detail": "access_token is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Verify access_token bằng cách gọi Google API
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            params={"access_token": access_token},
            timeout=10
        )
        
        if userinfo_response.status_code != 200:
            return Response({"detail": "Invalid Google access token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user_data = userinfo_response.json()
        
        # Lấy thông tin từ Google API response
        google_id = user_data.get("id")
        email = (user_data.get("email") or "").strip().lower()
        name = user_data.get("name") or ""
        
        if not google_id:
            return Response({"detail": "Cannot fetch Google user ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({"detail": "Invalid Google access token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Tìm theo provider trước
    user = User.objects(providers__match={"provider": "google", "provider_user_id": google_id}).first()

    # Nếu chưa có, link theo email (tránh tạo user trùng)
    if not user and email:
        user = User.objects(email=email).first()
        if user:
            user.providers.append(ProviderLink(provider="google", provider_user_id=google_id))
            user.save()

    # Nếu vẫn chưa có → tạo mới
    if not user:
        user = User(
            email=email or None,
            displayName=name,
            providers=[ProviderLink(provider="google", provider_user_id=google_id)]
        ).save()

    token = create_jwt({"sub": str(user.id), "email": user.email, "role": user.role})
    return Response({"access_token": token, "token_type": "Bearer"}, status=status.HTTP_200_OK)


# --------- FACEBOOK ----------
FB_APP_ID = os.getenv("FB_APP_ID", "") or os.getenv("FACEBOOK_APP_ID", "")
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "") or os.getenv("FACEBOOK_APP_SECRET", "")

def oauth_facebook(request):
    """
    Body FE: { "access_token": "<FB_USER_ACCESS_TOKEN>" }
    """
    user_token = request.data.get("access_token")
    if not user_token:
        return Response({"detail": "access_token is required"}, status=status.HTTP_400_BAD_REQUEST)

    # 1) Verify /debug_token
    app_token = f"{FB_APP_ID}|{FB_APP_SECRET}"
    dbg = requests.get(
        "https://graph.facebook.com/debug_token",
        params={"input_token": user_token, "access_token": app_token},
        timeout=10
    ).json()
    if not dbg.get("data", {}).get("is_valid"):
        return Response({"detail": "Invalid Facebook token"}, status=status.HTTP_401_UNAUTHORIZED)

    # 2) Lấy profile
    me = requests.get(
        "https://graph.facebook.com/me",
        params={"fields": "id,name,email", "access_token": user_token},
        timeout=10
    ).json()

    fb_id = me.get("id")
    if not fb_id:
        return Response({"detail": "Cannot fetch Facebook profile"}, status=status.HTTP_400_BAD_REQUEST)

    email = (me.get("email") or "").strip().lower()
    name = me.get("name") or ""

    # 3) Tìm theo provider
    user = User.objects(providers__match={"provider": "facebook", "provider_user_id": fb_id}).first()

    # 4) Link theo email nếu có
    if not user and email:
        user = User.objects(email=email).first()
        if user:
            user.providers.append(ProviderLink(provider="facebook", provider_user_id=fb_id))
            user.save()

    # 5) Tạo mới nếu vẫn chưa có
    if not user:
        user = User(
            email=email or None,
            displayName=name,
            providers=[ProviderLink(provider="facebook", provider_user_id=fb_id)]
        ).save()

    # 6) Trả JWT
    token = create_jwt({"sub": str(user.id), "email": user.email, "role": user.role})
    return Response({"access_token": token, "token_type": "Bearer"}, status=status.HTTP_200_OK)