

---

### **API Documentation - Shoe Shop**

**Base URL:** `http://127.0.0.1:8000/api`

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
*   **Mô tả:** Đăng ký một người dùng mới bằng email và mật khẩu. Có thể cung cấp `admin_key` để tạo tài khoản quản trị viên.
*   **Body (JSON):**
    ```json
    {
        "email": "user@example.com",
        "password": "yourstrongpassword",
        "full_name": "Nguyen Van A",
        "admin_key": "your_secret_admin_key" // (Optional)
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
        "id": "60d5ecf3e7b1c3b4a8f1b1a0",
        "email": "user@example.com",
        "full_name": "Nguyen Van A",
        "role": "user",
        "providers": [],
        "phone": null,
        "address": null,
        "gender": null,
        "birthday": null,
        "created_at": "2025-10-22T10:00:00.000Z"
    }
    ```
*   **Error Responses:**
    *   `400 Bad Request`: Dữ liệu không hợp lệ (thiếu email/password, email sai định dạng, mật khẩu quá ngắn).
        ```json
        { "detail": "invalid email" }
        ```
    *   `409 Conflict`: Email đã được đăng ký.
        ```json
        { "detail": "Email already registered" }
        ```

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
    {
        "detail": "Invalid credentials"
    }
    ```

---

#### **1.3. Lấy thông tin người dùng hiện tại**

*   **Endpoint:** `GET /me`
*   **Method:** `GET`
*   **Mô tả:** Lấy thông tin chi tiết của người dùng đang đăng nhập (dựa trên payload của JWT).
*   **Headers:** `Authorization: Bearer <your_jwt_access_token>` (Bắt buộc)
*   **Success Response (200 OK):**
    ```json
    {
        "user": {
            "sub": "60d5ecf3e7b1c3b4a8f1b1a0",
            "email": "user@example.com",
            "role": "user",
            "iat": 1678886400,
            "exp": 1678890000
        }
    }
    ```
*   **Error Response (401 Unauthorized):**
    ```json
    {
        "detail": "Missing Bearer token"
    }
    ```

---

#### **1.4. Đăng nhập bằng Google**

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
    {
        "detail": "Invalid Google token"
    }
    ```
---

#### **1.5. Đăng nhập bằng Facebook**

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
    {
        "detail": "Invalid Facebook token"
    }
    ```

---

