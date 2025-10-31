# API Implementation Summary

## Các API đã được triển khai theo `endpointAPIdesign.md`

Tất cả các endpoint đều nằm dưới base URL: `/api/`

### 1. Profile Management (Quản lý hồ sơ)

#### ✅ PUT `/api/profile`
- **Mô tả**: Cập nhật thông tin hồ sơ người dùng
- **Auth**: Required (Bearer token)
- **Body** (tùy chọn):
```json
{
  "displayName": "string",
  "phone": "string", 
  "sex": "male|female|other",
  "birth": "2024-01-01T00:00:00.000Z"
}
```
- **Response 200**:
```json
{
  "id": "...",
  "email": "...",
  "displayName": "...",
  "phone": "...",
  "sex": "...",
  "birth": "...",
  "avatar": "..."
}
```

#### ✅ PUT `/api/profile/avatar`
- **Mô tả**: Upload ảnh đại diện mới
- **Auth**: Required
- **Content-Type**: multipart/form-data
- **Form field**: `file` (JPEG/PNG, ≤ 1MB)
- **Response 200**:
```json
{
  "avatarUrl": "/media/avatars/..."
}
```

#### ✅ DELETE `/api/me`
- **Mô tả**: Xóa tài khoản người dùng
- **Auth**: Required
- **Body** (optional):
```json
{
  "password": "..." 
}
```
- **Response**: 204 No Content

---

### 2. Password Management (Quản lý mật khẩu)

#### ✅ POST `/api/change-password`
- **Mô tả**: Đổi mật khẩu hiện tại
- **Auth**: Required
- **Body**:
```json
{
  "oldPassword": "Old@123",
  "newPassword": "New@123"
}
```
- **Response 200**:
```json
{
  "message": "Password changed"
}
```

---

### 3. Address Management (Quản lý địa chỉ)

#### ✅ GET `/api/addresses`
- **Mô tả**: Lấy danh sách địa chỉ của user
- **Auth**: Required
- **Response 200**: Array of Address objects

#### ✅ POST `/api/addresses`
- **Mô tả**: Thêm địa chỉ mới
- **Auth**: Required
- **Body**:
```json
{
  "receiver": "Tên người nhận",
  "detail": "Số nhà, đường",
  "ward": "Phường",
  "district": "Quận/Huyện", 
  "province": "Tỉnh/TP",
  "phone": "0xxxxxxxxx",
  "is_default": false
}
```
- **Response 201**: Address object

#### ✅ PUT `/api/addresses/:id`
- **Mô tả**: Cập nhật địa chỉ
- **Auth**: Required
- **Body**: Các field như POST (tùy chọn)
- **Response 200**: Address object updated

#### ✅ PATCH `/api/addresses/:id/default`
- **Mô tả**: Thiết lập địa chỉ mặc định (tự động bỏ default các địa chỉ khác)
- **Auth**: Required
- **Response 200**:
```json
{
  "id": "...",
  "is_default": true
}
```

#### ✅ DELETE `/api/addresses/:id`
- **Mô tả**: Xóa địa chỉ
- **Auth**: Required
- **Response**: 204 No Content

---

### 4. Social Links (Liên kết MXH)

#### ✅ GET `/api/links`
- **Mô tả**: Lấy trạng thái liên kết các tài khoản MXH
- **Auth**: Required
- **Response 200**:
```json
{
  "google": true,
  "facebook": false
}
```

#### ✅ POST `/api/links/google`
- **Mô tả**: Liên kết tài khoản Google với user hiện tại
- **Auth**: Required
- **Body**:
```json
{
  "access_token": "..." 
}
```
hoặc
```json
{
  "id_token": "..."
}
```
- **Response 200**:
```json
{
  "google": true
}
```

#### ✅ DELETE `/api/links/google`
- **Mô tả**: Hủy liên kết tài khoản Google
- **Auth**: Required
- **Response**: 204 No Content

