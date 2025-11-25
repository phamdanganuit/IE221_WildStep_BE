# Checkout Workflow & APIs

## Workflow

1. **User thêm sản phẩm vào Cart** → Cart API
2. **User chọn Address** → Address API  
3. **User nhập Voucher code (optional)** → Validate Voucher API
4. **User chọn Payment method** → Frontend
5. **User xác nhận đặt hàng** → Create Order API
6. **Hệ thống xử lý:**
   - Validate cart, address, voucher
   - Tính toán giá (subtotal, shipping, discount, VAT, total)
   - Tạo Order với snapshot sản phẩm
   - Cập nhật stock và sold của Product
   - Cập nhật UserVoucher status = "used"
   - Xóa Cart

---

## API 1: Validate Voucher

**Endpoint:** `POST /api/vouchers/validate`

**Auth:** Required

**Request Body:**
```json
{
  "code": "VOUCHER123",
  "subtotal": 500000,        // Optional - để check min_value
  "cart_items": [            // Optional - để check categories
    {
      "category_id": "category_id_here"
    }
  ]
}
```

**Response Success (200):**
```json
{
  "valid": true,
  "voucher": {
    "_id": "voucher_id",
    "code": "VOUCHER123",
    "name": "Giảm 10%",
    "discount": 10,
    "discount_type": "percentage"
  },
  "discount_amount": 50000,
  "message": "Voucher hợp lệ"
}
```

**Response Error (400):**
```json
{
  "valid": false,
  "message": "Voucher không hợp lệ hoặc đã hết hạn"
}
```

**Validation Logic:**
- Voucher tồn tại và active
- User đã thêm voucher vào tài khoản (UserVoucher.status = "active")
- Voucher chưa hết hạn (expired_date)
- Voucher đã có hiệu lực (start_date)
- Nếu có subtotal: kiểm tra min_value
- Nếu có cart_items: kiểm tra categories

---

## API 2: Create Order

**Endpoint:** `POST /api/orders`

**Auth:** Required

**Request Body:**
```json
{
  "address_id": "address_id_here",
  "voucher_id": "voucher_id_here",      // Optional
  "payment_method": "cod",              // cod | bank_transfer | credit_card | e_wallet
  "notes": "Giao hàng buổi sáng"        // Optional
}
```

**Response Success (201):**
```json
{
  "order": {
    "_id": "order_id",
    "order_number": "ORD-20240101-001",
    "user": "user_id",
    "address": {
      "_id": "address_id",
      "receiver": "Nguyễn Văn A",
      "phone": "0123456789",
      "detail": "123 Đường ABC",
      "ward": "Phường 1",
      "district": "Quận 1",
      "province": "TP.HCM"
    },
    "items": [
      {
        "product_id": "product_id",
        "product_name": "Giày thể thao",
        "product_image": "image_url",
        "quantity": 2,
        "price": 500000,
        "total": 1000000,
        "color": "Đỏ",
        "size": "42"
      }
    ],
    "pricing": {
      "subtotal": 1000000,
      "shipping_fee": 30000,
      "discount": 100000,
      "vat": 0,
      "total_price": 930000
    },
    "payment_method": "cod",
    "payment_status": "pending",
    "status": "pending",
    "notes": "Giao hàng buổi sáng",
    "created_at": "2024-01-01T10:00:00"
  }
}
```

**Response Error (400):**
```json
{
  "detail": "Giỏ hàng trống"
}
```

**Processing Logic:**
1. Validate cart có sản phẩm
2. Validate address thuộc user
3. Validate voucher (nếu có): tồn tại, đã thêm, status, thời gian, min_value, categories
4. Tính toán:
   - Subtotal từ cart items
   - Shipping fee: 30,000 VNĐ (mặc định)
   - Discount từ voucher (nếu có)
   - VAT: 0 (mặc định)
   - Total = Subtotal + Shipping - Discount + VAT
5. Tạo Order với snapshot sản phẩm (OrderItem)
6. Cập nhật Product stock và sold
7. Cập nhật UserVoucher status = "used" (nếu có)
8. Xóa Cart
9. Trả về Order đã tạo

**Error Cases:**
- Cart trống
- Address không tồn tại hoặc không thuộc user
- Voucher không hợp lệ/đã sử dụng/hết hạn
- Sản phẩm hết hàng hoặc không còn active
- Đơn hàng chưa đạt min_value của voucher

---

## Database Schema: Order

### Order Collection
```python
{
  "_id": ObjectId,                    # Primary key
  "order_number": String,              # Unique: "ORD-000001", "ORD-000002"
  "user": Reference(User),             # Required
  "address": Reference(Address),       # Required - Shipping address
  "items": [OrderItem],                # Embedded documents - Snapshot sản phẩm
  "subtotal": Float,                   # Sum of item totals (min: 0)
  "shipping_fee": Float,               # Default: 0 (min: 0)
  "discount": Float,                   # Discount amount from voucher (min: 0)
  "vat": Float,                        # VAT/tax amount (min: 0)
  "total_price": Float,                # Final total (min: 0)
  "voucher": Reference(Voucher),      # Optional
  "payment_method": String,            # "cod" | "bank_transfer" | "credit_card" | "e_wallet"
  "payment_status": String,            # "pending" | "paid" | "refunded" | "failed"
  "payment_info": [String],            # Additional payment details
  "status": String,                    # "pending" | "processing" | "shipping" | "completed" | "cancelled"
  "notes": String,                     # Customer/admin notes
  "created_at": DateTime,              # Auto: datetime.utcnow()
  "updated_at": DateTime,              # Auto: datetime.utcnow()
  "completed_date": DateTime           # Set when status = "completed"
}
```

**Indexes:**
- `order_number` (unique)
- `user`
- `status`
- `payment_status`
- `created_at`
- `-created_at` (descending)

**Auto-generated:**
- `order_number`: Tự động tạo "ORD-000001", "ORD-000002", ...
- `completed_date`: Tự động set khi status = "completed"
- `updated_at`: Tự động cập nhật mỗi lần save

---

### OrderItem (Embedded Document)
```python
{
  "product_id": ObjectId,              # Required
  "product_name": String,               # Required - Snapshot tại thời điểm đặt hàng
  "product_image": String,              # Main image URL
  "quantity": Integer,                  # Required (min: 1)
  "price": Float,                       # Required - Price per unit tại thời điểm đặt hàng (min: 0)
  "total": Float,                       # Required - quantity * price (min: 0)
  "color": String,                      # Optional
  "size": String                        # Optional
}
```

**Lưu ý:**
- OrderItem là **snapshot** của sản phẩm tại thời điểm đặt hàng
- Lưu `product_name`, `product_image`, `price` để đảm bảo thông tin không thay đổi
- Không tham chiếu trực tiếp đến Product (chỉ lưu `product_id`)

---

### Relationships

**Order → User:**
- ReferenceField (required)
- Một User có nhiều Order

**Order → Address:**
- ReferenceField (required)
- Address phải thuộc về User

**Order → Voucher:**
- ReferenceField (optional)
- Một Order có thể có 1 Voucher hoặc không

**Order → OrderItem:**
- EmbeddedDocumentListField
- Một Order có nhiều OrderItem (embedded)

---

### Status Flow

**Order Status:**
```
pending → processing → shipping → completed
   ↓
cancelled
```

**Payment Status:**
```
pending → paid
   ↓
refunded | failed
```
