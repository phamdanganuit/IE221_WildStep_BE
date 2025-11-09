# Cập nhật các trường Product

## Tóm tắt thay đổi

### 1. Đã BỎ
- ❌ `specifications` (DictField) - không còn sử dụng

### 2. Đã THÊM

#### Product attributes (hỗ trợ đa ngôn ngữ)
- ✅ `gender` - Giới tính (DynamicField, có thể là string hoặc dict đa ngôn ngữ)
- ✅ `material` - Chất liệu (DynamicField, có thể là string hoặc dict đa ngôn ngữ)
- ✅ `weight` - Trọng lượng (DynamicField, có thể là string, số, hoặc dict đa ngôn ngữ)
- ✅ `size` - Kích thước tổng quát (DynamicField, có thể là string hoặc dict đa ngôn ngữ)

#### ColorVariant updates
- ✅ `hex_color` - Mã màu hex (StringField, ví dụ: "#FF5733")
- ✅ `color_name` - Đã chuyển sang DynamicField để hỗ trợ đa ngôn ngữ

#### SizeVariant updates
- ✅ `size_name` - Đã chuyển sang DynamicField để hỗ trợ đa ngôn ngữ

---

## Chi tiết cấu trúc trường mới

### Product Model

```python
class Product(me.Document):
    # ... các trường cũ ...
    
    # Product attributes (all support multilingual)
    gender = me.DynamicField()       # Ví dụ: "male", "female", "unisex" hoặc {"vi": "Nam", "en": "Male"}
    material = me.DynamicField()     # Ví dụ: "cotton" hoặc {"vi": "Cotton 100%", "en": "100% Cotton"}
    weight = me.DynamicField()       # Ví dụ: "350g" hoặc {"vi": "350 gram", "en": "350 grams"}
    size = me.DynamicField()         # Ví dụ: "L" hoặc {"vi": "Size L", "en": "Size L"}
```

### ColorVariant

```python
class ColorVariant(me.EmbeddedDocument):
    color_name = me.DynamicField(required=True)  # Ví dụ: {"vi": "Đỏ", "en": "Red", "ja": "赤"}
    hex_color = me.StringField()                 # Ví dụ: "#FF0000"
    image = me.StringField()                     # URL ảnh màu
    tags = me.ListField(me.StringField())        # Tags cho màu
```

### SizeVariant

```python
class SizeVariant(me.EmbeddedDocument):
    size_name = me.DynamicField(required=True)   # Ví dụ: {"vi": "Size M", "en": "Medium"}
    tags = me.ListField(me.StringField())        # Tags cho size
```

---

## API Usage

### Admin API - Tạo Product

**POST** `/api/admin/products`

#### Cách 1: Gửi dưới dạng JSON object (đa ngôn ngữ)

```json
{
  "name": {"vi": "Giày thể thao", "en": "Sports Shoes"},
  "description": {"vi": "Giày chất lượng cao", "en": "High quality shoes"},
  "price": 500000,
  "categoryId": "...",
  "brandId": "...",
  "gender": {"vi": "Nam", "en": "Male"},
  "material": {"vi": "Da tổng hợp", "en": "Synthetic leather"},
  "weight": {"vi": "400 gram", "en": "400 grams"},
  "size": {"vi": "EU 39-44", "en": "EU 39-44"},
  "colors": [
    {
      "color_name": {"vi": "Đen", "en": "Black"},
      "hex_color": "#000000",
      "image": "https://...",
      "tags": ["classic", "formal"]
    }
  ],
  "sizes": [
    {
      "size_name": {"vi": "Size 40", "en": "Size 40"},
      "tags": ["standard"]
    }
  ]
}
```

#### Cách 2: Gửi dưới dạng dot-notation fields

