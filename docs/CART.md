# API Giỏ Hàng (Cart API)

Tài liệu này mô tả đầy đủ các API endpoint cho chức năng giỏ hàng.

**Base URL:** `/api/cart` hoặc `/api/cart/items` (tùy endpoint)

**Authentication:** Tất cả các endpoint đều yêu cầu Bearer token trong header `Authorization`

---

## 1. Lấy Giỏ Hàng (Get Cart)

### ✅ GET `/api/cart`

**Mục đích:** Lấy toàn bộ sản phẩm trong giỏ hàng của user hiện tại

**Method:** `GET`

**Auth:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer {token}
```

**Request Body:** Không có

**Response 200 (Thành công):**
```json
{
  "_id": "cart_id_12345",
  "user": "user_id_67890",
  "products": [
    {
      "product_id": "product_id_123",
      "quantity": 2,
      "size": "US M10/W12",
      "color": "Mặc định"
    }
  ],
  "created_at": "2025-10-20T10:00:00.000Z",
  "updated_at": "2025-10-25T09:30:00.000Z"
}
```

**Hoặc Response với product details được populate:**
```json
{
  "_id": "cart_id_12345",
  "user": "user_id_67890",
  "products": [
    {
      "product_id": "product_id_123",
      "product": {
        "_id": "product_id_123",
        "name": "Converse x NARUTO Chuck Taylor All Star",
        "originalPrice": 5432200,
        "sold": 31,
        "rate": 4.3,
        "stock": 12,
        "discount": 10,
        "description": "The OG classic reworked with colors, graphics and details inspired by Naruto and his unique powers.",
        "images": [
          "https://static.nike.com/a/images/t_web_pdp_535_v2/f_auto/50266e78-2bcf-4dfe-bce4-293a63a05dae/NIKE+AVA+ROVER.png"
        ],
        "brand": {
          "_id": "brand_id_1",
          "name": "Converse"
        },
        "sizeTable": "https://templates.mediamodifier.com/63ff3c773e8bc57b10ca810b/size-table-chart-template-for-shoes.jpg",
        "category": {
          "_id": "category_id_1",
          "name": "Giày chạy bộ",
          "parent": {
            "_id": "parent_category_id",
            "name": "Nam"
          }
        },
        "createdAt": "2025-10-20T10:00:00.000Z"
      },
      "quantity": 2,
      "size": "US M10/W12",
      "color": "Mặc định"
    }
  ],
  "created_at": "2025-10-20T10:00:00.000Z",
  "updated_at": "2025-10-25T09:30:00.000Z"
}
```

**Response 200 (Giỏ hàng trống):**
```json
{
  "_id": "cart_id_12345",
  "user": "user_id_67890",
  "products": [],
  "created_at": "2025-10-20T10:00:00.000Z",
  "updated_at": "2025-10-25T09:30:00.000Z"
}
```

**Response 401 (Unauthorized):**
```json
{
  "detail": "Token không hợp lệ hoặc đã hết hạn"
}
```

**Response 500 (Server Error):**
```json
{
  "detail": "Đã xảy ra lỗi khi lấy giỏ hàng"
}
```

**Yêu cầu đặc biệt:**
- Nếu user chưa có giỏ hàng, tự động tạo giỏ hàng mới và trả về giỏ hàng trống
- Sắp xếp `products` theo thời gian thêm vào giỏ hàng (mới nhất trước)
- Kiểm tra và cập nhật stock của sản phẩm trước khi trả về (nếu sản phẩm hết hàng, đánh dấu trong response)
- Response có thể populate product details từ `product_id` để trả về thông tin đầy đủ

---

## 2. Thêm Sản Phẩm Vào Giỏ Hàng (Add to Cart)

### ✅ POST `/api/cart/items`

**Mục đích:** Thêm sản phẩm mới vào giỏ hàng hoặc cập nhật số lượng nếu sản phẩm đã tồn tại

**Method:** `POST`

**Auth:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "productId": "product_id_123",
  "quantity": 1,
  "size": "US M10/W12",
  "color": "Mặc định"
}
```

**Body Fields (bắt buộc):**
- `productId` (string, required): ID của sản phẩm
- `quantity` (number, required): Số lượng sản phẩm (min: 1, max: 99)
- `size` (string, required): Tên size được chọn (phải khớp với một trong các size của product)
- `color` (string, required): Tên màu được chọn (phải khớp với một trong các color của product)

