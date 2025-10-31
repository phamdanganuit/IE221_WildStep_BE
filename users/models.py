# users/models.py (SẮP XẾP LẠI THỨ TỰ)

import mongoengine as me
from datetime import datetime

# ĐỊNH NGHĨA CÁC CLASS KHÔNG PHỤ THUỘC TRƯỚC
class ProviderLink(me.EmbeddedDocument):
    provider = me.StringField(required=True, choices=["google", "facebook", "line"])
    provider_user_id = me.StringField(required=True)


# BÂY GIỜ ĐỊNH NGHĨA USER, VÌ ADDRESS SẼ CẦN NÓ
class User(me.Document):
    # --- Thông tin đăng nhập ---
    email = me.StringField(required=False, unique=True, sparse=True)
    password_hash = me.StringField(required=False)
    providers = me.EmbeddedDocumentListField(ProviderLink, default=list)
    role = me.StringField(choices=["user", "admin"], default="user")

    # --- Thông tin cá nhân (theo thiết kế DB mới) ---
    username = me.StringField()
    displayName = me.StringField()
    phone = me.StringField()
    sex = me.StringField(choices=["male", "female", "other"])
    birth = me.DateTimeField()
    avatar = me.StringField()

    # --- Tham chiếu đến các collection khác ---
    vouchers = me.ListField(me.ObjectIdField())

    # --- Notification settings ---
    emailNotif = me.BooleanField(default=True)
    emailUpdate = me.BooleanField(default=True)
    emailSale = me.BooleanField(default=True)
    emailSurvey = me.BooleanField(default=True)
    smsNotif = me.BooleanField(default=False)
    smsSale = me.BooleanField(default=False)

    # --- Metadata ---
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "users",
        "indexes": [
            "email",
            "username",
            {"fields": ["providers.provider", "providers.provider_user_id"]},
        ]
    }


# CUỐI CÙNG, ĐỊNH NGHĨA ADDRESS, VÌ NÓ THAM CHIẾU ĐẾN USER ĐÃ TỒN TẠI Ở TRÊN
class Address(me.Document):
    user = me.ReferenceField(User, required=True, reverse_delete_rule=me.CASCADE)
    
    receiver = me.StringField(required=True)
    phone = me.StringField(required=True)
    detail = me.StringField(required=True)
    ward = me.StringField(required=True)
    district = me.StringField(required=True)
    province = me.StringField(required=True)
    is_default = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "addresses"}