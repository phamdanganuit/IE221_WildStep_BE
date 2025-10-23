# users/models.py

import mongoengine as me
from datetime import datetime

# --- Model Address ---
# Vì Address liên quan chặt chẽ đến User, việc đặt nó ở đây là hợp lý.
class Address(me.Document):
    # Tham chiếu ngược về User sở hữu địa chỉ này
    user = me.ReferenceField('User', required=True, reverse_delete_rule=me.CASCADE)
    
    # Thông tin địa chỉ theo thiết kế DB của bạn
    receiver = me.StringField(required=True)
    phone = me.StringField(required=True)
    detail = me.StringField(required=True)
    ward = me.StringField(required=True)
    district = me.StringField(required=True)
    province = me.StringField(required=True)
    is_default = me.BooleanField(default=False) # Đổi 'default' -> 'is_default' vì 'default' là từ khóa
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "addresses"}


# --- ProviderLink không đổi ---
class ProviderLink(me.EmbeddedDocument):
    provider = me.StringField(required=True, choices=["google", "facebook"])
    provider_user_id = me.StringField(required=True)


# --- Model User được cập nhật ---
class User(me.Document):
    # --- Thông tin đăng nhập ---
    email = me.StringField(required=False, unique=True, sparse=True)
    password_hash = me.StringField(required=False)
    providers = me.EmbeddedDocumentListField(ProviderLink, default=list)
    role = me.StringField(choices=["user", "admin"], default="user")

    # --- Thông tin cá nhân (theo thiết kế DB mới) ---
    username = me.StringField()
    displayName = me.StringField() # Thay thế cho 'full_name'
    phone = me.StringField()
    sex = me.StringField(choices=["male", "female", "other"])
    birth = me.DateTimeField()
    avatar = me.StringField() # URL tới ảnh avatar

    # --- Tham chiếu đến các collection khác ---
    # MongoEngine sẽ tự động quản lý tham chiếu ngược từ Address.
    # Trường này không thực sự cần thiết nếu bạn luôn query từ Address -> User.
    # Tuy nhiên, để nó ở đây có thể tiện cho một số trường hợp.
    # addresses = me.ListField(me.ReferenceField(Address, reverse_delete_rule=me.PULL))
    
    # Tạm thời lưu voucher IDs, sau này sẽ tạo app promotions và dùng ReferenceField
    vouchers = me.ListField(me.ObjectIdField())

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
    
    # Chúng ta sẽ không dùng to_safe_dict() nữa, vì ProfileView sẽ xây dựng response
    # một cách tường minh và an toàn hơn.