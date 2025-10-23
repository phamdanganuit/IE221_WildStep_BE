from django.db import models

# Create your models here.
# orders/models.py

import mongoengine as me
from datetime import datetime



class ProductInCart(me.EmbeddedDocument):
    # Tạm thời chỉ cần ID sản phẩm và số lượng.
    # Sau này khi có app 'products', chúng ta sẽ làm chi tiết hơn.
    product_id = me.ObjectIdField(required=True)
    quantity = me.IntField(required=True, min_value=1)
    # Có thể thêm các trường khác như: color, size, price_at_add_time

class Cart(me.Document):
    # user trỏ đến collection 'users'
    user = me.ReferenceField('User', required=True, unique=True, reverse_delete_rule=me.CASCADE)
    products = me.EmbeddedDocumentListField(ProductInCart, default=list)
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "carts"}

    # Ghi đè hàm save để tự động cập nhật `updated_at` mỗi khi có thay đổi
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Cart, self).save(*args, **kwargs)

class Wishlist(me.Document):
    user = me.ReferenceField('User', required=True, unique=True, reverse_delete_rule=me.CASCADE)
    # Trong wishlist, thường chúng ta chỉ cần lưu ID của sản phẩm
    product_ids = me.ListField(me.ObjectIdField(), default=list)
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "wishlists"}

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Wishlist, self).save(*args, **kwargs)