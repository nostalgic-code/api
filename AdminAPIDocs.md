# Admin API Documentation

## Overview

The Admin API provides secure endpoints for platform administration tasks. All endpoints require platform user authentication and are designed for internal administrative operations including user management, customer management, and system monitoring.

## Base URL

```
https://api.yourdomain.com/api/v1/admin
```

## Authentication

All admin endpoints require:
1. Valid session token in the Authorization header
2. User must be a platform user (not a customer user)

```http
Authorization: Bearer <session_token>
```

## Error Response Format

All error responses follow a consistent format:

```json
{
    "error": "Human-readable error message",
    "code": "MACHINE_READABLE_CODE"
}
```

## Endpoints

### User Management

#### 1. Get All Users

Retrieve users with comprehensive filtering and pagination.

```http
GET /admin/users
```

##### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by status (comma-separated for multiple) | `pending,approved` |
| `customer_id` | string | Filter by customer ID (comma-separated for multiple) | `1,2,3` |
| `role` | string | Filter by role (comma-separated for multiple) | `owner,staff` |
| `search` | string | Search by name or email | `john` |
| `created_after` | string | ISO date string | `2025-01-01` |
| `created_before` | string | ISO date string | `2025-12-31` |
| `sort` | string | Sort field (prefix with - for desc) | `-created_at` |
| `page` | integer | Page number | `1` |
| `limit` | integer | Items per page (max: 100) | `20` |

##### Success Response

```http
200 OK
```

```json
{
    "data": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@company.com",
            "phone": "+27123456789",
            "role": "owner",
            "status": "pending",
            "permission_code": "RESTRICTED",
            "depot_access": [],
            "customer": {
                "id": 10,
                "name": "ABC Company",
                "code": "CUST001",
                "status": "approved"
            },
            "created_at": "2025-06-01T10:00:00Z",
            "updated_at": "2025-06-01T10:00:00Z",
            "last_login": null,
            "approval_eligibility": {
                "status": "ELIGIBLE",
                "validation_date": "2025-06-01T10:00:00Z",
                "mismatches": [],
                "warnings": []
            }
        }
    ],
    "meta": {
        "total": 100,
        "page": 1,
        "limit": 20,
        "pages": 5,
        "filters_applied": {
            "status": "pending",
            "sort": "-created_at"
        }
    }
}
```

#### 2. Get User Details

Retrieve detailed information for a specific user.

```http
GET /admin/users/{user_id}
```

##### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

##### Success Response

```http
200 OK
```

```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@company.com",
    "phone": "+27123456789",
    "role": "owner",
    "status": "pending",
    "permission_code": "RESTRICTED",
    "depot_access": ["JHB", "CPT"],
    "customer": {
        "id": 10,
        "name": "ABC Company",
        "code": "CUST001",
        "status": "approved"
    },
    "created_at": "2025-06-01T10:00:00Z",
    "updated_at": "2025-06-01T10:00:00Z",
    "details": {
        "permission_code_details": {
            "code": "RESTRICTED",
            "name": "Restricted Access",
            "permissions": {
                "view_products": true,
                "place_orders": false
            }
        },
        "depot_names": [
            {"code": "JHB", "name": "Johannesburg"},
            {"code": "CPT", "name": "Cape Town"}
        ],
        "activity_summary": {
            "last_login": "2025-06-20T14:30:00Z",
            "login_count": 15,
            "last_order": "2025-06-19T10:00:00Z"
        },
        "approval_info": null,
        "approval_eligibility_details": {
            "status": "ELIGIBLE",
            "validation_summary": "All checks passed",
            "issues": []
        }
    }
}
```

##### Error Response

```http
404 Not Found
```

```json
{
    "error": "User with ID 999 not found",
    "code": "USER_NOT_FOUND"
}
```

#### 3. Perform User Action

Approve or reject a pending user.

```http
POST /admin/users/{user_id}/actions
```

##### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

##### Request Body

```json
{
    "action": "approve",
    "depot_access": ["JHB", "CPT"],
    "permission_code": "STANDARD"
}
```

Or for rejection:

```json
{
    "action": "reject",
    "reason": "Invalid company information provided"
}
```

##### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | Either "approve" or "reject" |
| `reason` | string | Required for reject | Reason for rejection |
| `depot_access` | array | Optional for approve | List of depot codes |
| `permission_code` | string | Optional for approve | Permission code (defaults based on role) |

##### Success Response

```http
200 OK
```

```json
{
    "success": true,
    "message": "User approved successfully",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@company.com",
        "status": "approved",
        "role": "owner",
        "permission_code": "STANDARD",
        "depot_access": ["JHB", "CPT"]
    }
}
```

##### Error Responses

