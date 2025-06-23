# Customer Portal Guidelines

## 1. Vision & Guiding Principles

The Customer Portal is the primary interface for your clients. Its vision is to deliver an empowering and role-specific e-commerce experience that combines the efficiency of a B2B platform with the intuitive design of a modern consumer application.

Our design and functionality will be guided by these principles:

- **Role-Driven Clarity**: The interface must dynamically adapt to the logged-in user's role (owner, staff, viewer). Each user should only see the tools and information relevant to their responsibilities, reducing complexity and potential errors.

- **Streamlined Procurement**: The core journey—from finding a product to placing an order—must be as fast and frictionless as possible, especially for staff users who will perform this task repeatedly.

- **Empowerment through Oversight**: For owner roles, the portal must provide a clear, high-level overview of their company's activities, including user management and order history, enabling them to manage their account effectively.

- **Clean & Professional Interface**: The design will be modern, clean, and uncluttered, building trust and ensuring ease of use for all technical skill levels.

## 2. Proposed Layout & Role-Based UI/UX Design

Unlike the data-heavy admin panel, the Customer Portal will adopt a more familiar and streamlined e-commerce layout. The key is that this layout will intelligently reconfigure itself based on the user's role.

### A. Main Header Bar (Top, Fixed)

This is the primary navigation and action center for all customer users.

- **Company Logo & Name** *(Left)*: Clearly displays the customer's company name, reinforcing their private portal experience.

- **Primary Navigation Links** *(Center)*: This is the core of the role-based UI. The links shown here will change dynamically:
  - **Dashboard**: (Home icon) Visible ONLY to owner roles.
  - **Products**: Visible to all roles (owner, staff, viewer).
  - **Orders**: Visible to all roles.

- **Action & Profile Area** *(Right)*:
  - **Global Product Search Bar**: A prominent search bar for finding products by name, SKU, or category.
  - **Shopping Cart**: (Cart icon) A link to the cart page, with a badge showing the number of items. This will be visible to owner and staff roles but hidden for viewer roles.
  - **User Profile Dropdown**: An avatar or user's name that, when clicked, shows their name, role, and a "Logout" button.

### B. Main Content Area (Center, Dynamic)

This is where the selected page's content is rendered. It will display product grids, order lists, forms, and the owner's dashboard. The content within these pages will also adapt based on role (e.g., an "Add to Cart" button being disabled for viewers).

## 3. Core Functional Modules & User Flows

This section details the initial features of the Customer Portal, focusing on the distinct experiences for each role.

### 3.1. Module: The Owner's Dashboard

**Objective**: To give company owners a centralized view of their account, users, and recent activity.

**Access**: Strictly limited to users with the owner role. All other roles attempting to access this page will be redirected.

**Key Components & Flow**:

- **Welcome Header**: A personalized greeting, "Welcome, [Owner's Name]".

- **Quick Stats Cards**: A row of key metrics summarizing their company's activity.
  - Total Orders (This Month)
  - Total Spend (This Month)
  - Active Staff Members

- **User Management Table**: A simple but effective table listing all other users (staff, viewer) within their company.
  - **Columns**: User Name, User Email, Role, Last Login.
  - **Actions** *(Future Enhancement)*: Each row could have an "Edit" button, allowing the owner to change a user's role or deactivate them. This would require new API endpoints but is a logical next step.

- **Recent Company Orders**: A condensed list of the 5 most recent orders placed by any user from their company, with a link to the full "Orders" page.

### 3.2. Module: Product Catalog & Search

**Objective**: To provide an efficient and intuitive way for all users to find and learn about products.

**Access**: Visible to owner, staff, and viewer roles.

**Key Components & Flow**:

- **Product Listing Page**:
  - A clean grid or list view of products.
  - **Powerful Filtering**: Essential for B2B. Users should be able to filter products by category, brand, and potentially other specifications.
  - **Sorting**: Options to sort by price, name, or popularity.

- **Product Detail Page**:
  - Accessed by clicking a product from the listing page.
  - Displays detailed information: high-quality images, specifications, description, and price.

- **The "Add to Cart" Button** *(Role-Based Action)*:
  - For **owner** and **staff** roles, this is an active button that adds the product to their company's shared shopping cart.
  - For the **viewer** role, this button should be disabled or completely hidden, with a possible tooltip saying "You do not have permission to purchase."

### 3.3. Module: Shopping Cart

**Objective**: To provide a clear summary of selected items and a simple path to placing an order.

**Access**: Limited to owner and staff roles.

**Key Components & Flow**:

- **Itemized List**: A clear list of all items in the cart.
  - **Columns**: Product Image/Name, Unit Price, Quantity, Line Total.
  - **Quantity Control**: Each item should have controls to increase, decrease, or remove it from the cart.

- **Cart Summary**: A section that displays the subtotal, taxes (if applicable), and final total.

- **"Place Order" Button**: A prominent call-to-action button that finalizes the purchase. Clicking this would submit the order to the backend. (This assumes a simple "place order" API endpoint. A more complex checkout flow could be a future enhancement).

### 3.4. Module: Order History

**Objective**: To allow users to track current and past orders placed by their company.

**Access**: Visible to owner, staff, and viewer roles.

**Key Components & Flow**:

- **Main Order List**: A table listing all orders associated with the user's customer_id.
  - **Columns**: Order ID, Date Placed, Placed By (User Name), Total Amount, Status (e.g., a colored badge for "Processing", "Shipped", "Delivered").
  - The list should be searchable by Order ID and filterable by status.

- **Order Detail View**: Clicking on any order navigates to a detailed summary of that specific order, including the list of products purchased, quantities, prices, and shipping information.