#### ✅ POST `/api/links/facebook`
- **Mô tả**: Liên kết tài khoản Facebook
- **Auth**: Required
- **Body**:
```json
{
  "access_token": "..."
}
```
- **Response 200**:
```json
{
  "facebook": true
}
```

#### ✅ DELETE `/api/links/facebook`
- **Mô tả**: Hủy liên kết tài khoản Facebook
- **Auth**: Required
- **Response**: 204 No Content

---

### 5. Notification Settings (Cài đặt thông báo)

#### ✅ GET `/api/notification-settings`
- **Mô tả**: Lấy cài đặt thông báo hiện tại
- **Auth**: Required
- **Response 200**:
```json
{
  "emailNotif": true,
  "emailUpdate": true,
  "emailSale": true,
  "emailSurvey": true,
  "smsNotif": false,
  "smsSale": false
}
```

#### ✅ PUT `/api/notification-settings`
- **Mô tả**: Cập nhật cài đặt thông báo
- **Auth**: Required
- **Body**: Các boolean fields (tất cả hoặc một phần)
```json
{
  "emailNotif": true,
  "emailUpdate": false,
  "emailSale": true,
  "emailSurvey": false,
  "smsNotif": true,
  "smsSale": false
}
```
- **Response 200**: Cài đặt mới (như GET response)

---

## Database Changes (Thay đổi Database)

### User Model
Đã thêm các trường:
```python
emailNotif = BooleanField(default=True)
emailUpdate = BooleanField(default=True)
emailSale = BooleanField(default=True)
emailSurvey = BooleanField(default=True)
smsNotif = BooleanField(default=False)
smsSale = BooleanField(default=False)
```

### Address Model
Đã có đầy đủ các trường cần thiết với `is_default` field.

---

## Configuration (Cấu hình)

### Media Files
Đã cấu hình trong `config/settings.py`:
```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

Trong development mode, media files được serve tự động qua Django.

### Upload Directory
Avatar files được lưu trong: `media/avatars/`

---

## Testing (Kiểm tra)

### Cách test với curl hoặc Postman:

1. **Login để lấy token**:
```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

2. **Update profile**:
```bash
curl -X PUT http://localhost:8000/api/profile \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"displayName":"New Name","sex":"male"}'
```

3. **Upload avatar**:
```bash
curl -X PUT http://localhost:8000/api/profile/avatar \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

4. **Get addresses**:
```bash
curl -X GET http://localhost:8000/api/addresses \
  -H "Authorization: Bearer YOUR_TOKEN"
```

5. **Add address**:
```bash
curl -X POST http://localhost:8000/api/addresses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"receiver":"John","detail":"123 Street","ward":"Ward 1","district":"District 1","province":"HCM","phone":"0123456789","is_default":true}'
```

---

## Error Handling (Xử lý lỗi)

Tất cả API trả về error theo format:
```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created (POST)
- `204`: No Content (DELETE)
- `400`: Bad Request (validation error)
- `401`: Unauthorized (invalid/expired token or wrong password)
- `404`: Not Found (resource không tồn tại)
- `413`: Request Entity Too Large (file quá lớn)

---

## Notes (Ghi chú)

1. **File upload**: Avatar được lưu local trong thư mục `media/avatars/`. Trong production, nên migrate sang cloud storage (S3, GCS, Cloudinary, etc.)

2. **Address default logic**: Khi set một địa chỉ làm default, tất cả các địa chỉ khác của user sẽ tự động được set `is_default=false`.

3. **Social linking**: Khi link tài khoản MXH, hệ thống verify token với Google/Facebook API để đảm bảo tính hợp lệ.

4. **Password change**: Chỉ user có password (không phải OAuth-only) mới có thể đổi mật khẩu.

5. **Delete account**: Khi xóa user, các related documents (Address, Cart, Wishlist, Notification) sẽ tự động bị xóa theo (CASCADE rule).

