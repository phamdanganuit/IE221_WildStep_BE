import logging
from bson import ObjectId
from bson.errors import InvalidId
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from .auth import decode_jwt
from .models import User

logger = logging.getLogger(__name__)


class JWTAuthentication(BaseAuthentication):
    """
    Simple JWT authentication that reads Authorization: Bearer <token>
    and attaches both the authenticated user and decoded claims.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith(f"{self.keyword} "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            raise exceptions.AuthenticationFailed("Missing Bearer token")

        try:
            claims = decode_jwt(token)
        except Exception as exc:
            logger.debug("Failed to decode JWT: %s", exc, exc_info=True)
            raise exceptions.AuthenticationFailed("Invalid or expired token")

        user_id = claims.get("sub")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token payload missing subject")

        try:
            user_obj = User.objects(id=ObjectId(user_id)).first()
        except (InvalidId, Exception) as exc:
            logger.debug("Invalid user id in token: %s", exc, exc_info=True)
            raise exceptions.AuthenticationFailed("Invalid user")

        if not user_obj:
            raise exceptions.AuthenticationFailed("User not found")

        request.user_claims = claims
        return (user_obj, token)

