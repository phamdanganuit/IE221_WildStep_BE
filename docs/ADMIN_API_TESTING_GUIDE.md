# Hướng dẫn Testing Admin APIs

## Mục lục
1. [Chuẩn bị](#chuẩn-bị)
2. [Authentication](#authentication)
3. [Testing với Postman](#testing-với-postman)
4. [Testing với cURL](#testing-với-curl)
5. [Test từng API](#test-từng-api)
6. [Troubleshooting](#troubleshooting)

---

## Chuẩn bị

### 1. Khởi động server
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# hoặc
source venv/bin/activate      # Linux/Mac

# Run server
python manage.py runserver
```

Server sẽ chạy tại: `http://localhost:8000`

### 2. Tạo Admin Account

**Cách 1: Qua API Register với admin_key**
```bash
POST http://localhost:8000/api/register
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin123456",
  "displayName": "Admin User",
  "admin_key": "<ADMIN_SIGNUP_KEY từ .env>"
}
```

**Cách 2: Tạo trực tiếp trong MongoDB**
```javascript
db.users.insertOne({
  email: "admin@example.com",
  password_hash: "<hashed_password>",
  role: "admin",
  displayName: "Admin User"
})
```

### 3. Lấy Access Token
```bash
POST http://localhost:8000/api/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

**Lưu token này để dùng cho tất cả requests tiếp theo!**

---

## Authentication

Tất cả Admin APIs yêu cầu Bearer token trong header:

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Lưu ý:** User phải có `role: "admin"` trong JWT token.

---

## Testing với Postman

### 1. Setup Environment

Tạo Environment trong Postman với các variables:
- `base_url`: `http://localhost:8000`
- `token`: `<access_token từ login>`

### 2. Setup Authorization

Trong Postman:
1. Vào tab **Authorization**
2. Chọn Type: **Bearer Token**
3. Paste token vào **Token** field

Hoặc thêm vào Header:
```
Authorization: Bearer {{token}}
```

### 3. Tạo Collection

Tạo collection **"Admin APIs"** và organize theo nhóm:
- Dashboard & Analytics
- Products
- Brands
- Categories
- Orders
- Customers

---

## Testing với cURL

### Setup token variable (PowerShell)
```powershell
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
$BASE_URL = "http://localhost:8000"
```

### Setup token variable (Bash)
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
export BASE_URL="http://localhost:8000"
```

---

## Test từng API

### 🏠 1. Dashboard & Analytics

#### GET Dashboard Stats
```bash
# cURL
curl -X GET "$BASE_URL/api/admin/dashboard/stats?period=month" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Postman
GET {{base_url}}/api/admin/dashboard/stats?period=month
```

**Response:**
```json
{
  "summary": {
    "totalRevenue": 125450000,
    "revenueChange": 12.5,
    "totalOrders": 1234,
    "ordersChange": 8.2,
    "totalCustomers": 8549,
    "customersChange": 15.3,
    "totalProducts": 456,
    "productsChange": -2.1
  },
  "recentOrders": [...],
  "revenueChart": [...],
  "categoryDistribution": [...]
}
```

#### GET Analytics
```bash
curl -X GET "$BASE_URL/api/admin/analytics?period=month" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 📦 2. Products Management

#### GET Products List
```bash
curl -X GET "$BASE_URL/api/admin/products" \
  -H "Authorization: Bearer $TOKEN"
```

#### POST Create Product
```bash
curl -X POST "$BASE_URL/api/admin/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nike Air Max 270",
    "categoryId": "<child_category_id>",
    "brandId": "<brand_id>",
    "price": 3500000,
    "description": "Giày thể thao cao cấp",
    "stock": 45,
    "discount": 10,
    "status": "active",
    "images": [
      "/media/products/nike-air-max-270-1.jpg"
    ],
    "specifications": {
      "size": ["38", "39", "40", "41", "42"],
      "color": ["Đen", "Trắng", "Xám"],
      "material": "Da tổng hợp",
      "weight": "300g"
    },
    "tags": ["nike", "sports", "running"]
  }'
```

**Response (201):**
```json
{
  "id": "60d5ec49f1b2c72b8c8e4f3c",
  "name": "Nike Air Max 270",
  "slug": "nike-air-max-270",
  "description": "Giày thể thao cao cấp",
  "price": 3500000,
  "discountPrice": 3150000,
  "stock": 45,
  "status": "active",
  "images": ["/media/products/nike-air-max-270-1.jpg"],
  "createdAt": "2025-11-01T10:00:00Z"
}
```

#### GET Product Detail
```bash
curl -X GET "$BASE_URL/api/admin/products/<product_id>" \
  -H "Authorization: Bearer $TOKEN"
```

#### PUT Update Product
```bash
curl -X PUT "$BASE_URL/api/admin/products/<product_id>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock": 50,
    "discount": 15,
    "status": "active"
  }'
```

#### DELETE Product
```bash
curl -X DELETE "$BASE_URL/api/admin/products/<product_id>" \
  -H "Authorization: Bearer $TOKEN"
```

#### POST Upload Product Images
```bash
# cURL (multipart/form-data)
curl -X POST "$BASE_URL/api/admin/products/<product_id>/images" \
  -H "Authorization: Bearer $TOKEN" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg"

# Postman
# Method: POST
# Body > form-data
# Key: images (type: File), Value: [chọn file]
# Có thể thêm nhiều images (max 5)
```

**Response:**
```json
{
  "images": [
    "/media/products/product_id_abc123.jpg",
    "/media/products/product_id_def456.jpg"
  ]
}
```

---

### 🏷️ 3. Brands Management

#### GET Brands List
```bash
curl -X GET "$BASE_URL/api/admin/brands" \
  -H "Authorization: Bearer $TOKEN"
```

#### POST Create Brand
```bash
curl -X POST "$BASE_URL/api/admin/brands" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nike",
    "description": "Thương hiệu thể thao hàng đầu",
    "website": "https://www.nike.com",
    "country": "USA",
    "status": "active"
  }'
```

**Response (201):**
```json
{
  "id": "60d5ec49f1b2c72b8c8e4f2b",
  "name": "Nike",
  "slug": "nike",
  "description": "Thương hiệu thể thao hàng đầu",
  "logo": null,
  "website": "https://www.nike.com",
  "country": "USA",
  "status": "active",
  "createdAt": "2025-11-01T10:00:00Z",
  "updatedAt": "2025-11-01T10:00:00Z"
}
```

#### GET Brand Detail
```bash
curl -X GET "$BASE_URL/api/admin/brands/<brand_id>" \
  -H "Authorization: Bearer $TOKEN"
```

#### PUT Update Brand
```bash
curl -X PUT "$BASE_URL/api/admin/brands/<brand_id>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "status": "inactive"
  }'
```

#### DELETE Brand
```bash
curl -X DELETE "$BASE_URL/api/admin/brands/<brand_id>" \
  -H "Authorization: Bearer $TOKEN"
```

**Lưu ý:** Không thể xóa brand nếu có products đang sử dụng.

---

### 📁 4. Categories Management

#### GET Categories List
```bash
curl -X GET "$BASE_URL/api/admin/categories" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:** Trả về hierarchical structure (parent với children)

#### POST Create Parent Category
```bash
curl -X POST "$BASE_URL/api/admin/categories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Giày thể thao",
    "type": "parent",
    "description": "Danh mục giày thể thao",
    "status": "active"
  }'
```

#### POST Create Child Category
```bash
curl -X POST "$BASE_URL/api/admin/categories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Giày chạy bộ",
    "type": "child",
    "parentId": "<parent_category_id>",
    "description": "Giày dành cho chạy bộ",
    "status": "active"
  }'
```

---

### 🛒 5. Orders Management

#### GET Orders List
```bash
curl -X GET "$BASE_URL/api/admin/orders" \
  -H "Authorization: Bearer $TOKEN"
```

#### GET Order Detail
```bash
curl -X GET "$BASE_URL/api/admin/orders/<order_id>" \
  -H "Authorization: Bearer $TOKEN"
```

#### PATCH Update Order Status
```bash
curl -X PATCH "$BASE_URL/api/admin/orders/<order_id>/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "processing"
  }'
```

**Status transitions:**
- `pending` → `processing` → `shipping` → `completed` ✅
- Không thể đổi từ `completed` hoặc `cancelled` ❌

---

### 👥 6. Customers Management

#### GET Customers List
```bash
curl -X GET "$BASE_URL/api/admin/customers" \
  -H "Authorization: Bearer $TOKEN"
```

**Response includes:**
- `totalOrders`, `totalSpent`, `averageOrderValue`
- `isVip`: true if totalOrders > 10
- `status`: `blocked` | `vip` | `active` | `inactive`

#### GET Customer Detail
```bash
curl -X GET "$BASE_URL/api/admin/customers/<customer_id>" \
  -H "Authorization: Bearer $TOKEN"
```

**Response includes:**
- Full customer info
- Recent orders (last 10)
- Order history statistics
- Addresses

#### PATCH Update Customer Status (Block/Unblock)
```bash
curl -X PATCH "$BASE_URL/api/admin/customers/<customer_id>/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "blocked"
  }'
```

**Lưu ý:** Chỉ có thể set `blocked` manually. `vip`, `active`, `inactive` được tính tự động.

---

## Test Flow Hoàn Chỉnh

### Scenario 1: Tạo Brand → Category → Product

```bash
# 1. Tạo Brand
BRAND_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/brands" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Adidas",
    "description": "Adidas brand",
    "country": "Germany"
  }')
BRAND_ID=$(echo $BRAND_RESPONSE | jq -r '.id')

# 2. Tạo Parent Category
PARENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/categories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Giày thể thao",
    "type": "parent"
  }')
