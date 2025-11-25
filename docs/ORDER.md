# API Endpoints - Order Management (Quản lý Đơn hàng)

## Base URL
```
{base_url}/orders
```
Ví dụ: `http://localhost:8000/api/orders` hoặc `https://api.shoe-shop.app/api/orders`

---

## 1. Tạo đơn hàng mới

### **POST** `/orders`

**Mô tả:** Tạo đơn hàng mới từ giỏ hàng của user hiện tại.

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "address_id": "string (required)",
  "payment_method": "string (required)",
  "voucher_id": "string (optional)",
  "notes": "string (optional)"
}
```

**Chi tiết các trường:**

| Trường | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|--------|------|----------|-------|-------|
| `address_id` | string | ✅ Yes | ID địa chỉ giao hàng đã lưu trong hệ thống | `"60d5ecf3e7b1c3b4a8f1b1a0"` |
| `payment_method` | string | ✅ Yes | Phương thức thanh toán. Giá trị hợp lệ: `cod`, `bank_transfer`, `credit_card`, `e_wallet` | `"cod"` |
| `voucher_id` | string | ❌ No | ID voucher áp dụng (hiện tại chỉ hỗ trợ 1 voucher) | `"60d5ecf3e7b1c3b4a8f1b1a1"` |
| `notes` | string | ❌ No | Ghi chú đơn hàng từ khách hàng | `"Giao hàng vào buổi sáng"` |

**Validation:**
- `address_id`: Phải tồn tại trong danh sách địa chỉ của user
- `payment_method`: Phải là một trong các giá trị: `cod`, `bank_transfer`, `credit_card`, `e_wallet`
- `voucher_id`: Phải tồn tại và còn hiệu lực (nếu có)
- Giỏ hàng không được rỗng
- Tất cả sản phẩm trong giỏ hàng phải còn tồn kho

**Success Response (200 OK):**
```json
{
  "order": {
    "_id": "69251b01ce7854d9b6553798",
    "order_number": "ORD-000003",
    "user": "690ca89b7e4cdb6f3a594d33",
    "address": "692516a1cfd56b7be11c3c8b",
    "items": [
      {
        "product_id": "691a514d8a441121bc44c50a",
        "product_name": "Nike Ava Rover",
        "product_image": "https://shoeshop.blob.core.windows.net/media/products/691a514d8a441121bc44c50a_3c6d733d.png",
        "quantity": 1,
        "price": 3407810.0,
        "total": 3407810.0,
        "color": "Đen",
        "size": "31"
      }
    ],
    "subtotal": 3407810.0,
    "shipping_fee": 30000.0,
    "discount": 0.5,
    "vat": 0.0,
    "total_price": 3437809.5,
    "voucher": "69250383af4128ac9bd4cf6d",
    "payment_method": "cod",
    "payment_status": "pending",
    "payment_info": [],
    "status": "pending",
    "notes": "",
    "created_at": "2025-01-25T10:30:00.000Z",
    "updated_at": "2025-01-25T10:30:00.000Z"
  }
}
```

**Error Responses:**

**400 Bad Request** - Dữ liệu không hợp lệ:
```json
{
  "detail": "Vui lòng chọn địa chỉ giao hàng"
}
```
hoặc
```json
{
  "detail": "Phương thức thanh toán không hợp lệ"
}
```

**401 Unauthorized** - Chưa đăng nhập hoặc token hết hạn:
```json
{
  "detail": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
}
```

**404 Not Found** - Địa chỉ không tồn tại:
```json
{
  "detail": "Địa chỉ giao hàng không tồn tại"
}
```

**409 Conflict** - Voucher không hợp lệ hoặc giỏ hàng rỗng:
```json
{
  "detail": "Voucher không còn hiệu lực"
}
```
hoặc
```json
{
  "detail": "Giỏ hàng đang trống"
}
```

**422 Unprocessable Entity** - Sản phẩm hết hàng:
```json
{
  "detail": "Sản phẩm 'Giày thể thao Nike Air Max' size 42 màu Đen đã hết hàng"
}
```

---

## 2. Lấy danh sách đơn hàng

### **GET** `/orders`

**Mô tả:** Lấy danh sách đơn hàng của user hiện tại với các bộ lọc tùy chọn.

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|---------|------|----------|-------|-------|
| `status` | string | ❌ No | Lọc theo trạng thái. Giá trị: `placed`, `pending`, `processing`, `shipping`, `completed`, `cancelled` | `?status=pending` |
| `page` | integer | ❌ No | Số trang (bắt đầu từ 1) | `?page=1` |
| `limit` | integer | ❌ No | Số lượng đơn hàng mỗi trang (mặc định: 10) | `?limit=20` |
| `sort` | string | ❌ No | Sắp xếp. Giá trị: `created_at`, `-created_at` (mặc định: `-created_at`) | `?sort=-created_at` |

**Ví dụ Request:**
```
GET /orders?status=pending&page=1&limit=10
GET /orders?status=completed&sort=-created_at
GET /orders
```

**Success Response (200 OK):**
```json
{
  "orders": [
    {
      "_id": "69251b01ce7854d9b6553798",
      "order_number": "ORD-000003",
      "user": "690ca89b7e4cdb6f3a594d33",
      "address": "692516a1cfd56b7be11c3c8b",
      "items": [
        {
          "product_id": "691a514d8a441121bc44c50a",
          "product_name": "Nike Ava Rover",
          "product_image": "https://shoeshop.blob.core.windows.net/media/products/691a514d8a441121bc44c50a_3c6d733d.png",
          "quantity": 1,
          "price": 3407810.0,
          "total": 3407810.0,
          "color": "Đen",
          "size": "31"
        }
      ],
      "subtotal": 3407810.0,
      "shipping_fee": 30000.0,
      "discount": 0.5,
      "vat": 0.0,
      "total_price": 3437809.5,
      "voucher": "69250383af4128ac9bd4cf6d",
      "payment_method": "cod",
      "payment_status": "pending",
      "payment_info": [],
      "status": "pending",
      "notes": "",
      "created_at": "2025-01-25T10:30:00.000Z",
      "updated_at": "2025-01-25T10:30:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "totalPages": 3
  }
}
```

**Hoặc format đơn giản hơn (nếu không có pagination):**
```json
{
  "orders": [
    {
      "_id": "69251b01ce7854d9b6553798",
      "order_number": "ORD-000003",
      "status": "pending",
      "total_price": 3437809.5,
      "created_at": "2025-01-25T10:30:00.000Z"
    }
  ]
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "detail": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
}
```

**400 Bad Request** - Query parameter không hợp lệ:
```json
{
  "detail": "Status không hợp lệ"
}
```

---

## 3. Lấy chi tiết đơn hàng

### **GET** `/orders/{orderId}`

**Mô tả:** Lấy thông tin chi tiết của một đơn hàng cụ thể.

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| `orderId` | string | ✅ Yes | ID đơn hàng (có thể là `_id` hoặc `orderNumber`) |

**Ví dụ Request:**
```
GET /orders/60d5ecf3e7b1c3b4a8f1b1a2
GET /orders/ORD-2024-001234
```

**Success Response (200 OK):**
```json
{
  "order": {
    "_id": "69251b01ce7854d9b6553798",
    "order_number": "ORD-000003",
    "user": "690ca89b7e4cdb6f3a594d33",
    "address": "692516a1cfd56b7be11c3c8b",
    "items": [
      {
        "product_id": "691a514d8a441121bc44c50a",
        "product_name": "Nike Ava Rover",
        "product_image": "https://shoeshop.blob.core.windows.net/media/products/691a514d8a441121bc44c50a_3c6d733d.png",
        "quantity": 1,
        "price": 3407810.0,
        "total": 3407810.0,
        "color": "Đen",
        "size": "31"
      },
      {
        "product_id": "691a514d8a441121bc44c50b",
        "product_name": "Adidas Running Shoes",
        "product_image": "https://shoeshop.blob.core.windows.net/media/products/adidas-running-1.jpg",
        "quantity": 2,
        "price": 2500000.0,
        "total": 5000000.0,
        "color": "Trắng",
        "size": "42"
      }
    ],
    "subtotal": 8407810.0,
    "shipping_fee": 30000.0,
    "discount": 0.5,
    "vat": 0.0,
    "total_price": 8437809.5,
    "voucher": "69250383af4128ac9bd4cf6d",
    "payment_method": "cod",
    "payment_status": "pending",
    "payment_info": [],
    "status": "pending",
    "notes": "Giao hàng vào buổi sáng",
    "created_at": "2025-01-25T10:30:00.000Z",
    "updated_at": "2025-01-25T11:00:00.000Z"
  }
}
```

**Lưu ý:** 
- `address` và `voucher` là ObjectId references, không phải object đầy đủ. Frontend có thể cần gọi thêm API để lấy thông tin chi tiết nếu cần.
- `user` là ObjectId reference của user sở hữu đơn hàng.
- `payment_status` có thể là: `"pending"`, `"paid"`, `"failed"`, `"refunded"`.

**Error Responses:**

**401 Unauthorized:**
```json
{
  "detail": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
}
```

**403 Forbidden** - User không có quyền xem đơn hàng này:
```json
{
  "detail": "Bạn không có quyền xem đơn hàng này"
}
```

**404 Not Found:**
```json
{
  "detail": "Không tìm thấy đơn hàng"
}
```

---

## 4. Hủy đơn hàng

### **PATCH** `/orders/{orderId}/status`

**Mô tả:** Cập nhật trạng thái đơn hàng (chủ yếu dùng để hủy đơn hàng).

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Path Parameters:**

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| `orderId` | string | ✅ Yes | ID đơn hàng |

**Request Body:**
```json
{
  "status": "cancelled"
}
```

**Chi tiết các trường:**

| Trường | Kiểu | Bắt buộc | Mô tả | Giá trị hợp lệ |
|--------|------|----------|-------|---------------|
| `status` | string | ✅ Yes | Trạng thái mới của đơn hàng | `"cancelled"` (hiện tại chỉ hỗ trợ hủy) |

**Validation:**
- Chỉ có thể hủy đơn hàng khi status là `placed` hoặc `pending`
- Không thể hủy đơn hàng đã `shipping`, `completed`, hoặc đã `cancelled`
- User chỉ có thể hủy đơn hàng của chính mình

**Ví dụ Request:**
```
PATCH /orders/60d5ecf3e7b1c3b4a8f1b1a2/status
Content-Type: application/json

{
  "status": "cancelled"
}
```

**Success Response (200 OK):**
```json
{
  "order": {
    "_id": "69251b01ce7854d9b6553798",
    "order_number": "ORD-000003",
    "user": "690ca89b7e4cdb6f3a594d33",
    "address": "692516a1cfd56b7be11c3c8b",
    "items": [
      {
        "product_id": "691a514d8a441121bc44c50a",
        "product_name": "Nike Ava Rover",
        "product_image": "https://shoeshop.blob.core.windows.net/media/products/691a514d8a441121bc44c50a_3c6d733d.png",
        "quantity": 1,
        "price": 3407810.0,
        "total": 3407810.0,
        "color": "Đen",
        "size": "31"
      }
    ],
    "subtotal": 3407810.0,
    "shipping_fee": 30000.0,
    "discount": 0.5,
    "vat": 0.0,
    "total_price": 3437809.5,
    "voucher": "69250383af4128ac9bd4cf6d",
    "payment_method": "cod",
    "payment_status": "pending",
    "payment_info": [],
    "status": "cancelled",
    "notes": "",
    "created_at": "2025-01-25T10:30:00.000Z",
    "updated_at": "2025-01-25T12:00:00.000Z"
  },
  "message": "Hủy đơn hàng thành công"
}
```

**Error Responses:**

**400 Bad Request** - Không thể hủy đơn hàng:
```json
{
  "detail": "Không thể hủy đơn hàng đã được vận chuyển"
}
```
hoặc
```json
{
  "detail": "Trạng thái đơn hàng không cho phép hủy"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
}
```

**403 Forbidden** - User không có quyền:
```json
{
  "detail": "Bạn không có quyền hủy đơn hàng này"
}
```

**404 Not Found:**
```json
{
  "detail": "Không tìm thấy đơn hàng"
}
```

---

## Cấu trúc dữ liệu Order

### Order Object

```typescript
interface Order {
  _id: string;                    // ID đơn hàng (ObjectId)
  order_number: string;            // Mã đơn hàng (ví dụ: ORD-000003)
  user: string;                    // ID người dùng (ObjectId reference)
  address: string;                 // ID địa chỉ giao hàng (ObjectId reference)
  items: OrderItem[];             // Danh sách sản phẩm
  subtotal: number;               // Tổng tiền sản phẩm (double)
  shipping_fee: number;            // Phí vận chuyển (double)
  discount: number;               // Số tiền giảm giá (double)
  vat: number;                    // Thuế VAT (double)
  total_price: number;            // Tổng tiền thanh toán (double)
  voucher?: string;               // ID voucher đã áp dụng (ObjectId reference, optional)
  payment_method: PaymentMethod;  // Phương thức thanh toán
  payment_status: PaymentStatus;  // Trạng thái thanh toán
  payment_info: any[];            // Thông tin thanh toán (array)
  status: OrderStatus;             // Trạng thái đơn hàng
  notes: string;                  // Ghi chú (có thể là chuỗi rỗng)
  created_at: string;             // Ngày tạo (ISO 8601)
  updated_at: string;             // Ngày cập nhật (ISO 8601)
}
```

### Order Status

```typescript
type OrderStatus = 
  | "placed"      // Đã đặt (chờ xác nhận)
  | "pending"     // Chờ lấy hàng / Đang xử lý
  | "processing"  // Đang xử lý (alias của pending)
  | "shipping"    // Đang vận chuyển
  | "completed"   // Đã hoàn thành
  | "cancelled";  // Đã hủy
```

### Payment Method

```typescript
type PaymentMethod = 
  | "cod"           // Thanh toán khi nhận hàng
  | "bank_transfer" // Chuyển khoản ngân hàng
  | "credit_card"   // Thẻ tín dụng
  | "e_wallet";     // Ví điện tử
```

### Payment Status

```typescript
type PaymentStatus = 
  | "pending"   // Chờ thanh toán
  | "paid"      // Đã thanh toán
  | "failed"    // Thanh toán thất bại
  | "refunded"; // Đã hoàn tiền
```

### Order Item

```typescript
interface OrderItem {
  product_id: string;      // ID sản phẩm (ObjectId)
  product_name: string;     // Tên sản phẩm (string đơn giản, không phải object)
  product_image: string;    // URL ảnh sản phẩm
  quantity: number;         // Số lượng
  price: number;           // Giá tại thời điểm đặt hàng (double)
  total: number;           // Tổng tiền của item này (quantity * price) (double)
  color: string;           // Màu sắc
  size: string;            // Kích cỡ
}
```

**Lưu ý:** 
- `product_id` là ObjectId reference, không phải object đầy đủ
- `product_name` và `product_image` được lưu trực tiếp trong order để đảm bảo hiển thị đúng ngay cả khi sản phẩm đã bị xóa hoặc thay đổi
- `total` = `quantity * price` (tổng tiền của item này)

### Address Reference

Trong order, `address` chỉ là ObjectId reference. Để lấy thông tin chi tiết địa chỉ, cần gọi API:
- `GET /api/addresses/{addressId}` hoặc
- `GET /api/addresses` để lấy danh sách và tìm theo ID

### Voucher Reference

Trong order, `voucher` chỉ là ObjectId reference. Để lấy thông tin chi tiết voucher, cần gọi API:
- `GET /api/vouchers/{voucherId}` hoặc
- `GET /api/vouchers` để lấy danh sách và tìm theo ID

---

## Yêu cầu đặc biệt

### Authentication
- Tất cả các endpoint đều yêu cầu Bearer Token trong header `Authorization`
- Token được lấy từ API đăng nhập (`/api/login`)
- Format: `Authorization: Bearer {access_token}`
- Token hết hạn sẽ trả về `401 Unauthorized`

### Validation Rules

1. **Tạo đơn hàng:**
   - Giỏ hàng không được rỗng
   - Tất cả sản phẩm phải còn tồn kho đủ số lượng
   - Địa chỉ phải thuộc về user hiện tại
   - Voucher (nếu có) phải còn hiệu lực và user đủ điều kiện sử dụng

2. **Hủy đơn hàng:**
   - Chỉ có thể hủy khi status là `placed` hoặc `pending`
   - User chỉ có thể hủy đơn hàng của chính mình
   - Đơn hàng đã `shipping` hoặc `completed` không thể hủy

3. **Xem đơn hàng:**
   - User chỉ có thể xem đơn hàng của chính mình
   - Admin có thể xem tất cả đơn hàng

### Rate Limiting (Khuyến nghị)
- POST `/orders`: Tối đa 10 requests/phút/user
- GET `/orders`: Tối đa 60 requests/phút/user
- GET `/orders/{orderId}`: Tối đa 60 requests/phút/user
- PATCH `/orders/{orderId}/status`: Tối đa 5 requests/phút/user

### Business Logic

1. **Khi tạo đơn hàng:**
   - Tự động trừ số lượng tồn kho của sản phẩm
   - Tính toán phí vận chuyển dựa trên địa chỉ
   - Áp dụng voucher nếu có và hợp lệ
   - Tạo mã đơn hàng tự động (format: `ORD-XXXXXX`, ví dụ: `ORD-000003`)
   - Lưu `product_name` và `product_image` vào order để đảm bảo hiển thị đúng ngay cả khi sản phẩm thay đổi
   - Tính `total` cho mỗi item (quantity * price)
   - Tính `subtotal` (tổng của tất cả items)
   - Tính `total_price` = subtotal + shipping_fee - discount + vat
   - Set `payment_status` = `"pending"` mặc định

2. **Khi hủy đơn hàng:**
   - Hoàn lại số lượng tồn kho
   - Cập nhật `status` = `"cancelled"`
   - Cập nhật `updated_at` timestamp
   - Gửi thông báo hủy đơn hàng (nếu có hệ thống notification)

3. **Trạng thái đơn hàng:**
   - `placed` → `pending` → `shipping` → `completed`
   - Có thể chuyển từ `placed` hoặc `pending` → `cancelled`
   - Không thể quay lại trạng thái trước đó

---

## Ví dụ sử dụng với cURL

### 1. Tạo đơn hàng
```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "address_id": "692516a1cfd56b7be11c3c8b",
    "payment_method": "cod",
    "voucher_id": "69250383af4128ac9bd4cf6d",
    "notes": "Giao hàng vào buổi sáng"
  }'
