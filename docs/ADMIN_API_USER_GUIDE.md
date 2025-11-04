# Hướng dẫn Sử dụng Admin API

## Mục lục
1. [Giới thiệu](#giới-thiệu)
2. [Bắt đầu](#bắt-đầu)
3. [Xác thực](#xác-thực)
4. [Quản lý Dashboard](#quản-lý-dashboard)
5. [Quản lý Sản phẩm](#quản-lý-sản-phẩm)
6. [Quản lý Đơn hàng](#quản-lý-đơn-hàng)
7. [Quản lý Khách hàng](#quản-lý-khách-hàng)
8. [Quản lý Danh mục & Thương hiệu](#quản-lý-danh-mục--thương-hiệu)
9. [Các tình huống sử dụng](#các-tình-huống-sử-dụng)
10. [Mẹo và Lưu ý](#mẹo-và-lưu-ý)
11. [Câu hỏi thường gặp](#câu-hỏi-thường-gặp)

---

## Giới thiệu

Tài liệu này hướng dẫn cách sử dụng Admin API để quản lý cửa hàng giày trực tuyến. API này cung cấp các chức năng quản lý toàn diện cho quản trị viên.

### Tổng quan các tính năng

- **Dashboard & Thống kê**: Xem tổng quan doanh thu, đơn hàng, khách hàng
- **Quản lý Sản phẩm**: Thêm, sửa, xóa sản phẩm và upload ảnh
- **Quản lý Đơn hàng**: Xem và cập nhật trạng thái đơn hàng
- **Quản lý Khách hàng**: Xem thông tin và quản lý trạng thái khách hàng
- **Quản lý Danh mục & Thương hiệu**: Quản lý cấu trúc danh mục và thương hiệu

### Base URL

Tất cả API endpoints bắt đầu với: `/api/admin`

### Authentication

Tất cả các API yêu cầu xác thực bằng Bearer token với quyền admin. Xem phần [Xác thực](#xác-thực) để biết cách lấy token.

---

## Bắt đầu

### Yêu cầu

- Quyền truy cập admin (tài khoản có `role = "admin"`)
- Access token hợp lệ
- Công cụ gọi API (Postman, cURL, hoặc ứng dụng frontend)

### Cấu trúc URL

```
http://localhost:8000/api/admin/{endpoint}
```

Ví dụ:
- Dashboard: `GET http://localhost:8000/api/admin/dashboard/stats`
- Sản phẩm: `GET http://localhost:8000/api/admin/products`

---

## Xác thực

### Bước 1: Đăng nhập

Để sử dụng Admin API, bạn cần đăng nhập và lấy access token.

**Request:**
```http
POST /api/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

### Bước 2: Sử dụng Token

Thêm token vào header của mọi request:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Lưu ý về Token

- Token có thời hạn sử dụng (thường 24 giờ)
- Khi token hết hạn, bạn sẽ nhận lỗi `401 Unauthorized`
- Đăng nhập lại để lấy token mới

---

## Quản lý Dashboard

### Xem thống kê tổng quan

**Endpoint:** `GET /api/admin/dashboard/stats`

**Mục đích:** Xem tổng quan nhanh về tình hình kinh doanh

**Ví dụ request:**
```http
GET /api/admin/dashboard/stats?period=month
Authorization: Bearer {token}
```

**Tham số:**
- `period` (tùy chọn): `week`, `month`, `year` (mặc định: `month`)

**Response mẫu:**
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

**Cách sử dụng:**
- Xem tổng quan nhanh khi vào admin panel
- So sánh các chỉ số với kỳ trước
- Theo dõi các đơn hàng mới nhất

### Xem phân tích chi tiết

**Endpoint:** `GET /api/admin/analytics`

**Mục đích:** Phân tích sâu hơn về doanh số, sản phẩm bán chạy, phân khúc khách hàng

**Ví dụ request:**
```http
GET /api/admin/analytics?period=month
Authorization: Bearer {token}
```

**Response bao gồm:**
- Tổng quan doanh thu và đơn hàng
- Top sản phẩm bán chạy
- Phân khúc khách hàng (mới, thường xuyên, VIP, không hoạt động)
- Nguồn traffic
- Thống kê theo giờ

---

## Quản lý Sản phẩm

### Xem danh sách sản phẩm

**Endpoint:** `GET /api/admin/products`

**Mục đích:** Xem tất cả sản phẩm trong hệ thống

**Ví dụ request:**
```http
GET /api/admin/products?page=1&limit=20&status=active
Authorization: Bearer {token}
```

**Tham số tìm kiếm (tùy chọn):**
- `page`: Số trang (mặc định: 1)
- `limit`: Số item mỗi trang (mặc định: 20)
- `search`: Tìm kiếm theo tên
- `category`: Lọc theo danh mục
- `brand`: Lọc theo thương hiệu
- `status`: `active`, `inactive`, `out_of_stock`, `low_stock`
- `sort`: `name`, `price`, `stock`, `sold`, `createdAt`
- `order`: `asc`, `desc`

**Use case:** Xem danh sách sản phẩm để quản lý tồn kho, kiểm tra trạng thái

### Tạo sản phẩm mới

**Endpoint:** `POST /api/admin/products`

**Mục đích:** Thêm sản phẩm mới vào cửa hàng

**Ví dụ request:**
```http
POST /api/admin/products
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Nike Air Max 270",
  "categoryId": "60d5ec49f1b2c72b8c8e4f3c",
  "brandId": "60d5ec49f1b2c72b8c8e4f3d",
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

**Thông tin bắt buộc:**
- `name`: Tên sản phẩm
- `categoryId`: ID danh mục (phải tồn tại)
- `brandId`: ID thương hiệu (phải tồn tại)
- `price`: Giá gốc (VND)

**Thông tin tùy chọn:**
- `slug`: URL-friendly (tự động tạo từ name nếu không có)
- `description`: Mô tả sản phẩm
- `stock`: Số lượng tồn kho (mặc định: 0)
- `discount`: Phần trăm giảm giá (0-100)
- `status`: `active` hoặc `inactive`
- `images`: Mảng URL ảnh
- `specifications`: Thông số kỹ thuật (size, color, material, etc.)
- `tags`: Mảng tags

**Lưu ý:**
- `slug` tự động được tạo từ `name` nếu không cung cấp
- `discountPrice` tự động được tính: `price * (1 - discount/100)`
- Trạng thái sản phẩm tự động cập nhật: `out_of_stock` khi stock = 0, `low_stock` khi stock < 10

### Cập nhật sản phẩm

**Endpoint:** `PUT /api/admin/products/{id}`

**Mục đích:** Cập nhật thông tin sản phẩm (giá, tồn kho, mô tả, etc.)

**Ví dụ request:**
```http
PUT /api/admin/products/60d5ec49f1b2c72b8c8e4f3c
Authorization: Bearer {token}
Content-Type: application/json

{
  "stock": 50,
  "discount": 15,
  "description": "Mô tả mới cập nhật",
  "price": 3800000
}
```

**Lưu ý:**
- Tất cả các fields là tùy chọn
- Chỉ cập nhật các fields được gửi trong request
- `discountPrice` tự động được tính lại nếu `price` hoặc `discount` thay đổi

**Use case:**
- Cập nhật giá khi có khuyến mãi
- Cập nhật tồn kho sau khi nhập hàng
- Sửa mô tả hoặc thông tin sản phẩm

### Xem chi tiết sản phẩm

**Endpoint:** `GET /api/admin/products/{id}`

**Mục đích:** Xem đầy đủ thông tin một sản phẩm

**Ví dụ request:**
```http
GET /api/admin/products/60d5ec49f1b2c72b8c8e4f3c
Authorization: Bearer {token}
```

### Upload ảnh sản phẩm

**Endpoint:** `POST /api/admin/products/{id}/images`

**Mục đích:** Upload ảnh cho sản phẩm

**Ví dụ request:**
```http
POST /api/admin/products/60d5ec49f1b2c72b8c8e4f3c/images
Authorization: Bearer {token}
Content-Type: multipart/form-data

images: [File 1]
images: [File 2]
images: [File 3]
```

**Yêu cầu:**
- Format: JPEG, PNG, WebP
- Kích thước tối đa: 5MB mỗi file
- Số lượng: Tối đa 5 files mỗi lần upload

**Response:**
```json
{
  "images": [
    "/media/products/product_id_abc123.jpg",
    "/media/products/product_id_def456.jpg"
  ]
}
```

**Use case:** Thêm ảnh cho sản phẩm mới hoặc cập nhật ảnh sản phẩm hiện có

### Xóa sản phẩm

**Endpoint:** `DELETE /api/admin/products/{id}`

**Mục đích:** Xóa sản phẩm khỏi hệ thống

**Ví dụ request:**
```http
DELETE /api/admin/products/60d5ec49f1b2c72b8c8e4f3c
Authorization: Bearer {token}
```

**Lưu ý:**
- Xóa sản phẩm sẽ xóa tất cả ảnh liên quan
- Đơn hàng đã có sản phẩm này vẫn giữ nguyên thông tin

---

## Quản lý Đơn hàng

### Xem danh sách đơn hàng

**Endpoint:** `GET /api/admin/orders`

**Mục đích:** Xem tất cả đơn hàng với thông tin cơ bản

**Ví dụ request:**
```http
GET /api/admin/orders?page=1&limit=20&status=pending
Authorization: Bearer {token}
```

**Tham số tìm kiếm (tùy chọn):**
- `page`: Số trang
- `limit`: Số item mỗi trang
- `search`: Tìm theo mã đơn, tên khách hàng, email
- `status`: `pending`, `processing`, `shipping`, `completed`, `cancelled`
- `paymentStatus`: `pending`, `paid`, `refunded`, `failed`
- `startDate`: Ngày bắt đầu (ISO format)
- `endDate`: Ngày kết thúc (ISO format)
- `sort`: `createdAt`, `total`, `status`
- `order`: `asc`, `desc`

**Response bao gồm:**
- Danh sách đơn hàng với thông tin khách hàng, tổng tiền, trạng thái
- Thống kê số lượng đơn theo từng trạng thái
- Phân trang

**Use case:**
- Xem đơn hàng mới cần xử lý
- Lọc đơn hàng theo trạng thái để xử lý
- Tìm kiếm đơn hàng của khách hàng cụ thể

### Xem chi tiết đơn hàng

**Endpoint:** `GET /api/admin/orders/{id}`

**Mục đích:** Xem đầy đủ thông tin một đơn hàng

**Ví dụ request:**
```http
GET /api/admin/orders/60d5ec49f1b2c72b8c8e4f3c
Authorization: Bearer {token}
```

**Response bao gồm:**
- Thông tin khách hàng
- Danh sách sản phẩm trong đơn
- Địa chỉ giao hàng
- Tổng tiền, phí ship, giảm giá
- Trạng thái đơn hàng và thanh toán
- Ngày đặt, ngày hoàn thành
- Ghi chú

**Use case:**
- Xem chi tiết đơn hàng để chuẩn bị giao hàng
- Kiểm tra địa chỉ giao hàng
- Xem lịch sử đơn hàng của khách hàng

### Cập nhật trạng thái đơn hàng

**Endpoint:** `PATCH /api/admin/orders/{id}/status`

**Mục đích:** Thay đổi trạng thái đơn hàng (xử lý, đang giao, hoàn thành, hủy)

**Ví dụ request:**
```http
PATCH /api/admin/orders/60d5ec49f1b2c72b8c8e4f3c/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "processing"
}
```

**Các trạng thái:**
- `pending`: Chờ xử lý
- `processing`: Đang xử lý
- `shipping`: Đang giao hàng
- `completed`: Đã hoàn thành
- `cancelled`: Đã hủy

**Quy trình chuyển trạng thái:**
```
pending → processing → shipping → completed
   ↓          ↓           ↓
cancelled  cancelled  cancelled
```

**Lưu ý quan trọng:**
- ✅ Có thể chuyển: `pending` → `processing` → `shipping` → `completed`
- ✅ Có thể hủy từ: `pending`, `processing`, `shipping`
- ❌ **KHÔNG THỂ** chuyển từ `completed` hoặc `cancelled` sang trạng thái khác
- Tự động set `completedDate` khi chuyển sang `completed`

**Use case:**
- Cập nhật trạng thái khi xử lý đơn hàng
- Đánh dấu đã giao hàng khi khách nhận được
- Hủy đơn hàng khi khách yêu cầu

---

## Quản lý Khách hàng

### Xem danh sách khách hàng

**Endpoint:** `GET /api/admin/customers`

**Mục đích:** Xem tất cả khách hàng với thống kê tự động

**Ví dụ request:**
```http
GET /api/admin/customers?page=1&limit=20&status=vip
Authorization: Bearer {token}
```

**Tham số tìm kiếm (tùy chọn):**
- `page`: Số trang
- `limit`: Số item mỗi trang
- `search`: Tìm theo tên, email, số điện thoại
- `status`: `active`, `inactive`, `vip`, `blocked`
- `sort`: `name`, `totalOrders`, `totalSpent`, `joinDate`
- `order`: `asc`, `desc`

**Response bao gồm:**
- Thông tin khách hàng
- `totalOrders`: Tổng số đơn đã đặt
- `totalSpent`: Tổng số tiền đã chi
- `averageOrderValue`: Giá trị đơn hàng trung bình
- `isVip`: `true` nếu tổng đơn > 10
- `status`: Trạng thái tự động tính toán

**Trạng thái tự động:**
- `blocked`: Bị chặn thủ công bởi admin
- `vip`: Tổng số đơn > 10 (tự động)
- `active`: Có đơn hàng trong 30 ngày gần nhất (tự động)
- `inactive`: Không có đơn hàng trong 30 ngày gần nhất (tự động)

**Use case:**
- Xem danh sách khách VIP để ưu tiên chăm sóc
- Tìm khách hàng không hoạt động để chạy chiến dịch marketing
- Kiểm tra khách hàng bị chặn

### Xem chi tiết khách hàng

**Endpoint:** `GET /api/admin/customers/{id}`

**Mục đích:** Xem đầy đủ thông tin và lịch sử mua hàng của khách hàng

**Ví dụ request:**
```http
GET /api/admin/customers/60d5ec49f1b2c72b8c8e4f3c
Authorization: Bearer {token}
```

**Response bao gồm:**
- Thông tin cá nhân (tên, email, số điện thoại, avatar)
- Danh sách địa chỉ
- 10 đơn hàng gần nhất
- Thống kê mua hàng (tổng đơn, tổng tiền, đơn đầu tiên, đơn cuối)

**Use case:**
- Xem lịch sử mua hàng của khách để hỗ trợ
- Kiểm tra địa chỉ giao hàng
- Đánh giá giá trị khách hàng

### Chặn/Bỏ chặn khách hàng

**Endpoint:** `PATCH /api/admin/customers/{id}/status`

**Mục đích:** Chặn hoặc bỏ chặn khách hàng (chỉ có thể set `blocked` thủ công)

**Ví dụ request - Chặn:**
```http
PATCH /api/admin/customers/60d5ec49f1b2c72b8c8e4f3c/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "blocked"
}
```

**Ví dụ request - Bỏ chặn:**
```http
PATCH /api/admin/customers/60d5ec49f1b2c72b8c8e4f3c/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "active"
}
```

**Lưu ý:**
- Chỉ có thể set `blocked` thủ công
- Các trạng thái khác (`vip`, `active`, `inactive`) được tính tự động dựa trên hành vi mua hàng
- Khi bỏ chặn, status sẽ tự động chuyển về `active`, `inactive`, hoặc `vip` tùy theo dữ liệu

**Use case:**
- Chặn khách hàng vi phạm chính sách
- Bỏ chặn khách hàng sau khi giải quyết vấn đề

---

## Quản lý Danh mục & Thương hiệu

### Quản lý Thương hiệu

#### Xem danh sách thương hiệu

**Endpoint:** `GET /api/admin/brands`

**Mục đích:** Xem tất cả thương hiệu trong hệ thống

#### Tạo thương hiệu mới

**Endpoint:** `POST /api/admin/brands`

**Ví dụ request:**
```http
POST /api/admin/brands
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Nike",
  "description": "Thương hiệu thể thao hàng đầu thế giới",
  "website": "https://www.nike.com",
  "country": "USA",
  "status": "active"
}
```

**Thông tin bắt buộc:**
- `name`: Tên thương hiệu

**Thông tin tùy chọn:**
- `slug`: URL-friendly (tự động tạo từ name)
- `description`: Mô tả
- `website`: Website chính thức
- `country`: Quốc gia
- `status`: `active` hoặc `inactive`

#### Cập nhật thương hiệu

**Endpoint:** `PUT /api/admin/brands/{id}`

#### Xóa thương hiệu

**Endpoint:** `DELETE /api/admin/brands/{id}`

**Lưu ý:** Không thể xóa thương hiệu nếu có sản phẩm đang sử dụng thương hiệu đó.

### Quản lý Danh mục

#### Xem danh sách danh mục

**Endpoint:** `GET /api/admin/categories`

**Mục đích:** Xem cấu trúc danh mục dạng phân cấp (parent - child)

**Response:** Trả về danh mục cha với các danh mục con lồng bên trong

#### Tạo danh mục cha

**Endpoint:** `POST /api/admin/categories`

**Ví dụ request:**
```http
POST /api/admin/categories
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Giày thể thao",
  "type": "parent",
  "description": "Danh mục giày thể thao",
  "status": "active"
}
```

**Lưu ý:** `type` phải là `"parent"`

#### Tạo danh mục con

**Ví dụ request:**
```http
POST /api/admin/categories
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Giày chạy bộ",
  "type": "child",
  "parentId": "60d5ec49f1b2c72b8c8e4f3c",
  "description": "Giày dành cho chạy bộ",
  "status": "active"
}
```

**Lưu ý:**
- `type` phải là `"child"`
- `parentId` là bắt buộc cho danh mục con

**Cấu trúc danh mục:**
```
Giày thể thao (parent)
├── Giày chạy bộ (child)
├── Giày bóng đá (child)
└── Giày tennis (child)
```

---

## Các tình huống sử dụng

### Tình huống 1: Thêm sản phẩm mới vào cửa hàng

**Workflow:**

1. **Kiểm tra/B Tạo thương hiệu** (nếu chưa có)
   ```http
   GET /api/admin/brands
   # Hoặc tạo mới:
   POST /api/admin/brands
   { "name": "Nike", "country": "USA" }
   ```

2. **Kiểm tra/Tạo danh mục** (nếu chưa có)
   ```http
   GET /api/admin/categories
   # Hoặc tạo mới:
   POST /api/admin/categories
   { "name": "Giày thể thao", "type": "parent" }
   ```

3. **Tạo sản phẩm**
   ```http
   POST /api/admin/products
   {
     "name": "Nike Air Max 270",
     "categoryId": "...",
     "brandId": "...",
     "price": 3500000,
     "stock": 45,
     "description": "..."
   }
   ```

4. **Upload ảnh sản phẩm**
   ```http
   POST /api/admin/products/{product_id}/images
   Content-Type: multipart/form-data
   images: [file1, file2, file3]
   ```

### Tình huống 2: Xử lý đơn hàng mới

**Workflow:**

1. **Xem đơn hàng chờ xử lý**
   ```http
   GET /api/admin/orders?status=pending
   ```

2. **Xem chi tiết đơn hàng**
   ```http
   GET /api/admin/orders/{order_id}
   ```
   - Kiểm tra địa chỉ giao hàng
   - Xem danh sách sản phẩm
   - Kiểm tra ghi chú từ khách

3. **Cập nhật trạng thái**
   ```http
   PATCH /api/admin/orders/{order_id}/status
   { "status": "processing" }
   ```

4. **Khi đã giao hàng, cập nhật hoàn thành**
   ```http
   PATCH /api/admin/orders/{order_id}/status
   { "status": "completed" }
   ```

### Tình huống 3: Quản lý tồn kho

**Workflow:**

1. **Xem sản phẩm sắp hết hàng**
   ```http
   GET /api/admin/products?status=low_stock
   ```

2. **Cập nhật tồn kho sau khi nhập hàng**
   ```http
   PUT /api/admin/products/{product_id}
   { "stock": 100 }
   ```

3. **Ngừng bán sản phẩm hết hàng**
   ```http
   PUT /api/admin/products/{product_id}
   { "status": "inactive" }
   ```

### Tình huống 4: Chạy chiến dịch khuyến mãi

**Workflow:**

1. **Cập nhật giá và giảm giá cho sản phẩm**
   ```http
   PUT /api/admin/products/{product_id}
   {
     "discount": 20,
     "price": 3500000
   }
   ```
   → `discountPrice` tự động tính: 2,800,000 VND

2. **Xem danh sách sản phẩm đang giảm giá**
   ```http
   GET /api/admin/products?sort=discount&order=desc
   ```

### Tình huống 5: Quản lý khách hàng VIP

**Workflow:**

1. **Xem danh sách khách VIP**
   ```http
   GET /api/admin/customers?status=vip
   ```

2. **Xem chi tiết khách VIP**
   ```http
   GET /api/admin/customers/{customer_id}
   ```
   - Xem lịch sử mua hàng
   - Tổng số tiền đã chi
   - Đơn hàng gần nhất

3. **Phân tích để đưa ra chương trình ưu đãi phù hợp**

### Tình huống 6: Kiểm tra và chặn khách hàng vi phạm

**Workflow:**

1. **Xem chi tiết khách hàng**
   ```http
   GET /api/admin/customers/{customer_id}
   ```

2. **Kiểm tra lịch sử đơn hàng và hành vi**

3. **Chặn khách hàng nếu cần**
   ```http
   PATCH /api/admin/customers/{customer_id}/status
   { "status": "blocked" }
   ```

---

## Mẹo và Lưu ý

### 1. Quản lý Token

- **Lưu token an toàn**: Không share token với người khác
- **Refresh token thường xuyên**: Đăng nhập lại mỗi ngày hoặc khi cần
- **Xử lý token hết hạn**: Implement logic tự động đăng nhập lại khi nhận `401`

### 2. Xử lý Lỗi

**Các lỗi thường gặp:**

- **401 Unauthorized**: Token không hợp lệ hoặc hết hạn → Đăng nhập lại
- **403 Forbidden**: Không có quyền admin → Kiểm tra role trong database
- **404 Not Found**: ID không tồn tại → Kiểm tra ID format (ObjectId 24 ký tự)
- **400 Bad Request**: Dữ liệu không hợp lệ → Kiểm tra required fields và format

**Format lỗi:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Thông báo lỗi bằng tiếng Việt",
    "details": {}
  }
}
```

### 3. Tối ưu Performance

- **Sử dụng pagination**: Luôn sử dụng `page` và `limit` khi lấy danh sách
- **Lọc dữ liệu**: Sử dụng filters để giảm dữ liệu trả về
- **Cache token**: Tránh đăng nhập lại nhiều lần

### 4. Bảo mật

- **HTTPS**: Luôn sử dụng HTTPS trong production
- **Không log token**: Không log hoặc in token ra console
- **Xóa token khi logout**: Implement logout để invalidate token

### 5. Upload Ảnh

- **Tối ưu ảnh trước khi upload**: Giảm kích thước file để tăng tốc độ
- **Kiểm tra format**: Chỉ upload JPEG, PNG, WebP
- **Kiểm tra kích thước**: Mỗi file tối đa 5MB

### 6. Quản lý Trạng thái

- **Hiểu rõ status transitions**: Đặc biệt với orders, không thể revert
- **Sử dụng status tự động**: Nhiều status được tính tự động, không cần set thủ công

---

## Câu hỏi thường gặp

### Q1: Làm sao để lấy token admin?

**A:** Đăng nhập bằng tài khoản có `role = "admin"` qua endpoint `/api/login`. Xem phần [Xác thực](#xác-thực).

### Q2: Token hết hạn khi nào?

**A:** Token thường có thời hạn 24 giờ. Khi nhận lỗi `401 Unauthorized`, bạn cần đăng nhập lại.

### Q3: Có thể xóa thương hiệu/category đang có sản phẩm không?

**A:** Không. Bạn sẽ nhận lỗi `400 Bad Request` với code `CANNOT_DELETE`. Cần xóa hoặc chuyển tất cả sản phẩm trước.

### Q4: Làm sao biết sản phẩm nào sắp hết hàng?

**A:** Sử dụng filter `status=low_stock` khi lấy danh sách sản phẩm:
```http
GET /api/admin/products?status=low_stock
```

### Q5: Có thể revert đơn hàng từ `completed` về `pending` không?

**A:** Không. Đơn hàng `completed` hoặc `cancelled` không thể đổi trạng thái. Đây là thiết kế để đảm bảo tính toàn vẹn dữ liệu.

### Q6: Trạng thái khách hàng được tính như thế nào?

**A:** 
- `vip`: Tự động nếu tổng đơn > 10
- `active`: Tự động nếu có đơn trong 30 ngày gần nhất
- `inactive`: Tự động nếu không có đơn trong 30 ngày
- `blocked`: Chỉ có thể set thủ công bởi admin

### Q7: Làm sao tìm đơn hàng của một khách hàng cụ thể?

**A:** Sử dụng parameter `search` với email hoặc tên:
```http
GET /api/admin/orders?search=nguyenvana@email.com
```

### Q8: `discountPrice` được tính như thế nào?

**A:** Tự động tính: `discountPrice = price * (1 - discount/100)`. Khi bạn update `price` hoặc `discount`, `discountPrice` tự động cập nhật.

### Q9: Có thể upload bao nhiêu ảnh cho một sản phẩm?

**A:** Tối đa 5 files mỗi lần upload. Bạn có thể upload nhiều lần để thêm nhiều ảnh hơn.

### Q10: Slug được tạo tự động như thế nào?

**A:** Slug tự động tạo từ `name` bằng cách:
- Chuyển về lowercase
- Loại bỏ dấu tiếng Việt
- Thay khoảng trắng bằng dấu `-`
- Loại bỏ ký tự đặc biệt

Ví dụ: "Nike Air Max 270" → "nike-air-max-270"

---

## Tài liệu liên quan

- **API Specification**: `docs/ADMIN_API_SPEC.md` - Chi tiết kỹ thuật các endpoints
- **Implementation Guide**: `docs/ADMIN_API_IMPLEMENTATION.md` - Chi tiết implementation
- **Testing Guide**: `docs/ADMIN_API_TESTING_GUIDE.md` - Hướng dẫn test với Postman

---

## Hỗ trợ

Nếu gặp vấn đề khi sử dụng API:

1. Kiểm tra phần [Troubleshooting](#troubleshooting) trong Testing Guide
2. Xem error message trong response để biết chi tiết lỗi
3. Kiểm tra logs trên server để debug
4. Liên hệ team phát triển với thông tin:
   - Endpoint đang gọi
   - Request body/parameters
   - Response error message
   - Timestamp xảy ra lỗi

---

**Phiên bản**: 1.0.0  
**Cập nhật lần cuối**: Tháng 11, 2025  
**Tác giả**: Admin System Team

---

**Chúc bạn sử dụng Admin API hiệu quả! 🚀**