**Response 201 (Thành công - Thêm mới):**
```json
{
  "product_id": "product_id_123",
  "quantity": 1,
  "size": "US M10/W12",
  "color": "Mặc định",
  "message": "Đã thêm sản phẩm vào giỏ hàng"
}
```

**Hoặc Response với product details:**
```json
{
  "product_id": "product_id_123",
  "product": {
    "_id": "product_id_123",
    "name": "Converse x NARUTO Chuck Taylor All Star",
    "originalPrice": 5432200,
    "discount": 10,
    "stock": 12,
    "images": [
      "https://static.nike.com/a/images/t_web_pdp_535_v2/f_auto/50266e78-2bcf-4dfe-bce4-293a63a05dae/NIKE+AVA+ROVER.png"
    ],
    "brand": {
      "_id": "brand_id_1",
      "name": "Converse"
    }
  },
  "quantity": 1,
  "size": "US M10/W12",
  "color": "Mặc định",
  "message": "Đã thêm sản phẩm vào giỏ hàng"
}
```

**Response 200 (Thành công - Cập nhật số lượng):**
```json
{
  "product_id": "product_id_123",
  "quantity": 3,
  "size": "US M10/W12",
  "color": "Mặc định",
  "message": "Đã cập nhật số lượng sản phẩm trong giỏ hàng"
}
```

**Response 400 (Bad Request - Sản phẩm không tồn tại):**
```json
{
  "detail": "Sản phẩm không tồn tại"
}
```

**Response 400 (Bad Request - Size không hợp lệ):**
```json
{
  "detail": "Size không hợp lệ cho sản phẩm này"
}
```

**Response 400 (Bad Request - Màu không hợp lệ):**
```json
{
  "detail": "Màu không hợp lệ cho sản phẩm này"
}
```

**Lưu ý:** `size` và `color` phải khớp chính xác với `size_name` và `color_name` trong mảng `sizes` và `colors` của product.

**Response 400 (Bad Request - Hết hàng):**
```json
{
  "detail": "Sản phẩm đã hết hàng"
}
```

**Response 400 (Bad Request - Số lượng vượt quá tồn kho):**
```json
{
  "detail": "Số lượng yêu cầu vượt quá số lượng tồn kho. Số lượng còn lại: 5"
}
```

**Response 400 (Bad Request - Số lượng không hợp lệ):**
```json
{
  "detail": "Số lượng phải từ 1 đến 99"
}
```

**Response 401 (Unauthorized):**
```json
{
  "detail": "Token không hợp lệ hoặc đã hết hạn"
}
```

**Response 500 (Server Error):**
```json
{
  "detail": "Đã xảy ra lỗi khi thêm sản phẩm vào giỏ hàng"
}
```

**Yêu cầu đặc biệt:**
- Nếu sản phẩm với cùng `productId`, `size`, `color` đã tồn tại trong giỏ hàng, **cộng dồn** số lượng (không tạo mới)
- Kiểm tra stock trước khi thêm/cập nhật
- Validate `size` và `color` phải khớp với một trong các size/color của `productId`
- Giới hạn số lượng tối đa: 99 sản phẩm mỗi item
- Giới hạn tổng số items trong giỏ hàng: 50 items
- Nếu cộng dồn vượt quá stock, set quantity = stock và trả về cảnh báo

---

## 3. Cập Nhật Số Lượng (Update Quantity)

### ✅ PUT `/api/cart/items/:cartItemId`

**Mục đích:** Cập nhật số lượng của một sản phẩm trong giỏ hàng

**Method:** `PUT`

**Auth:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**URL Parameters:**
- `cartItemId` (string, required): ID của cart item cần cập nhật (index trong mảng products của Cart)

**Request Body:**
```json
{
  "quantity": 3
}
```

**Body Fields (bắt buộc):**
- `quantity` (number, required): Số lượng mới (min: 1, max: 99)

**Response 200 (Thành công):**
```json
{
  "product_id": "product_id_123",
  "quantity": 3,
  "size": "US M10/W12",
  "color": "Mặc định",
  "message": "Đã cập nhật số lượng thành công"
}
```

**Response 400 (Bad Request - Số lượng không hợp lệ):**
```json
{
  "detail": "Số lượng phải từ 1 đến 99"
}
```

**Response 400 (Bad Request - Số lượng vượt quá tồn kho):**
```json
{
  "detail": "Số lượng yêu cầu vượt quá số lượng tồn kho. Số lượng còn lại: 5"
}
```

