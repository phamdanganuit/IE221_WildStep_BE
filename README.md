
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
*   **Mô tả:** Đăng ký một người dùng mới bằng email và mật khẩu.
*   **Body (JSON):**
    ```json
    {
        "email": "user@example.com",
        "password": "yourstrongpassword",
        "full_name": "Nguyen Van A"
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
        "id": "60d5ecf3e7b1c3b4a8f1b1a0",
        "email": "user@example.com",
        "full_name": "Nguyen Van A",
        "role": "user",
        "phone": null,
        "address": null,
        "providers": []
    }
    ```
*   **Error Response (400 Bad Request):**
    ```json
    {
        "message": "Email already exists"
    }
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
        "user": {
            "id": "60d5ecf3e7b1c3b4a8f1b1a0",
            "email": "user@example.com",
            "full_name": "Nguyen Van A",
            "role": "user"
        }
    }
    ```
*   **Error Response (401 Unauthorized):**
    ```json
    {
        "message": "Invalid credentials"
    }
    ```

---

#### **1.3. Lấy thông tin người dùng hiện tại**

*   **Endpoint:** `GET /me`
*   **Method:** `GET`
*   **Mô tả:** Lấy thông tin chi tiết của người dùng đang đăng nhập (dựa trên JWT).
*   **Headers:** `Authorization: Bearer <your_jwt_access_token>` (Bắt buộc)
*   **Success Response (200 OK):**
    ```json
    {
        "id": "60d5ecf3e7b1c3b4a8f1b1a0",
        "email": "user@example.com",
        "full_name": "Nguyen Van A",
        "role": "user",
        "phone": "0987654321",
        "address": "123 Duong ABC, Quan 1, TP. HCM",
        "providers": [
            {
                "provider": "google",
                "provider_user_id": "109876543210987654321"
            }
        ]
    }
    ```
*   **Error Response (401 Unauthorized):**
    ```json
    {
        "message": "Authorization header is missing"
    }
    ```

---

#### **1.4. Đăng nhập bằng Google**

*   **Endpoint:** `POST /oauth/google`
*   **Method:** `POST`
*   **Mô tả:** Đăng nhập hoặc đăng ký thông qua tài khoản Google. Backend sẽ nhận `auth_token` từ frontend, xác thực với Google và trả về JWT của hệ thống.
*   **Body (JSON):**
    ```json
    {
        "auth_token": "google_authorization_code_or_id_token_from_frontend"
    }
    ```
*   **Success Response (200 OK):** (Tương tự như đăng nhập cơ bản)
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user": {
            "id": "60d5ecf3e7b1c3b4a8f1b1a1",
            "email": "google.user@gmail.com",
            "full_name": "Google User",
            "role": "user"
        }
    }
    ```
*   **Error Response (400 Bad Request):**
    ```json
    {
        "message": "Invalid Google token"
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
        "user": {
            "id": "60d5ecf3e7b1c3b4a8f1b1a2",
            "email": "facebook.user@example.com",
            "full_name": "Facebook User",
            "role": "user"
        }
    }
    ```
*   **Error Response (400 Bad Request):**
    ```json
    {
        "message": "Invalid Facebook token"
    }
    ```

---

Sau khi bạn đã sao chép và tạo file tài liệu xong, hãy nói **"OK, NEXT"** để chúng ta bắt đầu xây dựng API `/api/profile`.