PARENT_ID=$(echo $PARENT_RESPONSE | jq -r '.id')

# 3. Tạo Child Category
CHILD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/categories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Giày chạy bộ\",
    \"type\": \"child\",
    \"parentId\": \"$PARENT_ID\"
  }")
CHILD_ID=$(echo $CHILD_RESPONSE | jq -r '.id')

# 4. Tạo Product
curl -X POST "$BASE_URL/api/admin/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Adidas Ultraboost 22\",
    \"categoryId\": \"$CHILD_ID\",
    \"brandId\": \"$BRAND_ID\",
    \"price\": 4200000,
    \"stock\": 30,
    \"description\": \"Giày chạy bộ Adidas\"
  }"
```

### Scenario 2: Upload Images cho Product

```bash
# 1. Tạo product (như trên)
PRODUCT_ID="<product_id>"

# 2. Upload images
curl -X POST "$BASE_URL/api/admin/products/$PRODUCT_ID/images" \
  -H "Authorization: Bearer $TOKEN" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg"
```

### Scenario 3: Test Customer Status Logic

1. Tạo user và orders để test:
   - `< 10 orders` → không phải VIP
   - `> 10 orders` → VIP
   - Có order trong 30 ngày → `active`
   - Không có order trong 30 ngày → `inactive`

---

## Troubleshooting

### Lỗi 401 Unauthorized
**Nguyên nhân:**
- Token hết hạn hoặc không hợp lệ
- Thiếu header Authorization

**Giải pháp:**
```bash
# Login lại để lấy token mới
curl -X POST "$BASE_URL/api/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123456"
  }'
