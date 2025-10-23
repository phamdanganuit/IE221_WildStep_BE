

---

### **API Documentation - Shoe Shop**

**Base URL:** https://api.shoe-shop.app/api

#### **Authentication (Xác thực)**

Các endpoint yêu cầu xác thực phải được gửi kèm với một `Authorization` header theo định dạng `Bearer Token`.

*   **Header:** `Authorization`
*   **Value:** `Bearer <your_jwt_access_token>`

Token này được lấy từ kết quả trả về của các API đăng nhập (`/login`, `/oauth/google`, `/oauth/facebook`).

---

### **1. Users & Authentication**

#### **1.1. Đăng ký tài khoản mới**

*   **Endpoint:** `POST /register`
*   **Method:** `POST`
*   **Mô tả:** Đăng ký một người dùng mới bằng email và mật khẩu.
*   **Body (JSON):**
    ```json
    {
        "email": "user@example.com",
        "password": "yourstrongpassword",
        "displayName": "Nguyen Van A",
        "admin_key": "your_secret_admin_key" // (Tùy chọn, chỉ dành cho quản trị viên)
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
        "id": "60d5ecf3e7b1c3b4a8f1b1a0",
        "email": "user@example.com",
        "displayName": "Nguyen Van A",
        "role": "user"
    }
    ```
*   **Error Responses:**
    *   `400 Bad Request`: Dữ liệu không hợp lệ (thiếu email/password, email sai định dạng, mật khẩu quá ngắn).
    *   `409 Conflict`: Email đã được đăng ký.

---

#### **1.2. Đăng nhập cơ bản**

*   **Endpoint:** `POST /login`
*   **Method:** `POST`
*   **Mô tả:** Đăng nhập bằng email, mật khẩu và trả về JWT access token.
*   **Body (JSON):**
    ```json
    {
        "email": "user@example.com",
        "password": "yourstrongpassword"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "Bearer"
    }
    ```
*   **Error Response (401 Unauthorized):**
    ```json
    { "detail": "Invalid credentials" }
    ```

---

#### **1.3. Lấy thông tin hồ sơ người dùng chi tiết**

*   **Endpoint:** `GET /profile`
*   **Method:** `GET`
*   **Mô tả:** Lấy thông tin chi tiết của người dùng đang đăng nhập từ cơ sở dữ liệu, bao gồm thông tin cá nhân, các liên kết và các số liệu thống kê.
*   **Headers:** `Authorization: Bearer <your_jwt_access_token>` (Bắt buộc)
*   **Success Response (200 OK):**
    ```json
    {
        "_id": "60d5ecf3e7b1c3b4a8f1b1a0",
        "username": "nguyenvana",
        "displayName": "Nguyen Van A",
        "email": "user@example.com",
        "phone": "0987654321",
        "sex": "male",
        "birth": "2000-01-15T00:00:00",
        "avatar": "https://example.com/avatar.jpg",
        "role": "user",
        "google": true, // true nếu đã liên kết tài khoản Google
        "facebook": false, // true nếu đã liên kết tài khoản Facebook
        "addresses": [ // Danh sách ID các địa chỉ của người dùng
            "60d5ed12e7b1c3b4a8f1b1a1",
            "60d5ed1fe7b1c3b4a8f1b1a2"
        ],
        "vouchers": [], // Danh sách ID các voucher của người dùng
        "createdAt": "2025-10-22T10:00:00.000Z",
        "cartCount": 5, // Số lượng sản phẩm trong giỏ hàng
        "wishlistCount": 2, // Số lượng sản phẩm trong danh sách yêu thích
        "notificationCount": 3 // Số lượng thông báo chưa đọc
    }
    ```
*   **Error Response (401 Unauthorized / 404 Not Found):**
    *   `401`: Token không hợp lệ hoặc bị thiếu.
    *   `404`: Không tìm thấy người dùng tương ứng với token.

---

#### **1.4. Lấy thông tin payload của Token**

*   **Endpoint:** `GET /me`
*   **Method:** `GET`
*   **Mô tả:** Lấy thông tin thô được chứa trong payload của JWT. Hữu ích để kiểm tra nhanh token có hợp lệ không và chứa những thông tin gì (id, email, role).
*   **Headers:** `Authorization: Bearer <your_jwt_access_token>` (Bắt buộc)
*   **Success Response (200 OK):**
    ```json
    {
        "user": {
            "sub": "60d5ecf3e7b1c3b4a8f1b1a0", // User ID
            "email": "user@example.com",
            "role": "user",
            "iat": 1678886400, // Issued At
            "exp": 1678890000  // Expiration Time
        }
    }
    ```
*   **Error Response (401 Unauthorized):**
    ```json
    { "detail": "Missing Bearer token" }
    ```

---

#### **1.5. Đăng nhập bằng Google**

*   **Endpoint:** `POST /oauth/google`
*   **Method:** `POST`
*   **Mô tả:** Đăng nhập hoặc đăng ký thông qua tài khoản Google. Backend sẽ nhận `id_token` từ frontend, xác thực với Google và trả về JWT của hệ thống.
*   **Body (JSON):**
    ```json
    {
        "id_token": "google_id_token_from_frontend"
    }
    ```
*   **Success Response (200 OK):** (Tương tự như đăng nhập cơ bản)
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "Bearer"
    }
    ```
*   **Error Response (401 Unauthorized):**
    ```json
    { "detail": "Invalid Google token" }
    ```
---

#### **1.6. Đăng nhập bằng Facebook**

*   **Endpoint:** `POST /oauth/facebook`
*   **Method:** `POST`
*   **Mô tả:** Đăng nhập hoặc đăng ký thông qua tài khoản Facebook. Backend sẽ nhận `access_token` từ Facebook SDK (phía frontend) và trả về JWT của hệ thống.
*   **Body (JSON):**
    ```json
    {
        "access_token": "facebook_access_token_from_frontend_sdk"
    }
    ```
*   **Success Response (200 OK):** (Tương tự như đăng nhập cơ bản)
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "Bearer"
    }
    ```
*   **Error Response (401 Unauthorized):**
    ```json
    { "detail": "Invalid Facebook token" }
    ```

---

