# Admin API Endpoints Specification

## Tổng quan

Tài liệu này mô tả chi tiết tất cả các API endpoints cần thiết cho hệ thống Admin của website bán giày.

**Base URL**: `/api/admin`

**Authentication**: Tất cả endpoints đều yêu cầu Bearer token với role `admin`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

---

## 1. Dashboard (Thống kê tổng quan)

### GET `/api/admin/dashboard/stats`
Lấy thống kê tổng quan cho dashboard

**Query Parameters**:
- `period` (optional): `week` | `month` | `year` | `custom`
- `startDate` (optional): ISO date string (nếu period = custom)
- `endDate` (optional): ISO date string (nếu period = custom)

**Response 200**:
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
  "recentOrders": [
    {
      "id": "ORD-001",
      "customer": "Nguyễn Văn A",
      "product": "Nike Air Max 270",
      "amount": 3500000,
      "status": "completed",
      "date": "2025-11-01T10:30:00Z"
    }
    // ... more orders
  ],
  "revenueChart": [
    {
      "month": "T1",
      "revenue": 45000000,
      "orders": 120
    }
    // ... more months
  ],
  "categoryDistribution": [
    {
      "name": "Giày thể thao",
      "value": 45,
      "count": 205
    }
    // ... more categories
  ]
}
```

---

## 2. Products Management (Quản lý Sản phẩm)

### GET `/api/admin/products`
Lấy danh sách sản phẩm

**Query Parameters**:
- `page` (optional, default: 1): Số trang
- `limit` (optional, default: 20): Số item mỗi trang
- `search` (optional): Tìm kiếm theo tên
- `category` (optional): Lọc theo danh mục
- `brand` (optional): Lọc theo thương hiệu
- `status` (optional): `active` | `inactive` | `out_of_stock` | `low_stock`
- `sort` (optional): `name` | `price` | `stock` | `sold` | `createdAt`
- `order` (optional): `asc` | `desc`

**Response 200**:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Nike Air Max 270",
      "slug": "nike-air-max-270",
      "description": "Mô tả sản phẩm...",
      "category": {
        "id": 1,
        "name": "Giày thể thao",
        "slug": "giay-the-thao"
      },
      "brand": {
        "id": 1,
        "name": "Nike",
        "slug": "nike"
      },
      "price": 3500000,
      "discountPrice": null,
      "stock": 45,
      "sold": 123,
      "images": [
        "/media/products/nike-air-max-270-1.jpg",
        "/media/products/nike-air-max-270-2.jpg"
      ],
      "status": "active",
      "specifications": {
        "size": ["38", "39", "40", "41", "42"],
        "color": ["Đen", "Trắng", "Xám"]
      },
      "createdAt": "2024-01-15T10:00:00Z",
      "updatedAt": "2024-11-01T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 456,
    "totalPages": 23
  }
}
```

### GET `/api/admin/products/:id`
Lấy chi tiết một sản phẩm

**Response 200**:
```json
{
  "id": 1,
  "name": "Nike Air Max 270",
  "slug": "nike-air-max-270",
  "description": "Mô tả chi tiết...",
  "category": {
    "id": 1,
    "name": "Giày thể thao",
    "slug": "giay-the-thao"
  },
  "brand": {
    "id": 1,
    "name": "Nike",
    "slug": "nike"
  },
  "price": 3500000,
  "discountPrice": null,
  "stock": 45,
  "sold": 123,
  "images": [
    "/media/products/nike-air-max-270-1.jpg",
    "/media/products/nike-air-max-270-2.jpg"
  ],
  "status": "active",
  "specifications": {
    "size": ["38", "39", "40", "41", "42"],
    "color": ["Đen", "Trắng", "Xám"],
    "material": "Da tổng hợp",
    "weight": "300g"
  },
  "tags": ["nike", "sports", "running"],
  "createdAt": "2024-01-15T10:00:00Z",
  "updatedAt": "2024-11-01T15:30:00Z"
}
```

