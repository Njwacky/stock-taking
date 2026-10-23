# Stock Management System - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Registration](#user-registration)
3. [Login and Authentication](#login-and-authentication)
4. [Dashboard Overview](#dashboard-overview)
5. [Managing Your Stock](#managing-your-stock)
6. [Profile Management](#profile-management)
7. [User Roles and Permissions](#user-roles-and-permissions)
8. [Kit Transfer System](#kit-transfer-system)
9. [Reports and Analytics](#reports-and-analytics)
10. [Important System Information](#important-system-information)

## Getting Started

### System Requirements
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Internet Connection**: Minimum 1 Mbps (recommended 5 Mbps+)
- **Screen Resolution**: Minimum 1024x768, Recommended 1920x1080
- **JavaScript**: Must be enabled for interactive features

### Accessing the System
1. Open your web browser
2. Navigate to the system URL (provided by your administrator)
3. You will see the login page or dashboard if already logged in

## User Registration

### Creating a New Account
1. Click the "Register" button on the login page
2. Fill in the required information:
   - **Username**: Choose a unique username (3-150 characters)
   - **Clock Number**: Enter your employee clock number (1-9999)
   - **Password**: Create a secure password (minimum 12 characters)
   - **Confirm Password**: Re-enter your password
3. Click "Register" to create your account

**Important Security Note**: All new users are automatically assigned the "Regular User" role. Only administrators and managers can change user roles through the "Manage Users" feature.

### Password Requirements
- **Minimum Length**: 4 characters
- **Cannot be too similar to your username**
- **Cannot be entirely numeric**
- **Cannot be a commonly used password**

### Clock Number Validation
- Must be a unique number between 1 and 9999
- Each user must have a distinct clock number
- Used for employee identification throughout the system

## Login and Authentication

### Logging In
1. Enter your username and password
2. Click the "Login" button
3. You will be redirected to your dashboard

### Session Management
- **Session Timeout**: 24 hours of inactivity
- **Automatic Logout**: When browser is closed
- **Security**: Sessions are encrypted and secure

### Password Reset
If you forget your password, contact your system administrator to reset it.

## Dashboard Overview

### Main Dashboard Features
The dashboard provides an overview of your stock management activities:

#### For Non-Registered Users
- **Why Register Carousel**: Shows benefits of registering (slides automatically every 5 seconds)
- **Register/Login Options**: Prominent buttons to create account or login

#### For Registered Users
- **Welcome Message**: Personalized greeting with your username
- **Stock Summary**: Overview of your kits and quantities
- **Recent Activity**: Latest transfers and updates
- **Quick Actions**: Fast access to common tasks
- **Navigation Menu**: Access to all system features

### Dashboard Controls
- **Search**: Find specific kits or users
- **Filter**: Filter by kit type, condition, or date
- **Sort**: Organize data by different criteria
- **Export**: Download data in various formats

## Managing Your Stock

### Adding New Items
1. Navigate to "Add Stock" from the dashboard
2. Select the user (if you have permissions)
3. Enter quantities for each kit type:
   - **Feets**: Measurement units
   - **VHB Boss Tape**: Available in 18mm, 12mm, and 7mm widths
   - **PI Strips**: Polyimide strips
   - **Rivnuts**: Available in 8mm, 6mm, 5mm, and 4mm sizes
4. Set additional information:
   - **Condition**: New, Good, Fair, Poor, or Damaged
   - **Location**: Physical storage location
   - **Notes**: Additional information
   - **Expiration Date**: For items with shelf life
5. Click "Add Items" to save

### Viewing Your Stock
- Go to your dashboard to see all assigned kits
- Kits are displayed with type, quantity, and condition
- Use filters to find specific items
- Export your inventory list if needed

### Editing Stock Items
1. Find the item you want to edit
2. Click the edit button (pencil icon)
3. Update the information as needed
4. Save your changes

### Deleting Stock Items
1. Select the item(s) you want to delete
2. Click the delete button
3. Confirm the deletion in the popup dialog
4. **Note**: This action cannot be undone

### Bulk Operations
- **Bulk Selection**: Use checkboxes to select multiple items
- **Bulk Delete**: Delete multiple items at once
- **Selection Counter**: Shows number of selected items

## Profile Management

### Viewing Your Profile
1. Click on your username or go to "Profile"
2. View your personal information:
   - Username and clock number
   - Role and department
   - Date joined and last login
   - Contact information

### Profile QR Code
- Each user has a unique QR code
- Can be scanned for quick profile access
- Included in profile exports

### Updating Profile Information
1. Go to your profile page
2. Click "Edit Profile"
3. Update your information:
   - First name and last name
   - Email address
   - Department
   - Phone number
4. Save your changes

### Exporting Your Profile
1. On your profile page, click "Download PDF" or "Print"
2. **PDF Download**: Generates a complete PDF with:
   - Your personal information
   - QR code for quick access
   - Complete kit inventory with quantities
   - Automatic filename: `username_timestamp.pdf`
3. **Print**: Optimized print format for hard copies

### Viewing Other Users' Profiles
- If you have appropriate permissions, you can view other users' profiles
- Shows their basic information and assigned kits
- Useful for managers and supervisors

## User Roles and Permissions

### Role Hierarchy
1. **Administrator**: Full system access
2. **Manager**: Can manage users and view reports
3. **Supervisor**: Can view all kits and transfer items
4. **Regular User**: Basic kit management only

### Administrator Permissions
- Create, edit, and delete all users
- Edit user information including passwords and roles
- Manage system settings
- View all audit logs
- Generate all types of reports
- Full access to all features
- Can create new kit types
- **Admin password required** for editing users

### Manager Permissions
- View all kits in the system
- Generate reports and analytics
- Transfer kits between users
- **Delete users** (except admins)
- Cannot edit user information or reset passwords
- Cannot delete system data
- Can create new kit types

### Supervisor Permissions
- View all kits in the system
- Transfer kits between users
- Add items for any user
- Cannot manage users or system settings
- Cannot create new kit types

### Regular User Permissions
- View and manage their own kits
- Add items for themselves only
- Edit their own profile
- Cannot view other users' data
- Cannot transfer kits

## User Management

### Managing Users
User management is accessible through the "Manage Users" option in the navigation menu. This feature allows authorized personnel to oversee user accounts.

### Access Requirements
- **Administrators**: Full access to edit and delete users
- **Managers**: Can delete users (except administrators)
- **Supervisors**: Cannot manage users
- **Regular Users**: Cannot access user management

### Editing User Information (Admin Only)
Administrators can edit all user information including:
1. **Basic Information**: Username, clock number, personal details
2. **Role Assignment**: Change user roles (User, Supervisor, Manager, Admin)
3. **Password Reset**: Reset forgotten passwords for users
4. **Contact Information**: Update email, phone, department

#### Security Requirements for Editing Users
- **Admin Password Required**: Administrators must enter their own password to confirm any user changes
- **Cannot Edit Self**: Administrators cannot edit their own accounts (must have another admin do it)
- **Cannot Edit Superusers**: Regular admins cannot edit superuser accounts

#### Steps to Edit a User
1. Go to "Manage Users" from the navigation menu
2. Select the appropriate manager from the dropdown
3. Find the user you want to edit in the table
4. Click the "Edit" button next to their name
5. Update the necessary information
6. **Enter your admin password** in the security verification section
7. Click "Save Changes" to apply the updates

### Deleting Users
#### Administrator Deletion Rights
- Can delete any user except superusers and themselves
- Must confirm with admin password
- Full deletion access

#### Manager Deletion Rights
- Can delete regular users and supervisors
- Cannot delete administrators or superusers
- Must confirm with their own password

#### Steps to Delete Users
1. Go to "Manage Users" and select the appropriate manager
2. Find the user(s) you want to delete
3. **Single deletion**: Click the "Delete" button next to the user
4. **Bulk deletion**: Select multiple users with checkboxes, then click "Delete Selected"
5. Confirm the deletion in the popup dialog
6. Enter your password to verify the action
7. Confirm the final deletion

### Security Features
- **Password Verification**: All user management actions require password confirmation
- **Audit Logging**: All user edits and deletions are logged
- **Self-Protection**: Users cannot edit or delete their own accounts
- **Hierarchy Protection**: Lower-level users cannot modify higher-level accounts
- **Role Validation**: Role changes are validated and restricted

### Best Practices for User Management
- **Use Strong Admin Passwords**: Administrators should use complex, unique passwords
- **Regular Role Reviews**: Periodically review user roles and permissions
- **Document Changes**: Keep records of role changes and password resets
- **Immediate Revocation**: Remove access immediately when employees leave
- **Principle of Least Privilege**: Assign only necessary permissions to each role

## Kit Transfer System

### Transferring Kits
1. Go to the dashboard and find the kit you want to transfer
2. Click the transfer button
3. Select the recipient user from the dropdown
4. Add transfer notes (optional)
5. Confirm the transfer

### Transfer Permissions
- **Admins**: Can transfer any kit to any user
- **Managers**: Can transfer any kit to any user
- **Supervisors**: Can transfer kits between users
- **Regular Users**: Cannot transfer kits (must request supervisor)

### Transfer Tracking
- All transfers are logged in the system
- Transfer history shows:
  - From user and to user
  - Transfer date and time
  - Person who performed the transfer
  - Transfer notes

### Viewing Transfer History
- Go to your profile or dashboard
- Look for "Transfer History" section
- Shows all incoming and outgoing transfers
- Filter by date range or user

## Reports and Analytics

### Available Report Types
1. **Inventory Summary**: Complete stock overview
2. **User Activity**: User actions and statistics
3. **Kit Usage Statistics**: Usage patterns and trends
4. **Transfer History**: All kit transfers
5. **Expiration Report**: Items approaching expiration

### Generating Reports
1. Go to the dashboard and find "Reports" section
2. Select the report type you want
3. Choose the format (PDF, CSV, Excel, JSON)
4. Set filters if needed:
   - Date range
   - Specific users
   - Kit types
5. Click "Generate Report"

### Export Formats
- **PDF**: Professional format for printing
- **CSV**: Compatible with spreadsheet applications
- **Excel**: Full-featured spreadsheet format
- **JSON**: Data format for system integration

### Report Permissions
- **Admins**: Can generate all report types
- **Managers**: Can generate most reports
- **Supervisors**: Limited report access
- **Regular Users**: Cannot generate system reports

## Important System Information

### System Security
- **Password Protection**: All passwords are encrypted
- **Session Security**: Sessions timeout after 24 hours
- **Data Encryption**: Sensitive data is protected
- **Audit Logging**: All actions are tracked

### Data Validation
- **Clock Numbers**: Must be unique (1-9999)
- **Quantities**: Must be positive numbers
- **Dates**: Must be valid and logical
- **Emails**: Must be valid email format

### System Limitations
- **Maximum Kits**: No hard limit, but performance may degrade with very large numbers
- **File Uploads**: Maximum 5MB per file
- **Session Time**: 24 hours of inactivity
- **Concurrent Users**: System supports 100+ simultaneous users

### Browser Compatibility
- **Recommended**: Chrome, Firefox, Safari, Edge (latest versions)
- **JavaScript**: Required for interactive features
- **Cookies**: Required for session management
- **Mobile**: Responsive design works on tablets and phones

### Data Backup
- **Automatic Backups**: System data is backed up regularly
- **Recovery**: Data can be restored if needed
- **Audit Trail**: All changes are tracked and logged

### Getting Help
- **Technical Issues**: Contact your system administrator
- **Training Materials**: Available through the dashboard
- **User Support**: Check the FAQ section or contact support

### Best Practices
- **Password Security**: Use strong, unique passwords
- **Data Accuracy**: Keep your information up to date
- **Regular Login**: Log out when not using the system
- **Report Issues**: Report any problems immediately

---

**Version**: 1.0  
**Last Updated**: September 2025  
**System**: Stock Management System v5.2

For additional help or to report issues, please contact your system administrator.