```

### Lỗi 403 Forbidden
**Nguyên nhân:**
- User không có role `admin`

**Giải pháp:**
- Kiểm tra user có `role: "admin"` trong MongoDB
- Hoặc đăng ký lại với `admin_key`

### Lỗi 404 Not Found
**Nguyên nhân:**
- ObjectId không tồn tại
- URL sai

**Giải pháp:**
- Kiểm tra ObjectId format (24 ký tự hex)
- Verify resource tồn tại trong database

### Lỗi 400 Bad Request
**Nguyên nhân:**
- Thiếu required fields
- Invalid data format
- Business logic error (VD: xóa brand có products)

**Giải pháp:**
- Kiểm tra request body đầy đủ
- Xem error message chi tiết trong response

### Lỗi khi upload images
**Nguyên nhân:**
- File quá lớn (>5MB)
- File type không hợp lệ
- Storage không config đúng

**Giải pháp:**
- Kiểm tra file size và type
- Verify Azure Storage config (nếu dùng)
- Hoặc dùng local storage

---

## Test Checklist

### Products APIs
- [ ] GET products list
- [ ] POST create product (với images URLs)
- [ ] GET product detail
- [ ] PUT update product
- [ ] POST upload product images (files)
- [ ] DELETE product

### Brands APIs
- [ ] GET brands list
- [ ] POST create brand
- [ ] GET brand detail
- [ ] PUT update brand
- [ ] DELETE brand (test với/không có products)

### Categories APIs
- [ ] GET categories list
- [ ] POST create parent category
- [ ] POST create child category
- [ ] Verify hierarchical structure

### Orders APIs
- [ ] GET orders list
- [ ] GET order detail
- [ ] PATCH update status (test valid transitions)
- [ ] Test invalid transitions (completed → pending)

### Customers APIs
- [ ] GET customers list
- [ ] GET customer detail
- [ ] Verify auto-calculated: isVip, status
- [ ] PATCH block/unblock customer

### Dashboard & Analytics
- [ ] GET dashboard stats (với các periods khác nhau)
- [ ] GET analytics
- [ ] Verify calculated metrics

---

## Tips

1. **Sử dụng Postman Variables:**
   - Lưu `token`, `product_id`, `brand_id` trong variables
   - Dùng `{{variable}}` trong requests

2. **Test Error Cases:**
   - Invalid ObjectId
   - Missing required fields
   - Invalid status transitions
   - Delete resource with dependencies

3. **Verify Data:**
   - Check MongoDB sau mỗi operation
   - Verify auto-generated fields (slug, order_number, etc.)
   - Verify calculated fields (discount_price, status, isVip)

4. **Performance Testing:**
   - Test với large datasets
   - Test pagination
   - Monitor response times

---

## Resources

- **API Specification**: `docs/ADMIN_API_SPEC.md`
- **Implementation Details**: `docs/ADMIN_API_IMPLEMENTATION.md`
- **Base URL**: `http://localhost:8000/api/admin`

---

**Happy Testing! 🚀**

