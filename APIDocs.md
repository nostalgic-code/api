# Autospares Marketplace API Documentation

This document describes the RESTful API endpoints available for frontend consumption. All endpoints return JSON responses. Authentication is required for most endpoints except public info and health checks.

---

## Authentication Endpoints (`/auth`)

### POST `/auth/register`
Register a new customer user.
- **Request Body:**
  - `customer_code` (string, required)
  - `name` (string, required)
  - `email` (string, required)
  - `phone` (string, optional)
  - `role` (string, required: `owner`, `staff`, `viewer`)
- **Response:**
  - `success` (bool)
  - `message` (string)
  - `user` (object)
  - `requires_approval` (bool)

### POST `/auth/check-email`
Check if an email is available for registration.
- **Request Body:**
  - `email` (string, required)
- **Response:**
  - `eligible` (bool)
  - `message` (string)

### POST `/auth/send-otp`
Send OTP to user's phone number (for login).
- **Request Body:**
  - `phone` (string, required)
- **Response:**
  - `success` (bool)
  - `message` (string)
  - `expires_in` (int, seconds)

### POST `/auth/verify-otp`
Verify OTP and authenticate user.
- **Request Body:**
  - `phone` (string, required)
  - `otp` (string, required)
- **Response:**
  - `success` (bool)
  - `message` (string)
  - `session_token` (string)
  - `user_type` (string: `customer_user` or `platform_user`)
  - `user` (object)

### POST `/auth/validate-session`
Validate session token and get user data.
- **Request Body:**
  - `session_token` (string, required)
- **Response:**
  - `valid` (bool)
  - `user_type` (string)
  - `user` (object)

### POST `/auth/logout`
Logout and invalidate session.
- **Request Body:**
  - `session_token` (string, required)
- **Response:**
  - `success` (bool)
  - `message` (string)

### GET `/auth/user-info`
Get current user information from session token.
- **Headers:**
  - `Authorization: Bearer <session_token>`
- **Response:**
  - `success` (bool)
  - `user` (object)
  - `user_type` (string)

---

## Admin Endpoints (`/api/admin`)
*All endpoints require platform user authentication.*

### GET `/api/admin/pending-users`
Get all pending customer users.
- **Query Params:**
  - `customer_id` (int, optional)
  - `role` (string, optional)
  - `created_after` (ISO date, optional)
- **Response:**
  - `users` (list)
  - `count` (int)

### POST `/api/admin/users/<user_id>/approve`
Approve a pending customer user.
- **Request Body:**
  - `depot_access` (list of strings, optional)
  - `custom_permissions` (object, optional)
- **Response:**
  - `success` (bool)
  - `message` (string)
  - `user` (object)

### POST `/api/admin/users/<user_id>/reject`
Reject a pending customer user.
- **Request Body:**
  - `reason` (string, required)
- **Response:**
  - `success` (bool)
  - `message` (string)
  - `reason` (string)

### GET `/api/admin/customers`
Get all customers with statistics.
- **Query Params:**
  - `status` (string, optional)
  - `type` (string, optional)
  - `search` (string, optional)
- **Response:**
  - `customers` (list)
  - `count` (int)

### PUT `/api/admin/customers/<customer_id>/status`
Update customer status.
- **Request Body:**
  - `status` (string, required)
  - `reason` (string, optional)
- **Response:**
  - `success` (bool)
  - `message` (string)
  - `customer` (object)

### PUT `/api/admin/users/<user_id>/role`
Change a user's role.
- **Request Body:**
  - `role` (string, required)
- **Response:**
  - `success` (bool)
  - `message` (string)
  - `user` (object)

### PUT `/api/admin/users/<user_id>/permissions`
Update user's custom permissions.
- **Request Body:**
  - `permissions` (object, required)
- **Response:**
  - `success` (bool)
  - `message` (string)
  - `user` (object)

### GET `/api/admin/system/stats`
Get system-wide statistics.
- **Response:**
  - `customers` (object)
  - `users` (object)
  - `depots` (object)

---

## Common Endpoints

### GET `/health`
System health check.
- **Response:**
  - `status` (string: `healthy`, `degraded`, `unhealthy`)
  - `timestamp` (string)
  - `version` (string)
  - `environment` (object)
  - `database` (object)
  - `services` (object)

### GET `/`
API information and available endpoints.
- **Response:**
  - `name` (string)
  - `version` (string)
  - `description` (string)
  - `documentation` (object)
  - `endpoints` (object)
  - `environment` (string)
  - `contact` (object)

### GET `/schema`
Get database schema information.
- **Response:**
  - `database_type` (string)
  - `environment` (string)
  - `tables` (object)
  - `statistics` (object)

### GET `/dashboard`
Serve the dashboard HTML file (for internal use).

---

**Note:** All endpoints (except `/`, `/health`, `/schema`, `/dashboard`) require authentication. Admin endpoints require platform user privileges.