```

**Response mẫu:**
```json
{
  "order": {
    "_id": "69251b01ce7854d9b6553798",
    "order_number": "ORD-000003",
    "user": "690ca89b7e4cdb6f3a594d33",
    "address": "692516a1cfd56b7be11c3c8b",
    "items": [...],
    "subtotal": 3407810.0,
    "shipping_fee": 30000.0,
    "discount": 0.5,
    "vat": 0.0,
    "total_price": 3437809.5,
    "voucher": "69250383af4128ac9bd4cf6d",
    "payment_method": "cod",
    "payment_status": "pending",
    "status": "pending",
    "created_at": "2025-01-25T10:30:00.000Z"
  }
}
```

### 2. Lấy danh sách đơn hàng
```bash
curl -X GET "http://localhost:8000/api/orders?status=pending&page=1&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 3. Lấy chi tiết đơn hàng
```bash
curl -X GET http://localhost:8000/api/orders/69251b01ce7854d9b6553798 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Hoặc dùng order_number:**
```bash
curl -X GET http://localhost:8000/api/orders/ORD-000003 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 4. Hủy đơn hàng
```bash
curl -X PATCH http://localhost:8000/api/orders/69251b01ce7854d9b6553798/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "cancelled"
  }'
```

---

## Ghi chú

