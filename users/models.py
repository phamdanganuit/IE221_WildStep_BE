
import mongoengine as me
from datetime import datetime

class ProviderLink(me.EmbeddedDocument):
    provider = me.StringField(required=True, choices=["google", "facebook"])
    provider_user_id = me.StringField(required=True)  # Google: sub | Facebook: id

class User(me.Document):
    # Cho phép None (một số tài khoản FB không có email); unique+sparse để không đụng nhau
    email = me.StringField(required=False, unique=True, sparse=True)
    password_hash = me.StringField(required=False)  # social login có thể không có mật khẩu
    full_name = me.StringField()
    role = me.StringField(choices=["user", "admin"], default="user")

    # Danh sách liên kết social
    providers = me.EmbeddedDocumentListField(ProviderLink, default=list)

    # Thông tin bổ sung
    phone = me.StringField()
    address = me.StringField()
    gender = me.StringField(choices=["male", "female", "other"])
    birthday = me.DateTimeField()
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "users",
        "indexes": [
            "email",
            {"fields": ["providers.provider", "providers.provider_user_id"]},
        ]
    }

    def to_safe_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "providers": [
                {"provider": p.provider, "provider_user_id": p.provider_user_id}
                for p in self.providers
            ],
            "phone": self.phone,
            "address": self.address,
            "gender": self.gender,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