### POST `/api/admin/products`
Tạo sản phẩm mới

**Body**:
```json
{
  "name": "Nike Air Max 270",
  "slug": "nike-air-max-270",
  "description": "Mô tả sản phẩm",
  "categoryId": 1,
  "brandId": 1,
  "price": 3500000,
  "discountPrice": null,
  "stock": 45,
  "images": [
    "/media/products/nike-air-max-270-1.jpg"
  ],
  "status": "active",
  "specifications": {
    "size": ["38", "39", "40", "41", "42"],
    "color": ["Đen", "Trắng", "Xám"]
  },
  "tags": ["nike", "sports"]
}
```

**Response 201**:
```json
{
  "id": 1,
  "name": "Nike Air Max 270",
  // ... full product object
}
```

### PUT `/api/admin/products/:id`
Cập nhật sản phẩm

**Body**: Tương tự POST, tất cả fields là optional

**Response 200**: Updated product object

### DELETE `/api/admin/products/:id`
Xóa sản phẩm

**Response 204**: No Content

### POST `/api/admin/products/:id/images`
Upload ảnh cho sản phẩm

**Content-Type**: `multipart/form-data`

**Form fields**:
- `images`: File[] (JPEG/PNG, max 5MB mỗi file, tối đa 5 files)

**Response 200**:
```json
{
  "images": [
    "/media/products/nike-air-max-270-1.jpg",
    "/media/products/nike-air-max-270-2.jpg"
  ]
}
```

---

## 3. Orders Management (Quản lý Đơn hàng)

### GET `/api/admin/orders`
Lấy danh sách đơn hàng

**Query Parameters**:
- `page` (optional, default: 1)
- `limit` (optional, default: 20)
- `search` (optional): Tìm theo mã đơn, tên khách hàng, email
- `status` (optional): `pending` | `processing` | `shipping` | `completed` | `cancelled`
- `paymentStatus` (optional): `pending` | `paid` | `refunded` | `failed`
- `startDate` (optional): ISO date string
- `endDate` (optional): ISO date string
- `sort` (optional): `createdAt` | `total` | `status`
- `order` (optional): `asc` | `desc`

**Response 200**:
```json
{
  "data": [
    {
      "id": "ORD-001",
      "orderNumber": "ORD-001",
      "customer": {
        "id": 1,
        "name": "Nguyễn Văn A",
        "email": "nguyenvana@email.com",
        "phone": "0901234567"
      },
      "items": [
        {
          "product": {
            "id": 1,
            "name": "Nike Air Max 270",
            "image": "/media/products/nike-air-max-270-1.jpg"
          },
          "quantity": 1,
          "price": 3500000,
          "total": 3500000
        },
        {
          "product": {
            "id": 2,
            "name": "Adidas Ultraboost",
            "image": "/media/products/adidas-ultraboost-1.jpg"
          },
          "quantity": 1,
          "price": 4200000,
          "total": 4200000
        }
      ],
      "subtotal": 7700000,
      "shippingFee": 30000,
      "discount": 0,
      "total": 7730000,
      "status": "completed",
      "paymentMethod": "credit_card",
      "paymentStatus": "paid",
      "shippingAddress": {
        "receiver": "Nguyễn Văn A",
        "detail": "123 Đường ABC",
        "ward": "Phường 1",
        "district": "Quận 1",
        "province": "TP.HCM",
        "phone": "0901234567"
      },
      "orderDate": "2025-11-01T10:30:00Z",
      "completedDate": "2025-11-03T14:20:00Z",
      "notes": "Giao hàng trước 17h"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1234,
    "totalPages": 62
  },
  "stats": {
    "pending": 45,
    "processing": 123,
    "shipping": 89,
    "completed": 967,
    "cancelled": 10
  }
}
```

### GET `/api/admin/orders/:id`
Lấy chi tiết đơn hàng

**Response 200**: Full order object (giống như trong array của GET /orders)

