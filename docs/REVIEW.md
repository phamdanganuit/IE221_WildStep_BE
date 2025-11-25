

## Danh sách endpoint (review flow)

| # | Method | Path | Mô tả ngắn |
|---|--------|------|------------|
| 1 | `GET` | `/orders/{orderId}/reviewable-items` | Liệt kê item đủ điều kiện đánh giá |
| 2 | `POST` | `/orders/{orderId}/reviews` | Tạo review cho các item đã mua |
| 3 | `PATCH` | `/orders/{orderId}/reviews/{reviewId}` | Cập nhật review đã tạo |

---

## 1. `GET /orders/{orderId}/reviewable-items`

**Mục đích:** frontend xác định item nào đã/ chưa đánh giá.

### Response `200 OK`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `orderId` | string | ID đơn tương ứng |
| `status` | string | Trạng thái đơn (phải là `completed`) |
| `completed_at` | string (ISO) | Ngày hoàn tất để kiểm tra hạn review |
| `items` | array | Danh sách item đủ điều kiện |

Mỗi phần tử trong `items`:

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `order_item_id` | string | ID item trong đơn |
| `product_id` | string | ID sản phẩm |
| `product_name` | string | Tên sản phẩm |
| `product_image` | string | Ảnh dùng cho UI |
| `color` | string | Màu đã mua |
| `size` | string | Size đã mua |
| `quantity` | number | Số lượng đã mua |
| `isRated` | boolean | Đã có review hay chưa |
| `reviewId` | string \| null | ID review nếu đã tồn tại |


## 2. `POST /orders/{orderId}/reviews`

**Mục đích:** tạo review mới cho một hoặc nhiều item trong đơn hoàn tất.

### Request body

```json
{
  "items": [
    {
      "order_item_id": "itm_001",
      "product_id": "691a514d8a441121bc44c50a",
      "rating": 5,
      "comment": "Chất lượng rất tốt",
      "images": ["https://cdn.example.com/reviews/rev_001_img_1.jpg"]
    }
  ]
}
```

### Response `201 Created`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `orderId` | string | ID đơn chứa các review vừa tạo |
| `created` | array | Danh sách review đã lưu thành công |

Phần tử `created[]`:

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `reviewId` | string | ID review (ObjectId) |
| `order_item_id` | string | ID item được review |
| `product_id` | string | ID sản phẩm |
| `rating` | number | Điểm 1–5 |
| `comment` | string | Nội dung đánh giá |
| `images` | string[] | Danh sách URL ảnh đính kèm |
| `created_at` | string (ISO) | Thời điểm lưu review |


## 3. `PATCH /orders/{orderId}/reviews/{reviewId}`

**Mục đích:** cập nhật review còn trong thời hạn chỉnh sửa.

### Request body (các trường optional)

```json
{
  "rating": 4,
  "comment": "Sau 1 tuần sử dụng vẫn ổn",
  "images": []
}
```

### Response `200 OK`

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `review` | object | Review sau khi cập nhật |

`review` object:

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `reviewId` | string | ID review |
| `order_item_id` | string | ID item tương ứng |
| `product_id` | string | ID sản phẩm |
| `rating` | number | Điểm cập nhật |
| `comment` | string | Nội dung cập nhật |
| `images` | string[] | URL ảnh mới |
| `updated_at` | string (ISO) | Timestamp chỉnh sửa |

---

## 4. `GET /products/{productIdOrSlug}/reviews`

**Mục đích:** hiển thị danh sách review công khai của một sản phẩm với bộ lọc chi tiết.

### Query params được hỗ trợ

| Tên | Mặc định | Mô tả |
|-----|----------|-------|
| `page` | `1` | Trang hiện tại (1–∞) |
| `page_size` | `5` | Số review mỗi trang (1–50) |
| `sort` | `newest` | `newest`, `oldest`, `highest`, `lowest`, `with_images` |
| `rating` | – | Lọc theo đúng 1 mức sao (1–5) |
| `ratings` / `ratings[]` | – | Lọc nhiều mức sao, ví dụ `ratings=5,4` hoặc `ratings[]=5&ratings[]=4` |
| `has_images` / `has_media` | – | Khi đặt `true/1/on/yes` chỉ trả review có ảnh/video đính kèm |

- Có thể kết hợp đồng thời `ratings` và `has_images`.
- `sort=with_images` vẫn hoạt động như trước (tương đương vừa lọc ảnh vừa sắp xếp mới nhất).

### Response `200 OK`

```json
{
  "product": { "id": "64...", "slug": "air-jordan-1", "name": "Air Jordan 1", "thumbnail": "..." },
  "summary": {
    "count": 25,
    "average": 4.72,
    "with_images": 10,
    "distribution": { "5": 18, "4": 5, "3": 1, "2": 1, "1": 0 }
  },
  "filters": {
    "sort": "highest",
    "has_images": true,
    "ratings": [5, 4]
  },
  "pagination": {
    "page": 1,
    "page_size": 5,
    "total": 6,
    "total_pages": 2
  },
  "reviews": [
    {
      "reviewId": "656...",
      "orderId": "653...",
      "order_item_id": "ORD-123:0",
      "rating": 5,
      "comment": "Form ôm chân, màu chuẩn",
      "images": ["https://cdn.../rev1.png"],
      "variant": { "color": "University Blue", "size": "42" },
      "user": { "id": "64...", "displayName": "Trung Nghia", "avatar": "..." },
      "likeCount": 3,
      "created_at": "2024-11-11T09:00:00Z",
      "updated_at": null
    }
  ]
}
```

---

## 8. Lưu ý chung & mã lỗi

- **Xác thực:** mọi endpoint yêu cầu header `Authorization: Bearer {token}`. Thiếu hoặc token hết hạn trả `401` cùng biến `detail`.
- **403 Forbidden:** `detail` mô tả lý do (ví dụ `"Bạn không có quyền xem đơn hàng này"` hoặc `"Bạn chỉ có thể đánh giá sản phẩm sau khi đơn hoàn tất"`).
- **404 Not Found:** biến `detail` luôn có thông báo cụ thể như `"Không tìm thấy đơn hàng"`.
- **409 Conflict:** dùng khi review trùng hoặc đơn đã bị hủy; payload mẫu `{ "detail": "Voucher không còn hiệu lực" }`.
- **422 Unprocessable Entity:** khi sản phẩm hết hàng, backend trả `{ "detail": "Sản phẩm '...' size ... đã hết hàng" }`.

Giữ nguyên đúng tên biến trong response giúp frontend parse dễ dàng và giảm lỗi map trường.

