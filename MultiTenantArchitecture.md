# Multi-Tenant B2B Platform: Architecture & Implementation Guide

**Version:** 1.0  
**Date:** June 21, 2025  
**Author:** Gemini  
**Status:** Final

## 1. Introduction & Vision

This document outlines the architecture and phased implementation plan for migrating the existing platform from a single-user model to a secure, scalable, and robust multi-tenant B2B (Business-to-Business) system.

The primary goal of this architecture is to provide complete data isolation and customized experiences for each client company (referred to as a "Tenant") while enabling streamlined platform administration and management. This design establishes a clear separation of concerns between different user types and lays a solid foundation for future feature development, such as advanced analytics, tiered pricing, and customized product catalogs.

## 2. Core Architectural Concepts

The architecture is built on three fundamental principles: **Multi-Tenancy**, distinct **User Personas**, and fine-grained **Role-Based Access Control (RBAC)**.

### 2.1. Multi-Tenancy via Customer Accounts

The core of the architecture is the `Customer` entity. Each `Customer` record in our database represents a single, isolated Tenant. All data relevant to a specific client—including their users, orders, quotes, and activity—will be directly linked to their unique `Customer` record. This ensures that one customer can never access the data of another.

### 2.2. User Personas: The Two Key Roles

To ensure security and clarity, the system will distinguish between two fundamentally different types of users:

- **Platform Users**: These are members of our internal team (e.g., administrators, support staff, developers). They are responsible for:
  - Managing the entire platform
  - Approving new customers and users
  - Monitoring system health
  - Providing support
  
  > They are not customers themselves and exist outside the tenant structure.

- **Customer Users**: These are the employees of our client companies (the Tenants). They are responsible for:
  - Placing orders
  - Viewing products
  - Managing their company's account settings
  
  > Every `CustomerUser` belongs to one, and only one, `Customer`.

### 2.3. Role-Based Access Control (RBAC) & Permissions

Authorization within the platform is handled by a flexible, multi-layered RBAC system. A user's ability to perform actions is determined by a combination of three factors:

1. **Role**: A high-level designation (e.g., `Owner`, `Staff`, `Viewer`) that provides a baseline for permissions.

2. **Permission Codes**: Reusable, template-based permission sets (e.g., `CR101` for Owners) that can be assigned to users to standardize access levels across the platform.

3. **Granular Access Control**:
   - **Permissions (JSON)**: A flexible JSON field allows for custom, user-specific overrides to the default permissions granted by their role or code.
   - **Depot Access (JSON)**: A list of specific depot or warehouse codes that restricts a user's view of products, inventory, and fulfillment options to only their assigned locations.

## 3. Phased Implementation Guide

The migration will be executed in four logical phases, starting with the database foundation and progressively building up the application logic.

### Phase 1: Database Schema & Data Modeling

**Objective**: To establish a new database schema that physically represents the multi-tenant architecture and replaces the obsolete single-user model.

#### Guideline 1.1: Establish Customer Tenancy

The first step is to create the `customers` table. This table will serve as the central anchor for each tenant.

Key fields:
- `customer_code` - Links to external ERP systems
- `status` - Critical for administrative onboarding workflow (e.g., `pending`, `approved`)

#### Guideline 1.2: Differentiate User Types

The existing `users` table will be replaced by two new, distinct tables:

1. **`customer_users`** table
   - Contains a non-negotiable foreign key to the `customers` table
   - Enforces the rule that every customer user must belong to a tenant

2. **`platform_users`** table
   - For internal team members
   - Exists outside the tenant structure

> This separation is a crucial security measure.

#### Guideline 1.3: Standardize Permissions & Locations

To support the RBAC system, two new lookup tables will be created:

1. **`permission_codes`** table
   - Pre-populated with standardized permissions (e.g., "Owner", "Staff")
   
2. **`depots`** table
   - Pre-populated with location data (e.g., "Johannesburg", "Cape Town")

These tables allow administrators to assign consistent access rights easily.

