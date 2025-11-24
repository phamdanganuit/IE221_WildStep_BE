"""
Orders module models: Cart, Wishlist, Order, OrderItem
"""
import mongoengine as me
from datetime import datetime


class ProductInCart(me.EmbeddedDocument):
    """Product in shopping cart"""
    product_id = me.ObjectIdField(required=True)
    quantity = me.IntField(required=True, min_value=1)
    # Optional: color, size, price_at_add_time
    color = me.StringField()
    size = me.StringField()
    
    meta = {"strict": False}  # Ignore unknown fields like _id in embedded documents


class Cart(me.Document):
    """Shopping cart for users"""
    user = me.ReferenceField('User', required=True, unique=True, reverse_delete_rule=me.CASCADE)
    products = me.EmbeddedDocumentListField(ProductInCart, default=list)
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "carts"}

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Cart, self).save(*args, **kwargs)


class Wishlist(me.Document):
    """Wishlist (saved products) for users"""
    user = me.ReferenceField('User', required=True, unique=True, reverse_delete_rule=me.CASCADE)
    product_ids = me.ListField(me.ObjectIdField(), default=list)
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "wishlists"}

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Wishlist, self).save(*args, **kwargs)


class OrderItem(me.EmbeddedDocument):
    """Order item embedded in Order - snapshot of product at order time"""
    product_id = me.ObjectIdField(required=True)
    product_name = me.StringField(required=True)
    product_image = me.StringField()  # Main image URL
    quantity = me.IntField(required=True, min_value=1)
    price = me.FloatField(required=True, min_value=0)  # Price per unit at order time
    total = me.FloatField(required=True, min_value=0)  # quantity * price
    
    # Optional variants
    color = me.StringField()
    size = me.StringField()
    
    meta = {"strict": False}  # Ignore unknown fields like _id in embedded documents


class Order(me.Document):
    """Order model - Customer orders"""
    # Order identification
    order_number = me.StringField(required=True, unique=True)  # "ORD-001", "ORD-002", etc.
    
    # Customer & delivery
    user = me.ReferenceField('User', required=True)
    address = me.ReferenceField('Address', required=True)  # Shipping address
    
    # Order items
    items = me.EmbeddedDocumentListField(OrderItem, required=True)
    
    # Pricing
    subtotal = me.FloatField(required=True, min_value=0)  # Sum of item totals
    shipping_fee = me.FloatField(default=0, min_value=0)
    discount = me.FloatField(default=0, min_value=0)  # Discount amount from voucher
    vat = me.FloatField(default=0, min_value=0)  # VAT/tax amount
    total_price = me.FloatField(required=True, min_value=0)  # Final total
    
    # Voucher
    voucher = me.ReferenceField('Voucher', required=False)  # Optional voucher reference
    
    # Payment
    payment_method = me.StringField(
        choices=["cod", "bank_transfer", "credit_card", "e_wallet"],
        default="cod"
    )
    payment_status = me.StringField(
        choices=["pending", "paid", "refunded", "failed"],
        default="pending"
    )
    payment_info = me.ListField(me.StringField(), default=list)  # Additional payment details
    
    # Order status
    status = me.StringField(
        choices=["pending", "processing", "shipping", "completed", "cancelled"],
        default="pending"
    )
    
    # Notes
    notes = me.StringField()  # Customer notes or admin notes
    
    # Timestamps
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    completed_date = me.DateTimeField()  # Set when status becomes 'completed'
    
    meta = {
        "collection": "orders",
        "indexes": [
            "order_number",
            "user",
            "status",
            "payment_status",
            "created_at",
            "-created_at"  # Descending index for recent orders
        ]
    }
    
    def save(self, *args, **kwargs):
        """Auto-generate order_number and handle status changes"""
        # Generate order_number if not set
        if not self.order_number:
            # Find the latest order number
            last_order = Order.objects.order_by('-order_number').first()
            if last_order and last_order.order_number.startswith('ORD-'):
                try:
                    last_num = int(last_order.order_number.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.order_number = f"ORD-{new_num:06d}"  # ORD-000001, ORD-000002, etc.
        
        # Set completed_date when status becomes 'completed'
        if self.status == 'completed' and not self.completed_date:
            self.completed_date = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
        return super(Order, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order_number} - {self.user.email if self.user else 'Unknown'}"


class Voucher(me.Document):
    """Voucher/Coupon model (placeholder - can be expanded later)"""
    name = me.StringField(required=True)
    code = me.StringField(required=True, unique=True)
    description = me.StringField()
    discount = me.FloatField(required=True, min_value=0)  # % or fixed amount
    min_value = me.FloatField(default=0)  # Minimum order value to apply
    start_date = me.DateTimeField()
    expired_date = me.DateTimeField()
    categories = me.ListField(me.ObjectIdField())  # Applicable categories
    
    meta = {
        "collection": "vouchers",
        "indexes": ["code"]
    }
    
    def __str__(self):
        return f"{self.code} - {self.name}"
