# Admin API Implementation Summary

## Overview

This document summarizes the implemented Admin APIs for the shoe shop backend.

**Base URL**: `/api/admin`

**Authentication**: All endpoints require Bearer token with `role: "admin"`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

---

## ✅ Implemented Endpoints

### 1. Dashboard & Analytics

#### GET `/api/admin/dashboard/stats`
- **Description**: Dashboard statistics with revenue, orders, customers, products
- **Query Params**: 
  - `period`: `week` | `month` | `year` (default: month)
- **Response**: Summary stats, recent orders, revenue chart, category distribution

#### GET `/api/admin/analytics`
- **Description**: Detailed analytics
- **Query Params**: 
  - `period`: `week` | `month` | `year` (default: month)
- **Response**: Top products, customer segments, revenue analytics

---

### 2. Products Management

#### GET `/api/admin/products`
- **Description**: List all products with pagination
- **Response**: Array of products with brand, category, pricing, stock info

#### GET `/api/admin/products/:id`
- **Description**: Get product detail

#### POST `/api/admin/products`
- **Description**: Create new product
- **Required**: `name`, `categoryId`, `brandId`, `price`
- **Optional**: `slug` (auto-generated), `description`, `stock`, `discount`, `status`, `specifications`, `tags`

#### PUT `/api/admin/products/:id`
- **Description**: Update product
- **Body**: All fields optional

#### DELETE `/api/admin/products/:id`
- **Description**: Delete product

---

### 3. Brands Management

#### GET `/api/admin/brands`
- **Description**: List all brands

#### GET `/api/admin/brands/:id`
- **Description**: Get brand detail

#### POST `/api/admin/brands`
- **Description**: Create new brand
- **Required**: `name`
- **Optional**: `slug` (auto-generated), `description`, `website`, `country`, `status`

#### PUT `/api/admin/brands/:id`
- **Description**: Update brand

#### DELETE `/api/admin/brands/:id`
- **Description**: Delete brand
- **Note**: Cannot delete if brand has products

---

### 4. Categories Management

#### GET `/api/admin/categories`
- **Description**: List all categories (hierarchical: parent with children)
- **Response**: Parent categories with nested child categories

#### POST `/api/admin/categories`
- **Description**: Create new category
- **Required**: `name`, `type` (parent | child)
- **For child**: `parentId` is required
- **Optional**: `slug` (auto-generated), `description`, `status`

---

### 5. Orders Management

#### GET `/api/admin/orders`
- **Description**: List all orders
- **Response**: Orders with customer info, total, status

#### GET `/api/admin/orders/:id`
- **Description**: Get order detail with full items, shipping address

#### PATCH `/api/admin/orders/:id/status`
- **Description**: Update order status
- **Body**: `{ "status": "pending | processing | shipping | completed | cancelled" }`
- **Validation**: 
  - Cannot change from `completed` or `cancelled`
  - Auto-sets `completedDate` when status becomes `completed`

---

### 6. Customers Management

#### GET `/api/admin/customers`
- **Description**: List all customers with calculated stats
- **Response**: Customer list with:
  - `totalOrders`, `totalSpent`, `averageOrderValue`
  - `isVip`: true if totalOrders > 10
  - `status`: `blocked` | `vip` | `active` | `inactive`
    - `active`: has order in last 30 days
    - `inactive`: no order in last 30 days
    - `vip`: totalOrders > 10
    - `blocked`: manually blocked by admin

#### GET `/api/admin/customers/:id`
- **Description**: Get customer detail
- **Response**: Full customer info with:
  - Order history (last 10 orders)
  - Order statistics
  - Addresses

#### PATCH `/api/admin/customers/:id/status`
- **Description**: Update customer status (block/unblock)
- **Body**: `{ "status": "blocked" | "active" }`
- **Note**: Only `blocked` can be set manually. Other statuses are calculated.

---

## 📦 Models

### Product
- Fields: name, slug, description, original_price, discount, discount_price, stock, sold, rate, images[], brand, category, colors[], sizes[], status, specifications, tags[], created_at, updated_at
- Auto-generates: slug, discount_price
- Auto-updates: status based on stock

### Brand
- Fields: name, slug, description, logo, website, country, status, created_at, updated_at
- Auto-generates: slug

### ParentCategory / ChildCategory
- Hierarchical structure
- Fields: name, slug, description, image, status, created_at, updated_at
- ChildCategory has: parent (reference to ParentCategory)

