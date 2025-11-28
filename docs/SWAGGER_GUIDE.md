# Hướng dẫn sử dụng Swagger API Documentation

## Giới thiệu

Swagger (OpenAPI) đã được tích hợp vào dự án để cung cấp tài liệu API tương tác và dễ sử dụng.

## Truy cập Swagger UI

Sau khi chạy server, bạn có thể truy cập Swagger UI tại các URL sau:

### 1. Swagger UI (Giao diện chính)
```
http://localhost:8000/swagger/
```
- Giao diện tương tác cho phép test API trực tiếp
- Hiển thị tất cả endpoints, parameters, request/response schemas
- Cho phép thử nghiệm API ngay trên trình duyệt

### 2. ReDoc (Giao diện đọc tài liệu)
```
http://localhost:8000/redoc/
```
- Giao diện đẹp mắt, tập trung vào việc đọc tài liệu
- Phù hợp để tham khảo API specifications
- Không có tính năng test API

### 3. JSON Schema
```
http://localhost:8000/swagger.json/
http://localhost:8000/swagger.yaml/
```
- OpenAPI specification ở dạng JSON/YAML
- Sử dụng để import vào các công cụ khác (Postman, Insomnia, etc.)

## Cách sử dụng Swagger UI

### 1. Xem danh sách API
- Mở http://localhost:8000/swagger/
- Các API được nhóm theo tags (Users, Products, Orders, Admin, etc.)
- Click vào tag để mở rộng và xem các endpoints

### 2. Xác thực (Authentication)

#### Để test các API yêu cầu xác thực:

1. **Lấy JWT Token:**
   - Tìm endpoint `POST /api/login` hoặc `POST /api/register`
   - Click vào endpoint và chọn "Try it out"
   - Nhập thông tin đăng nhập:
     ```json
     {
       "email": "user@example.com",
       "password": "yourpassword"
     }
     ```
   - Click "Execute"
   - Copy `access_token` từ response

2. **Sử dụng Token:**
   - Click nút **"Authorize"** ở góc trên bên phải
   - Trong popup, nhập: `Bearer <your_token>`
     ```
     Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```
   - Click "Authorize" và "Close"
   - Giờ bạn có thể test các API yêu cầu xác thực

#### Admin APIs:
- Cần đăng nhập với tài khoản có role="admin"
- Tất cả admin APIs đều có prefix `/api/admin/`

### 3. Test một API endpoint

1. Click vào endpoint muốn test (ví dụ: `GET /api/products`)
2. Click nút **"Try it out"**
3. Nhập parameters (query params, path params, request body)
4. Click **"Execute"**
5. Xem kết quả:
   - **Response code**: 200, 400, 404, etc.
   - **Response body**: Dữ liệu trả về
   - **Response headers**: Headers của response
   - **Curl**: Lệnh curl tương đương

### 4. Xem Request/Response Schemas

Mỗi endpoint hiển thị:
- **Parameters**: Các tham số đầu vào (query, path, body)
- **Request Body Schema**: Cấu trúc dữ liệu gửi lên
- **Responses**: Các response codes và schemas tương ứng
- **Examples**: Ví dụ về request và response

## Cấu trúc API

### Public APIs (Không cần xác thực)

#### Authentication & Registration
- `POST /api/register` - Đăng ký tài khoản
- `POST /api/login` - Đăng nhập
- `POST /api/oauth/google` - Đăng nhập Google
- `POST /api/oauth/facebook` - Đăng nhập Facebook

#### Products & Content
- `GET /api/products` - Danh sách sản phẩm (có phân trang, filter, search)
- `GET /api/products/{id_or_slug}` - Chi tiết sản phẩm
- `GET /api/products/search` - Tìm kiếm sản phẩm
- `GET /api/products/autocomplete` - Gợi ý tìm kiếm
- `GET /api/categories` - Danh mục sản phẩm
- `GET /api/brands` - Thương hiệu
- `GET /api/reviews` - Danh sách đánh giá
- `GET /api/content/banners` - Banners quảng cáo
- `GET /api/content/hero` - Hero content