#### Guideline 1.4: Implement Polymorphic Sessions

To handle authentication from two different user tables gracefully:

- The `user_sessions` table will be designed to be polymorphic
- Uses a `user_id` field and a `user_type` field (containing either `'customer_user'` or `'platform_user'`)
- Allows a single session token to be traced back to the correct user record in the correct table

**Implementation Task**: This phase will be executed using a database migration tool (e.g., Flask-Migrate). Developers will define the new database models in the application code, and the tool will generate and apply the necessary SQL scripts to alter the database schema without data loss.

### Phase 2: Authentication & Registration Logic

**Objective**: To refactor the core authentication services and API endpoints to support the new user structure, registration flow, and login process.

#### Guideline 2.1: Implement the New Registration Flow

A new API endpoint for user registration will be created. The business logic must follow these steps:

1. The prospective user submits their company's `customer_code`
2. The system validates this code against the `customers` table
3. If the customer exists and is active, the user can proceed to submit their personal details
4. A new record is created in the `customer_users` table with a default status of `pending`

> The system must clearly communicate to the user that their account has been created but requires administrative approval before they can log in.

#### Guideline 2.2: Unify the OTP Login Process

The login logic will be updated to handle authentication for both platform and customer users:

1. When a phone number is submitted for OTP generation, the system queries both tables:
   - `customer_users`
   - `platform_users`

2. If the user is found in the `customer_users` table:
   - A multi-level validation check is performed
   - Both the user's status and their parent customer's status must be `approved`
   - If either is not, the login attempt is rejected

3. Only after all checks pass will the system proceed with sending the OTP

#### Guideline 2.3: Design a Secure & Informative Session Payload

Upon successful login, the API will return a detailed JSON object to the frontend. This payload is critical for the UI to render the correct user experience.

Payload contents:
- Session token
- Clear `user_type` identifier
- For customer users:
  - Calculated "effective permissions" (merged object of base and custom permissions)
  - List of accessible depots

### Phase 3: Authorization Middleware & Endpoint Security

**Objective**: To secure all relevant API endpoints, ensuring they are only accessible to authenticated users with the appropriate permissions.

#### Guideline 3.1: Develop Token Authentication Middleware

A primary middleware decorator (`@token_required`) will be developed with the following responsibilities:

- Validate the session token sent in the request header
- If valid: Fetch the corresponding user object and attach it to the request context
- If invalid or missing: Reject the request with a `401 Unauthorized` error

#### Guideline 3.2: Develop Permission Authorization Middleware

A second, specialized decorator (`@permission_required`) will be created:

- Runs after the token middleware
- Inspects the user object
- Checks if the user's "effective permissions" contain the specific right required
- If permission is absent: Reject with a `403 Forbidden` error

**Implementation Task**: Developers will systematically apply these decorators to all API endpoints that require authentication and authorization, effectively locking down the application and enforcing the business rules defined in the RBAC system.

### Phase 4: Platform Administration Module

**Objective**: To build a dedicated set of services and secure endpoints for platform administrators to manage the system.

#### Guideline 4.1: Create a Dedicated Admin Service Layer

All business logic related to administrative tasks will be encapsulated within a dedicated `AdminService`.

Administrative tasks include:
- Approving users
- Managing customers
- Assigning roles

> This centralizes administrative logic and keeps it separate from customer-facing services.

#### Guideline 4.2: Build Secure Admin API Endpoints

A new API blueprint (e.g., `/api/admin`) will be created to expose the functionalities of the `AdminService`.

These endpoints will allow the administrative frontend to perform actions like:
- Fetching a list of pending users
- Sending approval commands
- Managing system configurations

#### Guideline 4.3: Enforce Strict Access Control

Every endpoint within the admin module must be secured with:

1. The `@token_required` decorator
2. An additional check to ensure the logged-in user is a `PlatformUser`

> This prevents any possibility of a `CustomerUser`, regardless of their permissions, accessing platform-level administrative functions.