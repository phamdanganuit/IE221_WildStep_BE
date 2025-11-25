# API Vouchers - Thiết kế Endpoints

## Tổng quan

Tài liệu này mô tả thiết kế API endpoints cho quản lý vouchers (mã giảm giá) cho cả Admin và User.

## Cấu trúc dữ liệu Voucher

```json
{
  "_id": "ObjectId",
  "name": "string (required)",
  "code": "string (required, unique, indexed)",
  "description": "string",
  "discount": "number (required, min: 0)",
  "min_value": "number (default: 0)",
  "start_date": "datetime (ISO 8601)",
  "expired_date": "datetime (ISO 8601)",
  "categories": ["ObjectId[]"] // Danh sách childCategory IDs
}
```

### Lưu ý:
- `discount`: Có thể là số tiền cố định (VD: 29900) hoặc phần trăm (VD: 0.1 = 10%)
- `min_value`: Giá trị đơn hàng tối thiểu để áp dụng voucher
- `categories`: Mảng ObjectId tham chiếu đến childCategory. Nếu rỗng `[]`, voucher áp dụng cho vận chuyển
- `code`: Phải unique và có index để tìm kiếm nhanh

---

## Admin Endpoints

Base URL: `/api/admin/vouchers`

### 1. GET `/api/admin/vouchers` - Lấy danh sách vouchers

**Mục đích:** Admin xem tất cả vouchers trong hệ thống

**Query Parameters:**
- `page` (optional): Số trang (default: 1)
- `page_size` (optional): Số lượng mỗi trang (default: 20)
- `search` (optional): Tìm kiếm theo tên hoặc code
- `status` (optional): Lọc theo trạng thái (`active`, `expired`, `upcoming`)

