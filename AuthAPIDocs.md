# Authentication API Documentation

## Overview

The Authentication API provides secure access to the marketplace application through multiple authentication methods including password-based login, phone-based OTP authentication, and session management. The system supports multi-tenant architecture with role-based access control.

## Base URL

```
https://{BASE_URL}/api/auth
```

## Authentication Methods

1. **Password Authentication**: Email and password-based login
2. **OTP Authentication**: Phone number and one-time password verification
3. **Session Token**: Bearer token authentication for subsequent requests

## Endpoints

### 1. Register New Customer User

Register a new customer user with company validation.

```http
POST /auth/register
```

#### Request Body

```json
{
    "full_name": "John Doe",
    "email": "john@company.com",
    "password": "securepassword123",
    "phone": "+27123456789",
    "customer_code": "CUST001",
    "customer_name": "ABC Company Ltd",
    "customer_account_number": "ACC12345"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | Yes | User's full name |
| `email` | string | Yes | Valid email address (will be lowercased) |
| `password` | string | Yes | Minimum 8 characters |
| `phone` | string | Yes | Phone number with country code |
| `customer_code` | string | Yes | Company's customer code |
| `customer_name` | string | Yes | Company name for validation |
| `customer_account_number` | string | Yes | Company account number for validation |

#### Success Response

```http
201 Created
```

```json
{
    "success": true,
    "message": "Registration successful. Your account is pending approval from your company administrator.",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@company.com",
        "phone": "+27123456789",
        "role": "owner",
        "status": "pending",
        "customer_name": "ABC Company Ltd"
    }
}
```

#### Error Responses

```http
400 Bad Request
```

```json
{
    "success": false,
    "message": "All fields are required: full name, email, password, phone, customer code, customer name, and account number",
    "error_code": "MISSING_FIELDS"
}
```

```http
409 Conflict
```

```json
{
    "success": false,
    "message": "Email address is already registered",
    "error_code": "EMAIL_EXISTS"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `MISSING_FIELDS` | Required fields are missing |
| `INVALID_EMAIL` | Email format is invalid |
| `INVALID_PHONE` | Phone number format is invalid |
| `WEAK_PASSWORD` | Password is less than 8 characters |
| `EMAIL_EXISTS` | Email is already registered |
| `PHONE_EXISTS` | Phone number is already registered |
| `REGISTRATION_ERROR` | General registration failure |

### 2. Login with Email and Password

Authenticate using email and password credentials.

```http
POST /auth/login
```

#### Request Body

```json
{
    "email": "john@company.com",
    "password": "securepassword123"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email address |
| `password` | string | Yes | User's password |

#### Success Response

```http
200 OK
```

```json
{
    "success": true,
    "message": "Authentication successful",
    "session_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_type": "customer_user",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@company.com",
        "phone": "+27123456789",
        "role": "owner",
        "status": "approved",
        "customer": {
            "id": 10,
            "name": "ABC Company Ltd",
            "code": "CUST001",
            "account_number": "ACC12345",
            "status": "approved"
        },
        "permissions": {
            "view_products": true,
            "place_orders": true,
            "view_orders": true
        },
        "depot_access": ["JHB001", "CPT002"]
    }
}
```

#### Error Responses

```http
401 Unauthorized
```

```json
{
    "success": false,
    "message": "Invalid email or password",
    "error_code": "INVALID_CREDENTIALS"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `MISSING_CREDENTIALS` | Email or password missing |
| `INVALID_CREDENTIALS` | Invalid email or password |
| `USER_NOT_APPROVED` | User account not approved |
| `CUSTOMER_NOT_ACTIVE` | Customer account not active |
| `AUTH_ERROR` | General authentication error |

### 3. Send OTP

Send a one-time password to user's registered phone number.

```http
POST /auth/send-otp
```

#### Request Body

```json
{
    "phone": "+27123456789"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | string | Yes | Registered phone number with country code |

#### Success Response

```http
200 OK
```

```json
{
    "success": true,
    "message": "OTP sent to +27123456789",
    "expires_in": 300
}
```

#### Error Responses

```http
403 Forbidden
```

```json
{
    "success": false,
    "message": "User not found. Please contact administrator.",
    "error_code": "USER_NOT_FOUND"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `MISSING_PHONE` | Phone number not provided |
| `INVALID_PHONE` | Invalid phone number format |
| `USER_NOT_FOUND` | Phone number not registered |
| `USER_NOT_APPROVED` | User account not approved |
| `CUSTOMER_NOT_ACTIVE` | Customer account not active |
| `SMS_FAILED` | SMS delivery failed |

### 4. Verify OTP

Verify the OTP and authenticate the user.

```http
POST /auth/verify-otp
```

#### Request Body

```json
{
    "phone": "+27123456789",
    "otp": "123456"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | string | Yes | Phone number that received OTP |
| `otp` | string | Yes | 6-digit OTP code |

#### Success Response

```http
200 OK
```

```json
{
    "success": true,
    "message": "Authentication successful",
    "session_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_type": "customer_user",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@company.com",
        "phone": "+27123456789",
        "role": "admin",
        "customer": {
            "id": 10,
            "name": "ABC Company Ltd",
            "code": "CUST001"
        },
        "permissions": {
            "view_products": true,
            "place_orders": true,
            "manage_users": true
        }
    }
}
```

#### Error Responses

```http
400 Bad Request
```

```json
{
    "success": false,
    "message": "Invalid OTP. Please try again.",
    "error_code": "INVALID_OTP"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `MISSING_PHONE` | Phone number not provided |
| `MISSING_OTP` | OTP not provided |
| `OTP_EXPIRED` | OTP has expired (5 minutes) |
| `INVALID_OTP` | Incorrect OTP |
| `TOO_MANY_ATTEMPTS` | Exceeded 3 attempts |
| `USER_NOT_FOUND` | User not found |

### 5. Validate Session

Validate a session token and retrieve user information.

```http
POST /auth/validate-session
```

#### Request Body

```json
{
    "session_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_token` | string | Yes | Active session token |

#### Success Response

```http
200 OK
```

```json
{
    "valid": true,
    "user_type": "customer_user",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@company.com",
        "role": "owner",
        "customer": {
            "id": 10,
            "name": "ABC Company Ltd"
        },
        "permissions": {
            "view_products": true,
            "place_orders": true
        }
    }
}
```

#### Error Response

```http
401 Unauthorized
```

```json
{
    "valid": false,
    "error": "Invalid or expired session"
}
```

### 6. Logout

Invalidate the current session token.

```http
POST /auth/logout
```

#### Request Body

```json
{
    "session_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Success Response

```http
200 OK
```

```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

### 7. Get User Information

Retrieve current user information using bearer token authentication.

```http
GET /auth/user-info
```

#### Request Headers

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Success Response

```http
200 OK
```

```json
{
    "success": true,
    "user_type": "customer_user",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@company.com",
        "phone": "+27123456789",
        "role": "admin",
        "status": "approved",
        "customer": {
            "id": 10,
            "name": "ABC Company Ltd",
            "code": "CUST001"
        },
        "permissions": {
            "view_products": true,
            "place_orders": true,
            "manage_users": true
        },
        "depot_access": ["JHB001", "CPT002"]
    }
}
```

#### Error Response

```http
401 Unauthorized
```

```json
{
    "error": "Invalid or expired session"
}
```

## User Types

The API supports two user types:

1. **customer_user**: Regular customers with company associations
2. **platform_user**: Internal platform administrators

## User Roles (Customer Users)

- **owner**: Company owner with full permissions
- **admin**: Administrator with user management capabilities
- **user**: Standard user with basic permissions

## User Status

- **pending**: Awaiting approval
- **approved**: Active and can access the system
- **suspended**: Temporarily disabled
- **inactive**: Permanently disabled

## Session Management

- Session tokens expire after 24 hours
- Each successful authentication clears previous sessions
- Sessions must be validated for protected endpoints

## Rate Limiting

- OTP requests: 5 per phone number per hour
- Login attempts: 10 per email per hour
- General API calls: 100 per minute per IP

## Security Considerations

1. All passwords must be at least 8 characters
2. OTPs expire after 5 minutes
3. Maximum 3 OTP verification attempts
4. Phone numbers must include country code
5. Email addresses are case-insensitive
6. All communications should use HTTPS

## Error Handling

All error responses follow a consistent format:

```json
{
    "success": false,
    "message": "Human-readable error message",
    "error_code": "MACHINE_READABLE_CODE"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `409`: Conflict
- `500`: Internal Server Error