### User APIs (Cần xác thực)

#### Profile Management
- `GET /api/me` - Thông tin user hiện tại
- `GET /api/profile` - Profile đầy đủ
- `PUT /api/profile` - Cập nhật profile
- `POST /api/profile/avatar` - Upload avatar
- `POST /api/change-password` - Đổi mật khẩu

#### Address Management
- `GET /api/addresses` - Danh sách địa chỉ
- `POST /api/addresses` - Thêm địa chỉ mới
- `PUT /api/addresses/{id}` - Cập nhật địa chỉ
- `DELETE /api/addresses/{id}` - Xóa địa chỉ
- `POST /api/addresses/{id}/default` - Đặt địa chỉ mặc định

#### Cart Management
- `GET /api/cart` - Xem giỏ hàng
- `GET /api/cart/count` - Số lượng items trong giỏ
- `POST /api/cart/items` - Thêm sản phẩm vào giỏ
- `PUT /api/cart/items/{id}` - Cập nhật số lượng
- `DELETE /api/cart/items/{id}` - Xóa item khỏi giỏ
- `DELETE /api/cart/items` - Xóa toàn bộ giỏ hàng

#### Voucher Management
- `GET /api/vouchers` - Danh sách voucher của user
- `POST /api/vouchers/validate` - Kiểm tra voucher
- `POST /api/addVoucher` - Thêm voucher bằng code
- `DELETE /api/removeVoucher` - Xóa voucher

#### Order Management
- `GET /api/orders` - Lịch sử đơn hàng
- `POST /api/orders` - Tạo đơn hàng mới
- `GET /api/orders/{id}` - Chi tiết đơn hàng
- `PATCH /api/orders/{id}/status` - Cập nhật trạng thái (user cancel)
- `GET /api/orders/{id}/reviewable-items` - Sản phẩm có thể đánh giá
- `POST /api/orders/{id}/reviews` - Tạo đánh giá
- `PUT /api/orders/{id}/reviews/{reviewId}` - Cập nhật đánh giá

#### Review Actions
- `POST /api/reviews/upload-image` - Upload ảnh đánh giá
- `POST /api/reviews/{id}/like` - Like đánh giá
- `POST /api/reviews/{id}/dislike` - Dislike đánh giá

### Admin APIs (Cần xác thực + role admin)

#### Dashboard & Analytics
- `GET /api/admin/dashboard/stats` - Thống kê tổng quan
- `GET /api/admin/analytics` - Phân tích chi tiết

#### Brand Management
- `GET /api/admin/brands` - Danh sách brands
- `POST /api/admin/brands` - Tạo brand mới
- `GET /api/admin/brands/{id}` - Chi tiết brand
- `PUT /api/admin/brands/{id}` - Cập nhật brand
- `DELETE /api/admin/brands/{id}` - Xóa brand
- `POST /api/admin/brands/{id}/logo` - Upload logo

#### Category Management
- `GET /api/admin/categories` - Danh sách categories
- `POST /api/admin/categories` - Tạo category mới
- `GET /api/admin/categories/{id}` - Chi tiết category
- `PUT /api/admin/categories/{id}` - Cập nhật category
- `DELETE /api/admin/categories/{id}` - Xóa category

#### Product Management
- `GET /api/admin/products` - Danh sách sản phẩm
- `POST /api/admin/products` - Tạo sản phẩm mới
- `GET /api/admin/products/{id}` - Chi tiết sản phẩm
- `PUT /api/admin/products/{id}` - Cập nhật sản phẩm
- `DELETE /api/admin/products/{id}` - Xóa sản phẩm
- `POST /api/admin/products/{id}/images` - Upload ảnh sản phẩm

#### Banner Management
- `GET /api/admin/banners` - Danh sách banners
- `POST /api/admin/banners` - Tạo banner mới
- `GET /api/admin/banners/{id}` - Chi tiết banner
- `PUT /api/admin/banners/{id}` - Cập nhật banner
- `DELETE /api/admin/banners/{id}` - Xóa banner
- `POST /api/admin/banners/{id}/image` - Upload ảnh banner

