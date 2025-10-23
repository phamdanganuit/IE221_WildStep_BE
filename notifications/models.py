from django.db import models



import mongoengine as me
from datetime import datetime

# Tương tự như app 'orders', chúng ta dùng chuỗi 'User'
# để khai báo tham chiếu và tránh lỗi circular import.

class NotificationDetail(me.EmbeddedDocument):
    """
    Đây là một thông báo cụ thể, được nhúng vào danh sách của người dùng.
    """
    title = me.StringField(required=True)
    content = me.StringField()
    # type giúp phân loại thông báo ở frontend, ví dụ:
    # 'promotion', 'order_status', 'system_update'
    type = me.StringField()
    read = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.utcnow)

class Notification(me.Document):
    """
    Mỗi user sẽ có một document Notification duy nhất,
    chứa một danh sách tất cả các thông báo của họ.
    """
    user = me.ReferenceField('User', required=True, unique=True, reverse_delete_rule=me.CASCADE)
    notifications = me.EmbeddedDocumentListField(NotificationDetail, default=list)

    meta = {"collection": "notifications"}