1. **Voucher:** Hiện tại backend chỉ hỗ trợ 1 voucher mỗi đơn hàng. `voucher` trong order là ObjectId reference, không phải object đầy đủ.

2. **Address:** `address` trong order là ObjectId reference, không phải object đầy đủ. Frontend cần gọi API riêng để lấy thông tin chi tiết địa chỉ nếu cần.

3. **Product Information:** `product_name` và `product_image` được lưu trực tiếp trong order để đảm bảo hiển thị đúng ngay cả khi sản phẩm đã bị xóa hoặc thay đổi. `product_id` là ObjectId reference.

4. **Pagination:** Nếu có pagination, response sẽ có thêm object `pagination` với các trường: `page`, `limit`, `total`, `totalPages`.

5. **Date Format:** Tất cả các trường date/time đều sử dụng ISO 8601 format (UTC): `"2025-01-25T10:30:00.000Z"`

6. **Price Format:** Tất cả giá tiền đều tính bằng VNĐ và là số thực (double), ví dụ: `3407810.0`, `30000.0`, `0.5`.

7. **Image URLs:** Các URL ảnh có thể là absolute URL (ví dụ: `https://shoeshop.blob.core.windows.net/media/products/...`) hoặc relative path. Frontend sẽ tự động xử lý để hiển thị đúng.

8. **Field Naming:** Tất cả các trường đều sử dụng snake_case (ví dụ: `order_number`, `shipping_fee`, `total_price`, `created_at`) thay vì camelCase.

9. **Payment Status:** `payment_status` có thể là `"pending"`, `"paid"`, `"failed"`, hoặc `"refunded"`. Mặc định khi tạo đơn hàng là `"pending"`.

10. **VAT:** Trường `vat` hiện tại có thể là `0.0` nếu chưa tính thuế VAT. Có thể được cập nhật sau khi tính toán.

11. **Order Number Format:** Mã đơn hàng có format `ORD-XXXXXX` (6 chữ số), ví dụ: `ORD-000003`.

12. **Công thức tính giá:**
    - `total` (của mỗi item) = `quantity * price`
    - `subtotal` = Tổng của tất cả `total` của các items
    - `total_price` = `subtotal + shipping_fee - discount + vat`
    - Ví dụ: `3437809.5 = 3407810.0 + 30000.0 - 0.5 + 0.0`

13. **Discount:** `discount` là số tiền giảm giá (double), có thể là số nhỏ (ví dụ: 0.5) hoặc số lớn tùy theo voucher/promotion được áp dụng.