#### Order Management (Admin)
- `GET /api/admin/orders` - Danh sách đơn hàng (có filter, search, sort)
- `GET /api/admin/orders/{id}` - Chi tiết đơn hàng
- `PATCH /api/admin/orders/{id}/status` - Cập nhật trạng thái đơn

#### Customer Management
- `GET /api/admin/customers` - Danh sách khách hàng
- `GET /api/admin/customers/{id}` - Chi tiết khách hàng
- `PATCH /api/admin/customers/{id}/status` - Block/Unblock khách hàng

#### Voucher Management (Admin)
- `GET /api/admin/vouchers` - Danh sách vouchers
- `POST /api/admin/vouchers` - Tạo voucher mới
- `GET /api/admin/vouchers/{id}` - Chi tiết voucher
- `PUT /api/admin/vouchers/{id}` - Cập nhật voucher
- `DELETE /api/admin/vouchers/{id}` - Xóa voucher

## Query Parameters phổ biến

### Pagination
```
?page=1&limit=20
?page=2&page_size=50
```

### Search
```
?search=nike
?search=giày%20thể%20thao
```

### Filtering
```
?status=active
?paymentStatus=paid
?category=sneakers
?brand=nike
```

### Sorting
```
?sort=price&order=asc
?sort=createdAt&order=desc
?sort=name&order=asc
```

### Date Range
```
?startDate=2024-01-01T00:00:00Z&endDate=2024-12-31T23:59:59Z
```

## Response Codes

- **200 OK**: Request thành công
- **201 Created**: Tạo resource thành công
- **204 No Content**: Xóa thành công
- **400 Bad Request**: Dữ liệu đầu vào không hợp lệ
- **401 Unauthorized**: Chưa đăng nhập hoặc token không hợp lệ
- **403 Forbidden**: Không có quyền truy cập
- **404 Not Found**: Resource không tồn tại
- **409 Conflict**: Xung đột (ví dụ: email đã tồn tại)
- **500 Internal Server Error**: Lỗi server

## Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Mô tả lỗi"
  }
}
```

hoặc

```json
{
  "detail": "Mô tả lỗi"
}
```

## Tips & Best Practices

### 1. Testing Flow
1. Đăng ký/Đăng nhập để lấy token
2. Authorize trong Swagger UI
3. Test các endpoints cần xác thực
4. Kiểm tra response codes và data

### 2. Import vào Postman
1. Lấy OpenAPI spec: http://localhost:8000/swagger.json/
2. Mở Postman → Import → Paste URL hoặc import file JSON
3. Tạo Environment với biến `access_token`
4. Sử dụng `{{access_token}}` trong Authorization header

### 3. Debugging
- Kiểm tra **Curl command** trong Swagger UI để xem exact request
- Xem **Request/Response** trong Network tab của browser
- Kiểm tra Django logs trong terminal

### 4. Production
Khi deploy lên production:
- Set `DEBUG=False` trong settings
- Cân nhắc tắt Swagger UI hoặc giới hạn truy cập
- Hoặc giữ Swagger nhưng yêu cầu authentication

## Troubleshooting

### Token hết hạn
- Đăng nhập lại để lấy token mới
- Token mặc định có thời gian sống giới hạn

### CORS errors
- Server đã config CORS cho phép all origins trong development
- Production cần config ALLOWED_HOSTS cụ thể

### 404 Not Found cho Swagger
- Đảm bảo đã cài `drf-yasg`: `pip install drf-yasg`
- Kiểm tra `drf_yasg` trong INSTALLED_APPS
- Restart server sau khi thay đổi settings

## Liên hệ & Support

Nếu có vấn đề hoặc câu hỏi:
- Kiểm tra documentation tại `/swagger/` hoặc `/redoc/`
- Xem Django logs trong terminal
- Kiểm tra các file trong `docs/` folder

---

**Chúc bạn làm việc hiệu quả với Swagger API Documentation! 🚀**