### PATCH `/api/admin/orders/:id/status`
Cập nhật trạng thái đơn hàng

**Body**:
```json
{
  "status": "processing" // pending | processing | shipping | completed | cancelled
}
```

**Response 200**: Updated order object

**Lưu ý**: 
- Không thể chuyển từ `completed` hoặc `cancelled` sang status khác
- Khi chuyển sang `completed`, tự động set `completedDate`

### GET `/api/admin/orders/export`
Xuất báo cáo đơn hàng

**Query Parameters**: Tương tự GET /orders (thêm format)

**Query Parameters**:
- `format` (optional): `csv` | `xlsx` (default: csv)
- `startDate` (required)
- `endDate` (required)
- `status` (optional)
- `paymentStatus` (optional)

**Response 200**: File download (CSV hoặc Excel)

---

## 4. Customers Management (Quản lý Khách hàng)

### GET `/api/admin/customers`
Lấy danh sách khách hàng

**Query Parameters**:
- `page` (optional, default: 1)
- `limit` (optional, default: 20)
- `search` (optional): Tìm theo tên, email, số điện thoại
- `status` (optional): `active` | `inactive` | `vip` | `blocked`
- `sort` (optional): `name` | `totalOrders` | `totalSpent` | `joinDate`
- `order` (optional): `asc` | `desc`

**Response 200**:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Nguyễn Văn A",
      "displayName": "Nguyễn Văn A",
      "email": "nguyenvana@email.com",
      "phone": "0901234567",
      "avatar": "/media/avatars/user-1.jpg",
      "addresses": [
        {
          "id": 1,
          "receiver": "Nguyễn Văn A",
          "detail": "123 Đường ABC",
          "ward": "Phường 1",
          "district": "Quận 1",
          "province": "TP.HCM",
          "is_default": true
        }
      ],
      "totalOrders": 15,
      "totalSpent": 45000000,
      "averageOrderValue": 3000000,
      "lastOrder": "2025-11-01T10:30:00Z",
      "status": "active",
      "joinDate": "2024-05-15T10:00:00Z",
      "isVip": false
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 8549,
    "totalPages": 428
  },
  "stats": {
    "total": 8549,
    "active": 7234,
    "vip": 1234,
    "inactive": 81
  }
}
```

### GET `/api/admin/customers/:id`
Lấy chi tiết khách hàng

**Response 200**: Full customer object với thêm:
- `orders`: Array of recent orders (last 10)
- `orderHistory`: Summary stats

```json
{
  "id": 1,
  "name": "Nguyễn Văn A",
  // ... all customer fields
  "orders": [
    {
      "id": "ORD-001",
      "orderNumber": "ORD-001",
      "total": 3500000,
      "status": "completed",
      "orderDate": "2025-11-01T10:30:00Z"
    }
    // ... more orders
  ],
  "orderHistory": {
    "totalOrders": 15,
    "totalSpent": 45000000,
    "averageOrderValue": 3000000,
    "firstOrderDate": "2024-05-20T10:00:00Z",
    "lastOrderDate": "2025-11-01T10:30:00Z"
  }
}
```

### PATCH `/api/admin/customers/:id/status`
Cập nhật trạng thái khách hàng

**Body**:
```json
{
  "status": "active" // active | inactive | vip | blocked
}
```

**Response 200**: Updated customer object

---

## 5. Categories Management (Quản lý Danh mục)

### GET `/api/admin/categories`
Lấy danh sách danh mục

**Query Parameters**:
- `page` (optional, default: 1)
- `limit` (optional, default: 50)
- `search` (optional): Tìm theo tên
- `status` (optional): `active` | `inactive`
- `sort` (optional): `name` | `productCount` | `createdAt`
- `order` (optional): `asc` | `desc`

**Response 200**:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Giày thể thao",
      "slug": "giay-the-thao",
      "description": "Giày dành cho các hoạt động thể thao và vận động",
      "image": "/media/categories/sports-shoes.jpg",
      "productCount": 45,
      "status": "active",
      "createdAt": "2024-01-15T10:00:00Z",
      "updatedAt": "2024-11-01T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 15,
    "totalPages": 1
  }
}
```