```json
{
  "name.vi": "Giày thể thao",
  "name.en": "Sports Shoes",
  "description.vi": "Giày chất lượng cao",
  "description.en": "High quality shoes",
  "gender.vi": "Nam",
  "gender.en": "Male",
  "material.vi": "Da tổng hợp",
  "material.en": "Synthetic leather",
  "weight.vi": "400 gram",
  "weight.en": "400 grams",
  "size.vi": "EU 39-44",
  "size.en": "EU 39-44",
  "price": 500000,
  "categoryId": "...",
  "brandId": "..."
}
```

#### Cách 3: Gửi dưới dạng string đơn giản (không đa ngôn ngữ)

```json
{
  "name": "Giày thể thao",
  "description": "Giày chất lượng cao",
  "gender": "male",
  "material": "Synthetic leather",
  "weight": "400g",
  "size": "39-44",
  "price": 500000,
  "categoryId": "...",
  "brandId": "..."
}
```

---

### Admin API - Cập nhật Product

**PUT** `/api/admin/products/:id`

```json
{
  "gender.vi": "Nữ",
  "material": {"vi": "Vải canvas", "en": "Canvas fabric"},
  "colors": [
    {
      "color_name": {"vi": "Trắng", "en": "White"},
      "hex_color": "#FFFFFF",
      "image": "https://...",
      "tags": ["summer"]
    }
  ]
}
```

---

### Admin API - Lấy chi tiết Product

**GET** `/api/admin/products/:id`

Response:

```json
{
  "id": "...",
  "name": {"vi": "Giày thể thao", "en": "Sports Shoes"},
  "slug": "giay-the-thao",
  "description": {"vi": "Giày chất lượng cao", "en": "High quality shoes"},
  "price": 500000,
  "discountPrice": null,
  "stock": 100,
  "sold": 50,
  "images": ["https://..."],
  "status": "active",
  "gender": {"vi": "Nam", "en": "Male"},
  "material": {"vi": "Da tổng hợp", "en": "Synthetic leather"},
  "weight": {"vi": "400 gram", "en": "400 grams"},
  "size": {"vi": "EU 39-44", "en": "EU 39-44"},
  "colors": [
    {
      "color_name": {"vi": "Đen", "en": "Black"},
      "hex_color": "#000000",
      "image": "https://...",
      "tags": ["classic"]
    }
  ],
  "sizes": [
    {
      "size_name": {"vi": "Size 40", "en": "Size 40"},
      "tags": ["standard"]
    }
  ],
  "size_table": {"vi": "Bảng size...", "en": "Size chart..."},
  "tags": ["sports", "running"],
  "category": {...},
  "brand": {...},
  "createdAt": "2023-01-01T00:00:00",
  "updatedAt": "2023-01-02T00:00:00"
}
```

---

## Migration Notes

### Dữ liệu cũ
- Các product cũ có `specifications` sẽ không tự động migrate sang các trường mới
- Cần cập nhật thủ công nếu muốn chuyển dữ liệu từ `specifications` sang các trường mới

### Backward compatibility
- API vẫn hoạt động với các product cũ (không có các trường mới)
- Các trường mới sẽ trả về `null` hoặc không xuất hiện nếu chưa được set

---

## Files đã thay đổi

1. ✅ `products/models.py` - Cập nhật Product, ColorVariant, SizeVariant models
2. ✅ `products/admin_views.py` - Cập nhật ProductListView, ProductDetailView để xử lý trường mới

---

## Testing

### Test tạo product với các trường mới

```bash
curl -X POST http://localhost:8000/api/admin/products \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": {"vi": "Test Product", "en": "Test Product"},
    "price": 100000,
    "categoryId": "...",
    "brandId": "...",
    "gender": {"vi": "Nam", "en": "Male"},
    "material": {"vi": "Cotton", "en": "Cotton"},
    "weight": "300g",
    "colors": [
      {
        "color_name": {"vi": "Đỏ", "en": "Red"},
        "hex_color": "#FF0000"
      }
    ]
  }'
```