```http
400 Bad Request
```

```json
{
    "success": false,
    "error": "User status is approved, not pending",
    "code": "INVALID_STATUS"
}
```

#### 4. Update User

Update user attributes including role, permissions, and depot access.

```http
PATCH /admin/users/{user_id}
```

##### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

##### Request Body

```json
{
    "role": "admin",
    "permission_code": "ADMIN",
    "depot_access": ["JHB", "CPT", "DBN"]
}
```

##### Request Fields (all optional)

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | New role (owner, admin, staff, viewer) |
| `permission_code` | string | New permission code |
| `depot_access` | array | List of depot codes |

##### Success Response

```http
200 OK
```

```json
{
    "success": true,
    "message": "User updated successfully",
    "updated_fields": ["role", "permission_code", "permissions", "depot_access"],
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@company.com",
        "role": "admin",
        "permission_code": "ADMIN",
        "depot_access": ["JHB", "CPT", "DBN"]
    }
}
```

### Customer Management

#### 5. Get All Customers

Retrieve customers with filtering and pagination.

```http
GET /admin/customers
```

##### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by status (comma-separated) | `pending,approved` |
| `type` | string | Filter by type (comma-separated) | `standard,premium` |
| `search` | string | Search by name, code, or account number | `ABC` |
| `created_after` | string | ISO date string | `2025-01-01` |
| `created_before` | string | ISO date string | `2025-12-31` |
| `has_pending_users` | boolean | Filter customers with pending users | `true` |
| `sort` | string | Sort field (prefix with - for desc) | `-created_at` |
| `page` | integer | Page number | `1` |
| `limit` | integer | Items per page (max: 100) | `20` |

##### Success Response

```http
200 OK
```

```json
{
    "data": [
        {
            "id": 1,
            "code": "CUST001",
            "name": "ABC Company",
            "account_number": "ACC12345",
            "status": "approved",
            "type": "enterprise",
            "user_stats": {
                "total": 10,
                "approved": 7,
                "pending": 2,
                "rejected": 1
            },
            "created_at": "2025-06-01T10:00:00Z",
            "updated_at": "2025-06-01T10:00:00Z"
        }
    ],
    "meta": {
        "total": 50,
        "page": 1,
        "limit": 20,
        "pages": 3,
        "filters_applied": {
            "status": "approved",
            "has_pending_users": "true"
        }
    }
}
```

#### 6. Get Customer Details

Retrieve detailed information for a specific customer.

```http
GET /admin/customers/{customer_id}
```

##### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | integer | Yes | Customer ID |

##### Success Response

```http
200 OK
```

```json
{
    "id": 1,
    "code": "CUST001",
    "name": "ABC Company",
    "account_number": "ACC12345",
    "status": "approved",
    "type": "enterprise",
    "user_stats": {
        "total": 10,
        "approved": 7,
        "pending": 2,
        "rejected": 1
    },
    "details": {
        "user_breakdown": {
            "owner": {
                "total": 1,
                "approved": 1,
                "pending": 0,
                "rejected": 0
            },
            "admin": {
                "total": 2,
                "approved": 2,
                "pending": 0,
                "rejected": 0
            },
            "staff": {
                "total": 5,
                "approved": 4,
                "pending": 1,
                "rejected": 0
            },
            "viewer": {
                "total": 2,
                "approved": 0,
                "pending": 1,
                "rejected": 1
            }
        },
        "depot_coverage": [
            {
                "code": "JHB",
                "name": "Johannesburg",
                "user_count": 3
            },
            {
                "code": "CPT",
                "name": "Cape Town",
                "user_count": 2
            }
        ],
        "recent_activity": [
            {
                "type": "user_approved",
                "timestamp": "2025-06-20T14:30:00Z",
                "description": "User john@abc.com approved"
            }
        ],
        "owner_info": {
            "id": 1,
            "name": "John Doe",
            "email": "john@abc.com",
            "phone": "+27123456789",
            "status": "approved"
        }
    },
    "created_at": "2025-06-01T10:00:00Z",
    "updated_at": "2025-06-20T14:30:00Z"
}
```

#### 7. Update Customer

Update customer attributes (primarily status).

```http
PATCH /admin/customers/{customer_id}
```

##### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | integer | Yes | Customer ID |

##### Request Body

```json
{
    "status": "on_hold",
    "reason": "Non-payment of invoices"
}
```

##### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | New status (approved, on_hold, suspended) |
| `reason` | string | No | Reason for status change |

##### Success Response

```http
200 OK
```