### GET `/api/admin/categories/:id`
Lấy chi tiết danh mục

**Response 200**: Full category object

### POST `/api/admin/categories`
Tạo danh mục mới

**Body**:
```json
{
  "name": "Giày thể thao",
  "slug": "giay-the-thao", // optional, auto-generate từ name nếu không có
  "description": "Mô tả danh mục",
  "status": "active"
}
```

**Response 201**: Created category object

### PUT `/api/admin/categories/:id`
Cập nhật danh mục

**Body**: Tương tự POST, tất cả fields là optional

**Response 200**: Updated category object

### DELETE `/api/admin/categories/:id`
Xóa danh mục

**Response 204**: No Content

**Lưu ý**: Không thể xóa nếu danh mục có sản phẩm. Response 400 với message.

### POST `/api/admin/categories/:id/image`
Upload ảnh cho danh mục

**Content-Type**: `multipart/form-data`

**Form fields**:
- `image`: File (JPEG/PNG, max 5MB)

**Response 200**:
```json
{
  "image": "/media/categories/sports-shoes.jpg"
}
```

---

## 6. Brands Management (Quản lý Thương hiệu)

### GET `/api/admin/brands`
Lấy danh sách thương hiệu

**Query Parameters**: Tương tự categories

**Response 200**:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Nike",
      "slug": "nike",
      "description": "Thương hiệu thể thao hàng đầu thế giới",
      "logo": "/media/brands/nike-logo.png",
      "website": "https://www.nike.com",
      "country": "USA",
      "productCount": 52,
      "status": "active",
      "createdAt": "2024-01-10T10:00:00Z",
      "updatedAt": "2024-11-01T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 12,
    "totalPages": 1
  }
}
```

### GET `/api/admin/brands/:id`
Lấy chi tiết thương hiệu

**Response 200**: Full brand object

### POST `/api/admin/brands`
Tạo thương hiệu mới

**Body**:
```json
{
  "name": "Nike",
  "slug": "nike", // optional
  "description": "Mô tả thương hiệu",
  "website": "https://www.nike.com",
  "country": "USA",
  "status": "active"
}
```

**Response 201**: Created brand object

### PUT `/api/admin/brands/:id`
Cập nhật thương hiệu

**Body**: Tương tự POST

**Response 200**: Updated brand object

### DELETE `/api/admin/brands/:id`
Xóa thương hiệu

**Response 204**: No Content

**Lưu ý**: Không thể xóa nếu thương hiệu có sản phẩm. Response 400.

### POST `/api/admin/brands/:id/logo`
Upload logo cho thương hiệu

**Content-Type**: `multipart/form-data`

**Form fields**:
- `logo`: File (JPEG/PNG, max 5MB)

**Response 200**:
```json
{
  "logo": "/media/brands/nike-logo.png"
}
```

---

## 7. Analytics (Thống kê & Phân tích)

### GET `/api/admin/analytics`
Lấy dữ liệu phân tích

**Query Parameters**:
- `period`: `week` | `month` | `quarter` | `year` | `custom`
- `startDate`: ISO date string (nếu period = custom)
- `endDate`: ISO date string (nếu period = custom)
- `metrics`: Comma-separated list: `revenue,orders,customers,products` (default: all)

**Response 200**:
```json
{
  "summary": {
    "totalRevenue": 44200000,
    "revenueChange": 12.5,
    "totalOrders": 375,
    "ordersChange": 8.2,
    "newCustomers": 127,
    "customersChange": 15.3,
    "averageOrderValue": 117800
  },
  "dailyRevenue": [
    {
      "date": "2025-11-01",
      "revenue": 5200000,
      "orders": 45
    }
    // ... more days
  ],
  "topProducts": [
    {
      "productId": 1,
      "productName": "Nike Air Max",
      "sales": 234,
      "revenue": 819000000
    }
    // ... more products
  ],
  "customerSegments": [
    {
      "segment": "new",
      "name": "Khách mới",
      "count": 35,
      "percentage": 35
    },
    {
      "segment": "regular",
      "name": "Khách thường xuyên",
      "count": 45,
      "percentage": 45
    },
    {
      "segment": "vip",
      "name": "Khách VIP",
      "count": 15,
      "percentage": 15
    },
    {
      "segment": "inactive",
      "name": "Không hoạt động",
      "count": 5,
      "percentage": 5
    }
  ],
  "trafficSources": [
    {
      "source": "organic",
      "name": "Tìm kiếm tự nhiên",
      "visitors": 12450,
      "percentage": 42
    },
    {
      "source": "direct",
      "name": "Trực tiếp",
      "visitors": 8930,
      "percentage": 30
    },
    {
      "source": "social",
      "name": "Mạng xã hội",
      "visitors": 4780,
      "percentage": 16
    },
    {
      "source": "ads",
      "name": "Quảng cáo",
      "visitors": 2850,
      "percentage": 10
    },
    {
      "source": "other",
      "name": "Khác",
      "visitors": 590,
      "percentage": 2
    }
  ],
  "hourlyOrders": [
    {
      "hour": 0,
      "orders": 5
    },
    {
      "hour": 3,
      "orders": 2
    }
    // ... all 24 hours
  ]
}
```

---

## 8. Settings (Cài đặt hệ thống)

### GET `/api/admin/settings`
Lấy tất cả cài đặt hệ thống

**Response 200**:
```json
{
  "general": {
    "storeName": "Shoe Store",
    "storeEmail": "contact@shoestore.com",
    "storePhone": "0901234567",
    "storeAddress": "123 Đường ABC, Quận 1, TP.HCM",
    "currency": "VND",
    "timezone": "Asia/Ho_Chi_Minh"
  },
  "email": {
    "emailNotifications": true,
    "orderConfirmation": true,
    "shipmentTracking": true,
    "promotionalEmails": false
  },
  "payment": {
    "cod": true,
    "bankTransfer": true,
    "creditCard": false,
    "eWallet": false
  },
  "shipping": {
    "freeShippingThreshold": 500000,
    "shippingFee": 30000,
    "estimatedDelivery": "3-5 ngày"
  },
  "security": {
    "twoFactorAuth": false,
    "sessionTimeout": 30,
    "allowMultipleSessions": true
  }
}
```

### PUT `/api/admin/settings`
Cập nhật cài đặt hệ thống

**Body**: Có thể update một hoặc nhiều sections

```json
{
  "general": {
    "storeName": "New Store Name",
    "storeEmail": "new@email.com"
  },
  "email": {
    "emailNotifications": true,
    "orderConfirmation": false
  }
}
```

**Response 200**: Updated settings object

### GET `/api/admin/settings/:section`
Lấy cài đặt của một section cụ thể

**Path Parameters**:
- `section`: `general` | `email` | `payment` | `shipping` | `security`

**Response 200**: Settings object của section đó

### PUT `/api/admin/settings/:section`
Cập nhật cài đặt của một section

**Body**: Settings object của section đó

**Response 200**: Updated settings object

---

## Error Responses

Tất cả endpoints trả về error theo format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message in Vietnamese",
    "details": {} // optional, additional error details
  }
}
```

