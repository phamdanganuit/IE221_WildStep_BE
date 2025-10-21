import mongoengine as me
from datetime import datetime

class User(me.Document):
    """
    User model cho MongoDB dùng mongoengine
    """
    # Thông tin cơ bản
    email = me.StringField(required=True, unique=True)           # Email duy nhất
    password_hash = me.StringField(required=True)                # Mật khẩu đã băm (bcrypt)
    full_name = me.StringField()                                 # Họ tên đầy đủ
    role = me.StringField(choices=["user", "admin"], default="user")                          # Vai trò: user, admin
    # Thông tin bổ sung
    phone = me.StringField()                                     # Số điện thoại
    address = me.StringField()                                   # Địa chỉ
    gender = me.StringField(choices=["male", "female", "other"]) # Giới tính
    birthday = me.DateTimeField()                                # Ngày sinh

    # Hệ thống
    created_at = me.DateTimeField(default=datetime.utcnow)       # Ngày tạo tài khoản

    meta = {
        "collection": "users",   # tên collection trong MongoDB
        "indexes": ["email"]     # index cho email để tìm nhanh
    }

    def to_safe_dict(self):
        """
        Trả về thông tin user an toàn (không gồm password_hash).
        Dùng khi trả response cho client.
        """
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "address": self.address,
            "gender": self.gender,
            "role": self.role,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
