# Hướng dẫn Testing Admin APIs với Postman

## Mục lục
1. [Chuẩn bị](#chuẩn-bị)
2. [Setup Postman](#setup-postman)
3. [Authentication](#authentication)
4. [Test từng API](#test-từng-api)
5. [Test Scenarios](#test-scenarios)
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

### Bước 1: Login để lấy Token

1. Tạo request mới trong folder **"1. Authentication"**
2. **Method**: `POST`
3. **URL**: `{{base_url}}/api/login`
4. **Body** (tab Body > raw > JSON):
```json
{
  "email": "admin@example.com",
  "password": "admin123456"
}
```
5. Click **Send**
6. Copy `access_token` từ response
7. Vào **Environment** > Paste token vào variable `token` > **Save**

### Bước 2: Verify Token

Tất cả requests trong collection sẽ tự động dùng `{{token}}` từ environment.

**Lưu ý:** 
- User phải có `role: "admin"` trong JWT token
- Token có thể hết hạn → login lại để lấy token mới

---

## Setup Postman

### 1. Tạo Environment

1. Click **Environments** (icon bên trái) > **+** để tạo mới
2. Đặt tên: **"Shoe Shop Admin"**
3. Thêm các variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` |
| `token` | (để trống) | (sẽ set sau khi login) |
| `product_id` | (để trống) | (sẽ set sau khi tạo product) |
| `brand_id` | (để trống) | (sẽ set sau khi tạo brand) |
| `category_id` | (để trống) | (sẽ set sau khi tạo category) |
| `order_id` | (để trống) | (sẽ set sau khi tạo order) |
| `customer_id` | (để trống) | (sẽ set sau khi tạo customer) |

4. Click **Save**

### 2. Tạo Collection

1. Click **New** > **Collection**
2. Đặt tên: **"Admin APIs - Shoe Shop"**
3. Tạo folders để organize:
   - **1. Authentication**
   - **2. Dashboard & Analytics**
   - **3. Products**
   - **4. Brands**
   - **5. Categories**
   - **6. Orders**
   - **7. Customers**

### 3. Setup Collection Authorization

1. Vào **Collection** > Tab **Authorization**
2. Type: **Bearer Token**
3. Token: `{{token}}`
4. Click **Save**

→ Tất cả requests trong collection sẽ tự động dùng token này!

### 4. Setup Collection Variables

Vào **Collection** > Tab **Variables**:
- Thêm `base_url`: `http://localhost:8000`

---

## Test từng API

### 🏠 1. Dashboard & Analytics

#### GET Dashboard Stats

**Postman Setup:**
1. Tạo request trong folder **"2. Dashboard & Analytics"**
2. **Method**: `GET`
3. **URL**: `{{base_url}}/api/admin/dashboard/stats`
4. **Params** (tab Params):
   - Key: `period`, Value: `month` (có thể chọn: `week`, `month`, `year`)
5. Click **Send**

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

**Postman Setup:**
1. **Method**: `GET`
2. **URL**: `{{base_url}}/api/admin/analytics`
3. **Params**: `period=month` (optional)
4. Click **Send**

---

### 📦 2. Products Management

#### GET Products List

**Postman Setup:**
1. Tạo request trong folder **"3. Products"**
2. **Method**: `GET`
3. **URL**: `{{base_url}}/api/admin/products`
4. Click **Send**

#### POST Create Product

**Postman Setup:**
1. **Method**: `POST`
2. **URL**: `{{base_url}}/api/admin/products`
3. **Body** (tab Body > raw > JSON):
```json
{
  "name": "Nike Air Max 270",
  "categoryId": "{{category_id}}",
  "brandId": "{{brand_id}}",
  "price": 3500000,
  "description": "Giày thể thao cao cấp Nike Air Max 270 với công nghệ Air Max",
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
}
```
4. Click **Send**
5. **Lưu product_id**: Copy `id` từ response > Vào Environment > Set `product_id` > Save

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

**Postman Setup:**
1. **Method**: `GET`
2. **URL**: `{{base_url}}/api/admin/products/{{product_id}}`
3. Click **Send**

#### PUT Update Product

**Postman Setup:**
1. **Method**: `PUT`
2. **URL**: `{{base_url}}/api/admin/products/{{product_id}}`
3. **Body** (raw > JSON):
```json
{
  "stock": 50,
  "discount": 15,
  "status": "active",
  "description": "Updated description"
}
```
4. Click **Send**

#### DELETE Product

**Postman Setup:**
1. **Method**: `DELETE`
2. **URL**: `{{base_url}}/api/admin/products/{{product_id}}`
3. Click **Send**

#### POST Upload Product Images

**Postman Setup:**
1. **Method**: `POST`
2. **URL**: `{{base_url}}/api/admin/products/{{product_id}}/images`
3. **Body** (tab Body > form-data):
   - Key: `images` (type: **File**), Value: [Browse file 1]
   - Key: `images` (type: **File**), Value: [Browse file 2]
   - ... (tối đa 5 files)
4. **Lưu ý**: 
   - File type: JPEG, PNG, WebP
   - File size: Max 5MB mỗi file
   - Max 5 files mỗi lần upload
5. Click **Send**

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

**Postman Setup:**
1. Tạo request trong folder **"4. Brands"**
2. **Method**: `GET`
3. **URL**: `{{base_url}}/api/admin/brands`
4. Click **Send**

#### POST Create Brand

**Postman Setup:**
1. **Method**: `POST`
2. **URL**: `{{base_url}}/api/admin/brands`
3. **Body** (raw > JSON):
```json
{
  "name": "Nike",
  "description": "Thương hiệu thể thao hàng đầu thế giới",
  "website": "https://www.nike.com",
  "country": "USA",
  "status": "active"
}
```
4. Click **Send**
5. **Lưu brand_id**: Copy `id` từ response > Set vào environment variable `brand_id`

#### GET Brand Detail

**Postman Setup:**
1. **Method**: `GET`
2. **URL**: `{{base_url}}/api/admin/brands/{{brand_id}}`
3. Click **Send**

#### PUT Update Brand

**Postman Setup:**
1. **Method**: `PUT`
2. **URL**: `{{base_url}}/api/admin/brands/{{brand_id}}`
3. **Body** (raw > JSON):
```json
{
  "description": "Updated description",
  "status": "inactive"
}
```
4. Click **Send**

#### DELETE Brand

**Postman Setup:**
1. **Method**: `DELETE`
2. **URL**: `{{base_url}}/api/admin/brands/{{brand_id}}`
3. Click **Send**

**Lưu ý:** Không thể xóa brand nếu có products đang sử dụng.

---

### 📁 4. Categories Management

#### GET Categories List

**Postman Setup:**
1. Tạo request trong folder **"5. Categories"**
2. **Method**: `GET`
3. **URL**: `{{base_url}}/api/admin/categories`
4. Click **Send**

**Response:** Trả về hierarchical structure (parent với children)

#### POST Create Parent Category

**Postman Setup:**
1. **Method**: `POST`
2. **URL**: `{{base_url}}/api/admin/categories`
3. **Body** (raw > JSON):
```json
{
  "name": "Giày thể thao",
  "type": "parent",
  "description": "Danh mục giày thể thao",
  "status": "active"
}
```
4. Click **Send**
5. **Lưu parent_category_id**: Copy `id` từ response

#### POST Create Child Category

**Postman Setup:**
1. **Method**: `POST`
2. **URL**: `{{base_url}}/api/admin/categories`
3. **Body** (raw > JSON):
```json
{
  "name": "Giày chạy bộ",
  "type": "child",
  "parentId": "<parent_category_id>",
  "description": "Giày dành cho chạy bộ",
  "status": "active"
}
```
4. Click **Send**
5. **Lưu category_id**: Copy `id` từ response > Set vào environment variable `category_id`

---

### 🛒 5. Orders Management

#### GET Orders List

**Postman Setup:**
1. Tạo request trong folder **"6. Orders"**
2. **Method**: `GET`
3. **URL**: `{{base_url}}/api/admin/orders`
4. Click **Send**

#### GET Order Detail

**Postman Setup:**
1. **Method**: `GET`
2. **URL**: `{{base_url}}/api/admin/orders/{{order_id}}`
3. Click **Send**

#### PATCH Update Order Status

**Postman Setup:**
1. **Method**: `PATCH`
2. **URL**: `{{base_url}}/api/admin/orders/{{order_id}}/status`
3. **Body** (raw > JSON):
```json
{
  "status": "processing"
}
```
4. Click **Send**

**Test status transitions:**
- ✅ `pending` → `processing` → `shipping` → `completed`
- ❌ `completed` → `pending` (should fail)

**Status transitions:**
- `pending` → `processing` → `shipping` → `completed` ✅
- Không thể đổi từ `completed` hoặc `cancelled` ❌

---

### 👥 6. Customers Management

#### GET Customers List

**Postman Setup:**
1. Tạo request trong folder **"7. Customers"**
2. **Method**: `GET`
3. **URL**: `{{base_url}}/api/admin/customers`
4. Click **Send**

**Verify trong response:**
- `totalOrders`, `totalSpent`, `averageOrderValue` (auto-calculated)
- `isVip`: `true` nếu totalOrders > 10
- `status`: `blocked` | `vip` | `active` | `inactive` (auto-calculated)

#### GET Customer Detail

**Postman Setup:**
1. **Method**: `GET`
2. **URL**: `{{base_url}}/api/admin/customers/{{customer_id}}`
3. Click **Send**

**Response includes:**
- Full customer info
- Recent orders (last 10)
- Order history statistics
- Addresses

#### PATCH Update Customer Status (Block/Unblock)

**Postman Setup:**
1. **Method**: `PATCH`
2. **URL**: `{{base_url}}/api/admin/customers/{{customer_id}}/status`
3. **Body** (raw > JSON):
```json
{
  "status": "blocked"
}
```
4. Click **Send**

**Lưu ý:** Chỉ có thể set `blocked` manually. `vip`, `active`, `inactive` được tính tự động.

**Lưu ý:** Chỉ có thể set `blocked` manually. `vip`, `active`, `inactive` được tính tự động.

---

## Test Flow Hoàn Chỉnh

### Scenario 1: Tạo Brand → Category → Product

**Workflow trong Postman:**

1. **Tạo Brand**
   - POST `{{base_url}}/api/admin/brands`
   - Body: `{"name": "Adidas", "country": "Germany"}`
   - Copy `id` từ response → Set vào `brand_id` variable

2. **Tạo Parent Category**
   - POST `{{base_url}}/api/admin/categories`
   - Body: `{"name": "Giày thể thao", "type": "parent"}`
   - Copy `id` từ response (lưu tạm)

3. **Tạo Child Category**
   - POST `{{base_url}}/api/admin/categories`
   - Body: `{"name": "Giày chạy bộ", "type": "child", "parentId": "<parent_id>"}`
   - Copy `id` từ response → Set vào `category_id` variable

4. **Tạo Product**
   - POST `{{base_url}}/api/admin/products`
   - Body:
   ```json
   {
     "name": "Adidas Ultraboost 22",
     "categoryId": "{{category_id}}",
     "brandId": "{{brand_id}}",
     "price": 4200000,
     "stock": 30,
     "description": "Giày chạy bộ Adidas"
   }
   ```
   - Copy `id` từ response → Set vào `product_id` variable

### Scenario 2: Upload Images cho Product

**Workflow:**

1. **Tạo Product** (như trên) → Có `product_id`

2. **Upload Images**
   - POST `{{base_url}}/api/admin/products/{{product_id}}/images`
   - Body > form-data:
     - `images`: [File] - chọn image1.jpg
     - `images`: [File] - chọn image2.jpg
   - Send
   - Verify: Response có array `images` với URLs mới

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
1. Login lại trong Postman
2. Copy token mới → Update vào environment variable `token`
3. Save environment

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
1. Kiểm tra trong Postman:
   - File size < 5MB
   - File type: JPEG, PNG, WebP
2. Verify storage config trong `.env` hoặc `settings.py`
3. Check server logs để xem error chi tiết

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

## Tips & Best Practices

### 1. Sử dụng Postman Variables
- **Environment variables**: `{{token}}`, `{{base_url}}`, `{{product_id}}`
- **Collection variables**: Shared cho toàn bộ collection
- **Auto-save IDs**: Sau mỗi POST, copy `id` → Update variable

### 2. Sử dụng Tests Tab trong Postman
**Example Test Script** (sau request Create Product):
```javascript
// Auto-save product_id
if (pm.response.code === 201) {
    var jsonData = pm.response.json();
    pm.environment.set("product_id", jsonData.id);
    pm.test("Product created successfully", function () {
        pm.response.to.have.status(201);
    });
}
```

### 3. Organize Requests
- Sắp xếp theo thứ tự logical (Brand → Category → Product)
- Đặt tên rõ ràng: "GET Products", "POST Create Product"
- Thêm descriptions cho mỗi request

### 4. Test Error Cases
- Invalid ObjectId format
- Missing required fields
- Invalid status transitions
- Delete resource with dependencies
- Invalid file types/sizes

### 5. Verify Data
- Check response structure
- Verify auto-generated fields (slug, order_number, discount_price)
- Verify calculated fields (status, isVip, totalSpent)

### 6. Export/Import Collection
- Export collection để share với team
- Import collection để setup nhanh
- Version control collection JSON

---

## Postman Collection Template

### Suggested Request Structure:

```
📁 Admin APIs - Shoe Shop
├── 📁 1. Authentication
│   └── POST Login
│
├── 📁 2. Dashboard & Analytics
│   ├── GET Dashboard Stats
│   └── GET Analytics
│
├── 📁 3. Products
│   ├── GET Products List
│   ├── POST Create Product
│   ├── GET Product Detail
│   ├── PUT Update Product
│   ├── DELETE Product
│   └── POST Upload Images
│
├── 📁 4. Brands
│   ├── GET Brands List
│   ├── POST Create Brand
│   ├── GET Brand Detail
│   ├── PUT Update Brand
│   └── DELETE Brand
│
├── 📁 5. Categories
│   ├── GET Categories List
│   ├── POST Create Parent Category
│   └── POST Create Child Category
│
├── 📁 6. Orders
│   ├── GET Orders List
│   ├── GET Order Detail
│   └── PATCH Update Status
│
└── 📁 7. Customers
    ├── GET Customers List
    ├── GET Customer Detail
    └── PATCH Update Status
```

## Resources

- **API Specification**: `docs/ADMIN_API_SPEC.md`
- **Implementation Details**: `docs/ADMIN_API_IMPLEMENTATION.md`
- **Base URL**: `{{base_url}}/api/admin` (default: `http://localhost:8000/api/admin`)

---

## Quick Start Checklist

- [ ] Tạo Environment với `base_url` và `token`
- [ ] Tạo Collection "Admin APIs"
- [ ] Setup Collection Authorization (Bearer Token)
- [ ] Login và save token vào environment
- [ ] Test GET Dashboard Stats để verify authentication
- [ ] Tạo Brand → Save brand_id
- [ ] Tạo Category → Save category_id
- [ ] Tạo Product → Save product_id
- [ ] Test upload images cho product
- [ ] Test các APIs khác

---

**Happy Testing với Postman! 🚀**