**Response 404 (Not Found):**
```json
{
  "detail": "Không tìm thấy sản phẩm trong giỏ hàng"
}
```

**Response 403 (Forbidden):**
```json
{
  "detail": "Bạn không có quyền cập nhật sản phẩm này"
}
```

**Lưu ý:** `cartItemId` có thể là index trong mảng `products` của Cart hoặc một identifier khác tùy implementation.

**Response 401 (Unauthorized):**
```json
{
  "detail": "Token không hợp lệ hoặc đã hết hạn"
}
```

**Response 500 (Server Error):**
```json
{
  "detail": "Đã xảy ra lỗi khi cập nhật số lượng"
}
```

**Yêu cầu đặc biệt:**
- Kiểm tra `cartItemId` thuộc về user hiện tại
- Kiểm tra stock trước khi cập nhật
- Nếu quantity = 0, có thể tự động xóa item (hoặc trả về lỗi, tùy thiết kế)
- Validate quantity phải là số nguyên dương

---

## 4. Xóa Sản Phẩm Khỏi Giỏ Hàng (Remove from Cart)

### ✅ DELETE `/api/cart/items/:cartItemId`

**Mục đích:** Xóa một sản phẩm khỏi giỏ hàng

**Method:** `DELETE`

**Auth:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer {token}
```

**URL Parameters:**
- `cartItemId` (string, required): ID của cart item cần xóa (index trong mảng products của Cart)

**Request Body:** Không có

**Response 200 (Thành công):**
```json
{
  "message": "Đã xóa sản phẩm khỏi giỏ hàng thành công"
}
```

**Hoặc Response 204 (No Content):**
```
(No body)
```

**Response 404 (Not Found):**
```json
{
  "detail": "Không tìm thấy sản phẩm trong giỏ hàng"
}
```

**Response 403 (Forbidden):**
```json
{
  "detail": "Bạn không có quyền xóa sản phẩm này"
}
```

**Response 401 (Unauthorized):**
```json
{
  "detail": "Token không hợp lệ hoặc đã hết hạn"
}
```

**Response 500 (Server Error):**
```json
{
  "detail": "Đã xảy ra lỗi khi xóa sản phẩm khỏi giỏ hàng"
}
```

**Yêu cầu đặc biệt:**
- Kiểm tra `cartItemId` thuộc về user hiện tại
- Sau khi xóa, nếu giỏ hàng trống, có thể giữ nguyên giỏ hàng hoặc xóa luôn giỏ hàng (tùy thiết kế)

---

## 5. Xóa Tất Cả Sản Phẩm (Clear Cart)

### ✅ DELETE `/api/cart/items`

**Mục đích:** Xóa tất cả sản phẩm khỏi giỏ hàng

**Method:** `DELETE`

**Auth:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer {token}
```

**Request Body:** Không có

**Response 200 (Thành công):**
```json
{
  "message": "Đã xóa tất cả sản phẩm khỏi giỏ hàng"
}
```

**Hoặc Response 204 (No Content):**
```
(No body)
```

**Response 401 (Unauthorized):**
```json
{
  "detail": "Token không hợp lệ hoặc đã hết hạn"
}
```

**Response 500 (Server Error):**
```json
{
  "detail": "Đã xảy ra lỗi khi xóa giỏ hàng"
}
```

**Yêu cầu đặc biệt:**
- Xóa tất cả `cart_products` nhưng giữ lại cart document (hoặc xóa luôn cart, tùy thiết kế)

---

## 6. Lấy Tổng Số Lượng Sản Phẩm (Get Cart Count)

### ✅ GET `/api/cart/count`

**Mục đích:** Lấy tổng số lượng sản phẩm trong giỏ hàng (dùng cho badge trên icon giỏ hàng)

**Method:** `GET`