**Response 200:**
```json
{
  "data": [
    {
      "_id": "voucher_id",
      "name": "Giảm 29.900đ cho đơn hàng đầu tiên",
      "code": "WILDSTEPWELCOME",
      "description": "Giảm 29.900đ cho đơn hàng đầu tiên",
      "discount": 29900,
      "min_value": 0,
      "start_date": "2025-01-01T00:00:00.000Z",
      "expired_date": "2025-12-31T23:59:59.000Z",
      "categories": ["category_id_1", "category_id_2"]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

---

### 2. GET `/api/admin/vouchers/:id` - Lấy chi tiết voucher

**Mục đích:** Admin xem thông tin chi tiết một voucher

**Response 200:**
```json
{
  "_id": "voucher_id",
  "name": "Giảm 29.900đ cho đơn hàng đầu tiên",
  "code": "WILDSTEPWELCOME",
  "description": "Giảm 29.900đ cho đơn hàng đầu tiên",
  "discount": 29900,
  "min_value": 0,
  "start_date": "2025-01-01T00:00:00.000Z",
  "expired_date": "2025-12-31T23:59:59.000Z",
  "categories": [
    {
      "_id": "category_id_1",
      "name": { "vi": "Giày nữ", "en": "Women Shoes" },
      "slug": "giay-nu"
    }
  ],
  "createdAt": "2025-01-01T00:00:00.000Z",
  "updatedAt": "2025-01-01T00:00:00.000Z"
}
```

---

### 3. POST `/api/admin/vouchers` - Tạo voucher mới

**Mục đích:** Admin tạo voucher mới

**Request Body:**
```json
{
  "name": "Giảm 29.900đ cho đơn hàng đầu tiên",
  "code": "WILDSTEPWELCOME",
  "description": "Giảm 29.900đ cho đơn hàng đầu tiên. - Áp dụng cho tất cả sản phẩm.",
  "discount": 29900,
  "min_value": 0,
  "start_date": "2025-01-01T00:00:00.000Z",
  "expired_date": "2025-12-31T23:59:59.000Z",
  "categories": ["category_id_1", "category_id_2"] // Optional, rỗng [] = voucher vận chuyển
}
```

**Validation:**
- `name`: Required, string
- `code`: Required, string, unique, uppercase
- `discount`: Required, number >= 0
- `min_value`: Optional, number >= 0 (default: 0)
- `start_date`: Required, datetime
- `expired_date`: Required, datetime, must be after start_date
- `categories`: Optional, array of ObjectId (childCategory IDs)

**Response 201:**
```json
{
  "_id": "voucher_id",
  "name": "Giảm 29.900đ cho đơn hàng đầu tiên",
  "code": "WILDSTEPWELCOME",
  "description": "Giảm 29.900đ cho đơn hàng đầu tiên",
  "discount": 29900,
  "min_value": 0,
  "start_date": "2025-01-01T00:00:00.000Z",
  "expired_date": "2025-12-31T23:59:59.000Z",
  "categories": ["category_id_1", "category_id_2"],
  "createdAt": "2025-01-01T00:00:00.000Z",
  "updatedAt": "2025-01-01T00:00:00.000Z"
}
```

**Error Responses:**
- `400`: Validation error (thiếu trường bắt buộc, code đã tồn tại, expired_date < start_date)
- `409`: Code đã tồn tại

---

### 4. PUT `/api/admin/vouchers/:id` - Cập nhật voucher

**Mục đích:** Admin cập nhật thông tin voucher

**Request Body:** (Tương tự POST, tất cả fields optional)

```json
{
  "name": "Giảm 30.000đ cho đơn hàng đầu tiên",
  "description": "Mô tả mới",
  "discount": 30000,
  "min_value": 50000,
  "start_date": "2025-01-01T00:00:00.000Z",
  "expired_date": "2025-12-31T23:59:59.000Z",
  "categories": ["category_id_1"]
}
```

**Response 200:**
```json
{
  "_id": "voucher_id",
  "name": "Giảm 30.000đ cho đơn hàng đầu tiên",
  "code": "WILDSTEPWELCOME",
  "description": "Mô tả mới",
  "discount": 30000,
  "min_value": 50000,
  "start_date": "2025-01-01T00:00:00.000Z",
  "expired_date": "2025-12-31T23:59:59.000Z",
  "categories": ["category_id_1"],
  "updatedAt": "2025-01-15T10:30:00.000Z"
}
```

**Error Responses:**
- `404`: Voucher không tồn tại
- `400`: Validation error
- `409`: Code đã tồn tại (nếu thay đổi code)

---

### 5. DELETE `/api/admin/vouchers/:id` - Xóa voucher

**Mục đích:** Admin xóa voucher

**Response 204:** No Content

**Error Responses:**
- `404`: Voucher không tồn tại
- `400`: Không thể xóa voucher đang được sử dụng (nếu có logic này)

---

## User Endpoints

Base URL: `/api/vouchers` (không có `/admin`)

### 1. GET `/api/vouchers` - Lấy danh sách vouchers của user

**Mục đích:** User xem danh sách vouchers đã thêm vào tài khoản

**Auth:** Required (Bearer token)

**Query Parameters:**
- `status` (optional): `active`, `expired`, `used`

**Response 200:**
```json
{
  "data": [
    {
      "_id": "voucher_id",
      "name": "Giảm 29.900đ cho đơn hàng đầu tiên",
      "code": "WILDSTEPWELCOME",
      "description": "Giảm 29.900đ cho đơn hàng đầu tiên",
      "discount": 29900,
      "min_value": 0,
      "start_date": "2025-01-01T00:00:00.000Z",
      "expired_date": "2025-12-31T23:59:59.000Z",
      "categories": ["category_id_1", "category_id_2"],
      "addedAt": "2025-01-10T00:00:00.000Z" // Ngày user thêm voucher
    }
  ]
}
```

---

### 2. POST `/api/addVoucher` - Thêm voucher vào danh sách của user

**Mục đích:** User thêm voucher vào tài khoản bằng mã code

**Auth:** Required (Bearer token)

**Request Body:**
```json
{
  "code": "WILDSTEPWELCOME"
}
```

**Response 200:**
```json
{
  "_id": "user_voucher_id",
  "voucher": {
    "_id": "voucher_id",
    "name": "Giảm 29.900đ cho đơn hàng đầu tiên",
    "code": "WILDSTEPWELCOME",
    "description": "Giảm 29.900đ cho đơn hàng đầu tiên",
    "discount": 29900,
    "min_value": 0,
    "start_date": "2025-01-01T00:00:00.000Z",
    "expired_date": "2025-12-31T23:59:59.000Z",
    "categories": ["category_id_1", "category_id_2"]
  },
  "addedAt": "2025-01-10T00:00:00.000Z"
}
```

**Error Responses:**
- `400`: Mã voucher không hợp lệ hoặc đã hết hạn
- `401`: Token không hợp lệ
- `409`: Voucher đã được thêm vào tài khoản

**Logic kiểm tra:**
1. Tìm voucher theo code
2. Kiểm tra voucher còn hiệu lực (start_date <= now <= expired_date)
3. Kiểm tra user chưa thêm voucher này
4. Thêm vào bảng user_vouchers (hoặc tương đương)

---

### 3. DELETE `/api/removeVoucher` - Xóa voucher khỏi danh sách của user

**Mục đích:** User xóa voucher khỏi tài khoản

**Auth:** Required (Bearer token)

**Request Body:**
```json
{
  "voucherId": "voucher_id"
}
```

**Response 200:**
```json
{
  "message": "Xóa mã giảm giá thành công!"
}
```

**Error Responses:**
- `404`: Voucher không tồn tại trong danh sách của user
- `401`: Token không hợp lệ

---

## Database Schema (Tham khảo)

### Collection: `vouchers`
```javascript
{
  _id: ObjectId,
  name: String (required),
  code: String (required, unique, indexed),
  description: String,
  discount: Number (required, min: 0),
  min_value: Number (default: 0),
  start_date: Date,
  expired_date: Date,
  categories: [ObjectId], // References to childCategory
  createdAt: Date,
  updatedAt: Date
}
```

### Collection: `user_vouchers` (hoặc tương đương)
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  voucher_id: ObjectId (ref: vouchers),
  addedAt: Date,
  usedAt: Date, // Optional, nếu cần track
  status: String // "active", "used", "expired"
}
```

---

## Ví dụ sử dụng

### Admin tạo voucher mới:
```http
POST /api/admin/vouchers
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "name": "Giảm 10% tối đa 50k cho đơn từ 300k",
  "code": "SAVE10",
  "description": "Giảm 10% tối đa 50.000đ. - Áp dụng cho đơn từ 300k.",
  "discount": 0.1,
  "min_value": 300000,
  "start_date": "2025-01-01T00:00:00.000Z",
  "expired_date": "2025-12-31T23:59:59.000Z",
  "categories": ["category_id_1"]
}
```

### User thêm voucher:
```http
POST /api/addVoucher
Authorization: Bearer {user_token}
Content-Type: application/json

{
  "code": "SAVE10"
}
```

---

## Lưu ý quan trọng

1. **Code uniqueness**: Code phải unique trong toàn hệ thống
2. **Date validation**: `expired_date` phải sau `start_date`
3. **Categories**: 
   - Nếu `categories = []`: Voucher áp dụng cho vận chuyển
   - Nếu `categories = [id1, id2, ...]`: Voucher áp dụng cho các danh mục cụ thể
4. **Discount format**:
   - Số tiền cố định: `29900` (đồng)
   - Phần trăm: `0.1` (10%), `0.2` (20%)
5. **User voucher tracking**: Cần lưu thông tin user nào đã thêm voucher nào để tránh duplicate