```json
{
    "success": true,
    "message": "Customer updated successfully",
    "updated_fields": ["status"],
    "customer": {
        "id": 1,
        "code": "CUST001",
        "name": "ABC Company",
        "status": "on_hold",
        "account_number": "ACC12345",
        "type": "enterprise",
        "user_stats": {
            "total": 10,
            "approved": 7,
            "pending": 2,
            "rejected": 1
        }
    }
}
```

#### 8. Get Customer Users

Retrieve all users for a specific customer with filtering.

```http
GET /admin/customers/{customer_id}/users
```

##### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | integer | Yes | Customer ID |

##### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by user status | `pending` |
| `role` | string | Filter by user role | `owner` |
| `search` | string | Search by name or email | `john` |
| `sort` | string | Sort field (prefix with - for desc) | `-created_at` |
| `page` | integer | Page number | `1` |
| `limit` | integer | Items per page | `20` |

##### Success Response

```http
200 OK
```

```json
{
    "data": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@abc.com",
            "phone": "+27123456789",
            "role": "owner",
            "status": "approved",
            "permission_code": "ADMIN",
            "depot_access": ["JHB", "CPT"],
            "created_at": "2025-06-01T10:00:00Z",
            "last_login": "2025-06-25T08:30:00Z"
        }
    ],
    "meta": {
        "total": 10,
        "page": 1,
        "limit": 20,
        "pages": 1,
        "filters_applied": {
            "status": "approved"
        }
    },
    "customer": {
        "id": 1,
        "name": "ABC Company",
        "code": "CUST001",
        "status": "approved"
    }
}
```

### System Information

#### 9. Get System Statistics

Retrieve system-wide statistics for the dashboard.

```http
GET /admin/system/stats
```

##### Success Response

```http
200 OK
```

```json
{
    "customers": {
        "total": 50,
        "approved": 45,
        "pending": 3,
        "suspended": 2
    },
    "users": {
        "customer_users": {
            "total": 250,
            "approved": 200,
            "pending": 30,
            "rejected": 20
        },
        "platform_users": {
            "total": 10,
            "admins": 3
        }
    },
    "depots": {
        "total": 5,
        "active": 5
    },
    "permission_codes": {
        "total": 5
    }
}
```

#### 10. Get Recent Activity

Retrieve recent administrative activities.

```http
GET /admin/system/recent-activity
```

##### Query Parameters

| Parameter | Type | Description | Default | Max |
|-----------|------|-------------|---------|-----|
| `limit` | integer | Number of activities to return | 10 | 50 |

##### Success Response

```http
200 OK
```

```json
{
    "activities": [
        {
            "id": "user_approved_123",
            "type": "user_approved",
            "message": "User john@company.com was approved",
            "timestamp": "2025-06-25T14:30:00Z",
            "user_email": "john@company.com",
            "customer_name": "ABC Company"
        },
        {
            "id": "user_rejected_124",
            "type": "user_rejected",
            "message": "User jane@company.com was rejected",
            "timestamp": "2025-06-25T13:15:00Z",
            "user_email": "jane@company.com",
            "customer_name": "XYZ Corp"
        },
        {
            "id": "customer_updated_10",
            "type": "customer_updated",
            "message": "Customer ABC Company status was updated",
            "timestamp": "2025-06-25T12:00:00Z",
            "customer_name": "ABC Company",
            "customer_status": "on_hold"
        }
    ],
    "count": 3
}
```

## Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_PARAMETER` | Invalid query parameter value |
| `USER_NOT_FOUND` | User ID does not exist |
| `CUSTOMER_NOT_FOUND` | Customer ID does not exist |
| `ACTION_REQUIRED` | Action field missing in request |
| `INVALID_STATUS` | Invalid status for the requested operation |
| `NO_DATA` | No update data provided |
| `FETCH_ERROR` | Database fetch operation failed |
| `UPDATE_ERROR` | Database update operation failed |
| `ACTION_ERROR` | Action execution failed |
| `STATS_ERROR` | Statistics calculation failed |
| `ACTIVITY_ERROR` | Activity retrieval failed |

## Rate Limiting

Admin endpoints have the following rate limits:
- 1000 requests per hour per user
- 100 requests per minute per user

## Security Considerations

1. All endpoints require platform user authentication
2. Customer users cannot access admin endpoints
3. All actions are logged with the acting user's ID
4. Sensitive data is filtered based on permissions
5. Database transactions are rolled back on errors

## Pagination

All list endpoints support pagination with:
- Default page size: 20 items
- Maximum page size: 100 items
- Page numbering starts at 1
- Total count is included in meta response

## Filtering

List endpoints support multiple filter types:
- Single value filters: `status=pending`
- Multi-value filters: `status=pending,approved`
- Date range filters: `created_after` and `created_before`
- Text search: `search` parameter
- Sorting: `sort` parameter (prefix with `-` for descending)