**Auth:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer {token}
```

**Request Body:** Không có

**Response 200 (Thành công):**
```json
{
  "count": 5
}
```

**Response 401 (Unauthorized):**
```json
{
  "detail": "Token không hợp lệ hoặc đã hết hạn"
}
```

**Yêu cầu đặc biệt:**
- Trả về tổng số lượng (sum of quantities) của tất cả items trong giỏ hàng
- Endpoint này nên được tối ưu để trả về nhanh (có thể cache)

---

## Validation Rules (Quy Tắc Validation)

### 1. ProductId
- Phải tồn tại trong database
- Sản phẩm phải đang active (không bị xóa/ẩn)

### 2. Size
- Phải là string khớp với `size_name` trong mảng `sizes` của product
- Phải thuộc về productId được chỉ định
- Size phải có stock > 0

### 3. Color
- Phải là string khớp với `color_name` trong mảng `colors` của product
- Phải thuộc về productId được chỉ định

### 4. Quantity
- Phải là số nguyên dương
- Min: 1
- Max: 99 (hoặc stock hiện tại, lấy giá trị nhỏ hơn)
- Không được vượt quá stock của sản phẩm

### 5. Stock Check
- Kiểm tra stock trước mỗi thao tác thêm/cập nhật
- Nếu stock = 0, trả về lỗi "Sản phẩm đã hết hàng"
- Nếu quantity > stock, trả về lỗi với thông tin stock còn lại

---

## Business Logic (Logic Nghiệp Vụ)

### 1. Add to Cart Logic
```
1. Validate input (productId, size, color, quantity)
2. Kiểm tra product tồn tại và active
3. Kiểm tra size và color khớp với sizes/colors của product
4. Kiểm tra stock >= quantity
5. Tìm cart của user (hoặc tạo mới nếu chưa có)
6. Tìm cart item với cùng productId, size, color
7. Nếu tồn tại:
   - Cộng dồn quantity (newQuantity = oldQuantity + quantity)
   - Kiểm tra newQuantity <= stock, nếu không thì set = stock
   - Cập nhật cart item
8. Nếu không tồn tại:
   - Kiểm tra số lượng items trong cart < 50
   - Tạo mới cart item (ProductInCart)
9. Trả về kết quả
```

### 2. Update Quantity Logic
```
1. Validate cartItemId thuộc về user hiện tại
2. Validate quantity (1-99)
3. Kiểm tra stock >= quantity
4. Cập nhật quantity của cart item
5. Trả về kết quả
```

### 3. Remove from Cart Logic
```
1. Validate cartItemId thuộc về user hiện tại
2. Xóa cart item khỏi mảng products
3. Trả về kết quả
```

---

## Database Schema (Cấu Trúc Database)

### Cart Collection/Model
```javascript
{
  _id: ObjectId,
  user: ObjectId (ref: User),
  products: [
    {
      product_id: ObjectId (ref: Product),
      quantity: Number,
      size: String,  // size_name từ product.sizes
      color: String  // color_name từ product.colors
    }
  ],
  created_at: Date,
  updated_at: Date
}
```

**Indexes:**
- `user`: Unique index (mỗi user chỉ có 1 cart)

**Lưu ý:**
- `products` là mảng các embedded documents (ProductInCart)
- `size` và `color` là strings, không phải object references
- Product có `sizes` và `colors` là embedded arrays (SizeVariant, ColorVariant)

---

## Error Handling (Xử Lý Lỗi)

Tất cả API trả về error theo format chuẩn:
```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes:**
- `200`: Success (GET, PUT, DELETE thành công)
- `201`: Created (POST thành công)
- `204`: No Content (DELETE thành công, không trả về body)
- `400`: Bad Request (validation error, stock không đủ, etc.)
- `401`: Unauthorized (invalid/expired token)
- `403`: Forbidden (user không có quyền truy cập resource)
- `404`: Not Found (cart_product không tồn tại)
- `500`: Internal Server Error (lỗi server)

---

## Rate Limiting (Giới Hạn Tần Suất)

- **Add to Cart:** Tối đa 30 requests/phút/user
- **Update Quantity:** Tối đa 60 requests/phút/user
- **Remove from Cart:** Tối đa 20 requests/phút/user
- **Get Cart:** Tối đa 120 requests/phút/user

---

## Notes (Ghi Chú)

1. **Cart Auto-Creation:** Khi user đăng nhập lần đầu và thêm sản phẩm, tự động tạo cart mới

2. **Stock Synchronization:** Luôn kiểm tra stock real-time trước mỗi thao tác để tránh overselling

3. **Cart Expiry:** Có thể thiết kế cart tự động xóa sau 30 ngày không hoạt động (optional)

4. **Optimistic Updates:** Frontend có thể update UI trước, nhưng phải rollback nếu API trả về lỗi

5. **Concurrent Updates:** Xử lý race condition khi nhiều request cùng lúc (dùng transaction hoặc lock)

6. **Cart Product Limit:** Giới hạn 50 items/cart để tránh performance issues

7. **Quantity Limit:** Giới hạn 99 sản phẩm/item để tránh abuse