### Common HTTP Status Codes:
- `200`: Success
- `201`: Created (POST)
- `204`: No Content (DELETE)
- `400`: Bad Request (validation error, invalid data)
- `401`: Unauthorized (invalid/expired token)
- `403`: Forbidden (user không có quyền admin)
- `404`: Not Found (resource không tồn tại)
- `409`: Conflict (duplicate slug, etc.)
- `413`: Request Entity Too Large (file quá lớn)
- `422`: Unprocessable Entity (business logic error)
- `500`: Internal Server Error

### Error Codes:

**Authentication Errors**:
- `UNAUTHORIZED`: Token không hợp lệ hoặc đã hết hạn
- `FORBIDDEN`: User không có quyền admin
- `TOKEN_EXPIRED`: Token đã hết hạn

**Validation Errors**:
- `VALIDATION_ERROR`: Dữ liệu không hợp lệ
- `MISSING_FIELD`: Thiếu field bắt buộc
- `INVALID_FORMAT`: Format không đúng

**Business Logic Errors**:
- `RESOURCE_NOT_FOUND`: Resource không tồn tại
- `DUPLICATE_SLUG`: Slug đã tồn tại
- `CANNOT_DELETE`: Không thể xóa (có dependency)
- `INVALID_STATUS_TRANSITION`: Chuyển trạng thái không hợp lệ
- `FILE_TOO_LARGE`: File quá lớn
- `INVALID_FILE_TYPE`: Loại file không được phép

