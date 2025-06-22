# Admin Dashboard Guideline

## 1. Vision & Guiding Principles

The primary vision for the Admin Dashboard is to create a centralized command center for platform administrators. It must be efficient, intuitive, and powerful, enabling administrators to manage the entire user and customer lifecycle with minimal friction.

**Guiding Principles:**
- **Clarity over Clutter:** Every piece of information should have a purpose. Prioritize a clean interface, using whitespace and clear typography to make data easily digestible.
- **Action-Oriented Design:** The UI should make the most common administrative tasks (like approving users) obvious and accessible.
- **Data-Driven Insights:** The dashboard should provide a high-level overview of the platform's health and growth, not just management tools.
- **Seamless Workflows:** Administrators should move logically from one task to the next without getting lost (e.g., from viewing a pending user to viewing that user's parent company in a single click).

---

## 2. Proposed Layout & UI/UX Design

To achieve a professional and clean look, adopt a standard, highly effective three-part layout:

### A. Main Navigation Sidebar (Left, Fixed)
- **Purpose:** Primary navigation hub, permanently visible on the left.
- **Contents:**
  - Dashboard (Home/Stats icon)
  - User Management (Users icon)
  - Customer Management (Building/Company icon)
  - System Health (Heartbeat/Server icon)
  - Settings/Profile (Gear/User icon) at the bottom

### B. Top Header Bar (Top, Fixed)
- **Purpose:** Provides context and quick-access tools.
- **Contents:**
  - Global Search Bar (Left/Center): Instantly find any user or customer.
  - Notification Center (Right): Bell icon with badge for new notifications (e.g., users pending approval).
  - Admin User Profile (Far Right): Avatar/dropdown with admin's name, profile link, and "Logout" button.

### C. Main Content Area (Center, Dynamic)
- **Purpose:** Displays content for the selected module (data tables, forms, charts, detailed views).

---

## 3. Core Functional Modules (Based on API)

Essential features of the dashboard, mapped from API endpoints:

### 3.1. Main Dashboard ("At-a-Glance" View)
- **Objective:** High-level, real-time overview of platform status.
- **API Endpoint:** `GET /api/admin/system/stats`
- **Key Components:**
  - **Statistic "Stat" Cards:**
    - Total Customers
    - Total Active Users
    - Pending User Approvals (Actionable, styled with primary color, links to User Management approval queue)
    - Total Depots
  - **Recent Activity Feed:** Last 5-10 admin actions (e.g., "Admin John Doe approved user lisa@example.com"). *(Enhancement: requires new logging endpoint)*
  - **Charts & Graphs:**
    - Line chart: "New User Registrations Over the Last 30 Days"
    - Pie chart: "Customer Status Breakdown" (Approved, Pending, On Hold)

### 3.2. User Management (Core Workflow)
- **Objective:** Manage the entire lifecycle of customer users (approval, role, permissions).
- **API Endpoints:**
  - `GET /pending-users`
  - `POST /users/.../approve`
  - `POST /users/.../reject`
  - `PUT /users/.../role`
  - `PUT /users/.../permissions`
- **Layout & Flow:**
  - **Tabbed Interface:**
    - Pending Approval (default)
    - Active Users (searchable)
    - Rejected Users (archive)
  - **Data Table:** Sortable, filterable for each view.
    - **Pending Users Table Columns:** User Name, User Email, Associated Customer, Role Requested, Date Registered, Actions
  - **Approval/Rejection Workflow:**
    - "Approve" opens modal with user details, depot_access, custom_permissions (uses `POST /api/admin/users/<user_id>/approve`).
    - "Reject" opens modal for rejection reason (required by API).
    - On success: user removed from pending list in real-time, show success notification ("toast").
  - **Managing Active Users:**
    - Click user to view details, update role or permissions (uses respective PUT endpoints).

### 3.3. Customer (Tenant) Management
- **Objective:** View, manage, and audit all customer accounts.
- **API Endpoints:**
  - `GET /api/admin/customers`
  - `PUT /customers/<customer_id>/status`
- **Layout & Flow:**
  - **Main Customer Data Table:**
    - Columns: Customer Name, Customer Code, Status (colored badge), Type, Date Joined, User Count
    - Filtering: By status, type, and search bar
  - **Detailed Customer View:**
    - Header with core details and status control (uses PUT endpoint)
    - List/table of all customer_users
    - Other info (e.g., order history, account stats) as future enhancements

### 3.4. System Health
- **Objective:** Quick diagnosis of system issues for technical admins.
- **API Endpoint:** `GET /health`
- **Layout & Flow:**
  - Display key-value pairs from API response
  - Overall status ("healthy", "degraded") with color-coded icon
  - Sub-statuses (database, services) in collapsible sections (accordions)