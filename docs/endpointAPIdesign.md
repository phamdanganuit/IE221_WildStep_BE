## API Endpoints Needed Now – Shoe Shop (Delta from Auth_README)

Chỉ liệt kê các endpoint CẦN THÊM để phục vụ các màn hình hiện có. Các endpoint đã có sẵn trong `Auth_README.md` (POST /api/register, POST /api/login, POST /api/oauth/google, POST /api/oauth/facebook, GET /api/profile, GET /api/me) giữ nguyên, không lặp lại ở đây.

### Base URL
- `https://api.shoe-shop.app/api`

### Authentication
- Với endpoint có (Auth), gửi header: `Authorization: Bearer <access_token>`

### Error Format (theo dự án hiện tại)
```json
{ "detail": "..." }
```

---

## 1) Hồ sơ cá nhân (Profile)

### 1.1 Cập nhật thông tin hồ sơ
- PUT `/profile` (Auth)
- Body (tùy chọn, validate kiểu dữ liệu):
```json
{ "displayName": "string", "phone": "string", "sex": "male|female|other", "birth": "2024-01-01T00:00:00.000Z" }
```
- 200 (trả về phần hồ sơ đã cập nhật):
```json
{ "id": "60d5...", "email": "user@example.com", "displayName": "...", "phone": "...", "sex": "...", "birth": "...", "avatar": "https://..." }
```
- 400 `INVALID_INPUT`

### 1.2 Cập nhật ảnh đại diện
- PUT `/profile/avatar` (Auth) – multipart/form-data
  - Form: `file` (jpeg/png, ≤ 1MB)
- 200:
```json
{ "avatarUrl": "https://..." }
```
- 400 file không hợp lệ | 413 quá dung lượng

### 1.3 Xóa tài khoản
- DELETE `/me` (Auth)
- Optional Body: `{ "password": "..." }` (nếu yêu cầu xác nhận lại)
- 204

---

## 2) Đổi mật khẩu

### 2.1 Đổi mật khẩu hiện tại
- POST `/change-password` (Auth)
- Body:
```json
{ "oldPassword": "Old@123", "newPassword": "New@123" }
```
- 200 `{ "message": "Password changed" }`
- 400 mật khẩu yếu | 401 mật khẩu cũ sai

---

## 3) Địa chỉ người dùng

### Model trả về
```json
{ "id": "addr_123", "receiver": "Tên", "detail": "Số nhà/đường", "ward": "Phường", "district": "Quận/Huyện", "province": "Tỉnh/TP", "phone": "0xxxxxxxxx", "is_default": true, "createdAt": "2025-01-03T10:20:40.123Z" }
```

### 3.1 Lấy danh sách địa chỉ
- GET `/addresses` (Auth)
- 200 `[ Address ]`

### 3.2 Thêm địa chỉ
- POST `/addresses` (Auth)
- Body (bắt buộc):
```json
{ "receiver": "...", "detail": "...", "ward": "...", "district": "...", "province": "...", "phone": "...", "is_default": false }
```
- 201 `Address`

### 3.3 Sửa địa chỉ
- PUT `/addresses/:id` (Auth)
- Body: các field như khi tạo (tùy chọn)
- 200 `Address` | 404 không tìm thấy/không sở hữu

### 3.4 Thiết lập mặc định
- PATCH `/addresses/:id/default` (Auth)
- 200 `{ "id": "...", "is_default": true }` (các địa chỉ khác phải tự động `is_default=false`)

- DELETE `/addresses/:id` (Auth)
- 204 | 404

---

## 4) Liên kết tài khoản MXH

### 4.1 Lấy trạng thái liên kết
- GET `/links` (Auth)
- 200:
```json
{ "google": true, "facebook": false }
```

### 4.2 Liên kết/Hủy liên kết Google
- POST `/links/google` (Auth)
  - Body: `{ "access_token": "..." }` hoặc `{ "id_token": "..." }`
  - 200 `{ "google": true }`
- DELETE `/links/google` (Auth) → 204

### 4.3 Liên kết/Hủy liên kết Facebook
- POST `/links/facebook` (Auth)
  - Body: `{ "access_token": "..." }`
  - 200 `{ "facebook": true }`
- DELETE `/links/facebook` (Auth) → 204

---

## 5) Cài đặt thông báo

### 5.1 Lấy cài đặt
- GET `/notification-settings` (Auth)
- 200:
```json
{ "emailNotif": true, "emailUpdate": true, "emailSale": true, "emailSurvey": true, "smsNotif": false, "smsSale": false }
```

- PUT `/notification-settings` (Auth)
- Body: cùng shape như response (tất cả boolean)
- 200 trả về cài đặt mới

---

Ghi chú: Các endpoint có sẵn theo `Auth_README.md` (POST /api/register, POST /api/login, POST /api/oauth/google, POST /api/oauth/facebook, GET /api/profile, GET /api/me) giữ nguyên không thay đổi. Tất cả endpoint trong tài liệu này đều nằm dưới base `/api`.