### Order
- Fields: order_number, user, address, items[], subtotal, shipping_fee, discount, vat, total_price, voucher, payment_method, payment_status, status, notes, created_at, updated_at, completed_date
- Auto-generates: order_number (ORD-000001, ORD-000002, ...)
- Auto-sets: completed_date when status = 'completed'

### OrderItem (Embedded)
- Fields: product_id, product_name, product_image, quantity, price, total, color, size

### User (Updated)
- Added: `blocked` field (boolean) for admin to manually block users

---

## 🔐 Authentication

All admin endpoints use `@require_admin` decorator which:
1. Checks for valid Bearer token
2. Verifies user has `role = "admin"`
3. Returns 401 for invalid/expired tokens
4. Returns 403 for non-admin users

---

## 📝 Response Format

### Success Response
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

### Error Codes
- `MISSING_FIELD`: Required field missing
- `RESOURCE_NOT_FOUND`: Resource not found
- `CANNOT_DELETE`: Cannot delete due to dependencies
- `INVALID_STATUS_TRANSITION`: Invalid status change
- `CREATE_FAILED` / `UPDATE_FAILED`: Operation failed

---

## 🚧 TODO / Future Improvements

### High Priority
- [ ] Add pagination, search, filters to all list endpoints
- [ ] Implement category detail/update/delete endpoints
- [ ] Add image upload endpoints:
  - POST `/api/admin/products/:id/images`
  - POST `/api/admin/brands/:id/logo`
  - POST `/api/admin/categories/:id/image`

### Medium Priority
- [ ] Add order export functionality (CSV/Excel)
- [ ] Implement advanced filtering:
  - Products: by price range, date range, search
  - Orders: by date range, customer, payment status
  - Customers: by spending range, order count
- [ ] Add settings management APIs

### Low Priority
- [ ] Add rate limiting for admin APIs
- [ ] Implement audit logging
- [ ] Add bulk operations (bulk update status, bulk delete)
- [ ] Add data export for all entities

---

## 🧪 Testing

To test the APIs:

1. **Create admin user**:
```bash
# Register with admin key
POST /api/register
{
  "email": "admin@example.com",
  "password": "admin123",
  "admin_key": "<ADMIN_SIGNUP_KEY from .env>"
}
```

2. **Login as admin**:
```bash
POST /api/login
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

3. **Use token for admin APIs**:
```bash
GET /api/admin/dashboard/stats
Headers:
  Authorization: Bearer <token>
```

---

## 📊 Status Calculation Logic

### Customer Status
- **blocked**: `user.blocked == true` (manual)
- **vip**: `totalOrders > 10` (automatic)
- **active**: Has order in last 30 days (automatic)
- **inactive**: No order in last 30 days (automatic)

### Product Status
- **out_of_stock**: `stock == 0` (automatic)
- **low_stock**: `stock < 10 and stock > 0` (automatic)
- **active**: Default, or manually set
- **inactive**: Manually set

### Order Status Transitions
```
pending → processing → shipping → completed
   ↓          ↓           ↓
cancelled  cancelled  cancelled
```
- Cannot change from `completed` or `cancelled`

---

## 📁 Project Structure

```
products/
  ├── models.py           # Brand, Category, Product models
  ├── admin_views.py      # Products CRUD APIs
  └── admin_urls.py       # Products routes

orders/
  ├── models.py           # Order, OrderItem, Voucher models
  ├── admin_views.py      # Orders, Customers APIs
  ├── dashboard_views.py  # Dashboard, Analytics APIs
  └── admin_urls.py       # Orders, Customers routes

users/
  ├── models.py           # User model (updated with blocked field)
  └── auth.py             # require_admin decorator

config/
  └── urls.py             # Main routing (includes admin URLs)
```

---

## 🎯 Key Features

1. ✅ **Complete CRUD** for Products, Brands, Categories
2. ✅ **Order Management** with status tracking
3. ✅ **Customer Analytics** with automatic VIP detection
4. ✅ **Dashboard Statistics** with revenue, orders, customers metrics
5. ✅ **Hierarchical Categories** (parent/child structure)
6. ✅ **Auto-generated slugs** for SEO-friendly URLs
7. ✅ **Order number generation** (ORD-000001, ORD-000002, ...)
8. ✅ **Status validation** for orders and customers
9. ✅ **Admin-only access** with JWT authentication

---

**Version**: 1.0  
**Last Updated**: November 2025  
**Status**: MVP Complete - Ready for Testing

