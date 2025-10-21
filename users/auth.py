import os, time, bcrypt, jwt
from functools import wraps
from rest_framework.response import Response
from rest_framework import status

JWT_SECRET = os.getenv("JWT_SECRET", "dev")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_jwt(payload: dict) -> str:
    now = int(time.time())
    exp = now + JWT_EXPIRES_MIN * 60
    return jwt.encode({"iat": now, "exp": exp, **payload}, JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

def require_auth(view_func):
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response({"detail": "Missing Bearer token"}, status=status.HTTP_401_UNAUTHORIZED)
        token = auth_header.split(" ", 1)[1].strip()
        try:
            claims = decode_jwt(token)
            request.user_claims = claims
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
        return view_func(self, request, *args, **kwargs)
    return _wrapped
def require_admin(view_func):
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        # require_auth phải chạy trước để gắn request.user_claims
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response({"detail":"Missing Bearer token"}, status=401)
        token = auth_header.split(" ", 1)[1].strip()
        try:
            claims = decode_jwt(token)
            request.user_claims = claims
        except jwt.ExpiredSignatureError:
            return Response({"detail":"Token expired"}, status=401)
        except Exception:
            return Response({"detail":"Invalid token"}, status=401)

        # lấy user và kiểm tra role
        from .models import User
        from bson import ObjectId
        user = User.objects(id=ObjectId(claims["sub"])).first()
        if not user or user.role != "admin":
            return Response({"detail":"Admin only"}, status=403)

        request.user = user
        return view_func(self, request, *args, **kwargs)
    return _wrapped