---

## Pagination

Tất cả endpoints list đều trả về pagination:

```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 456,
    "totalPages": 23,
    "hasNext": true,
    "hasPrev": false
  }
}
```

---

## File Upload

### Giới hạn:
- **Product images**: Max 5MB mỗi file, tối đa 5 files
- **Category images**: Max 5MB, 1 file
- **Brand logos**: Max 5MB, 1 file
- **Supported formats**: JPEG, PNG, WebP

### Response format:
```json
{
  "url": "/media/products/image.jpg",
  "size": 1024000,
  "width": 1920,
  "height": 1080
}
```

---

## Notes

1. **Slug auto-generation**: Nếu không cung cấp slug, hệ thống tự động generate từ name (loại bỏ dấu, lowercase, thay space bằng -)

2. **Status transitions**:
   - Orders: `pending` → `processing` → `shipping` → `completed`
   - Orders có thể chuyển sang `cancelled` từ bất kỳ status nào (trừ `completed`)

3. **Cascade delete**: 
   - Xóa category/brand không được phép nếu có sản phẩm
   - Xóa sản phẩm sẽ xóa ảnh liên quan

4. **Permissions**: Tất cả endpoints yêu cầu user có `role = 'admin'`

5. **Rate limiting**: Admin APIs có thể có rate limiting khác với public APIs (recommended: 100 requests/minute)

6. **Audit log**: Tất cả thao tác admin nên được log để audit trail

---

## Implementation Checklist

### ✅ High Priority:
- [ ] GET `/api/admin/dashboard/stats`
- [ ] GET `/api/admin/products` (with filters)
- [ ] POST `/api/admin/products`
- [ ] PUT `/api/admin/products/:id`
- [ ] DELETE `/api/admin/products/:id`
- [ ] GET `/api/admin/orders` (with filters)
- [ ] PATCH `/api/admin/orders/:id/status`
- [ ] GET `/api/admin/customers`
- [ ] GET `/api/admin/customers/:id`

### ⚠️ Medium Priority:
- [ ] GET `/api/admin/categories`
- [ ] POST `/api/admin/categories`
- [ ] PUT `/api/admin/categories/:id`
- [ ] DELETE `/api/admin/categories/:id`
- [ ] GET `/api/admin/brands`
- [ ] POST `/api/admin/brands`
- [ ] PUT `/api/admin/brands/:id`
- [ ] DELETE `/api/admin/brands/:id`
- [ ] GET `/api/admin/analytics`

### 📝 Low Priority:
- [ ] POST `/api/admin/products/:id/images`
- [ ] POST `/api/admin/categories/:id/image`
- [ ] POST `/api/admin/brands/:id/logo`
- [ ] GET `/api/admin/orders/export`
- [ ] GET `/api/admin/settings`
- [ ] PUT `/api/admin/settings`

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Author**: Admin System Team

