# User Guide - WWW Art Gallery

Complete guide for using the Classic Art Gallery application across all user roles.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Guest Users (Not Logged In)](#guest-users)
3. [Registered Users](#registered-users)
4. [Manager Role](#manager-role)
5. [Administrator Role](#administrator-role)
6. [Common Tasks](#common-tasks)

---

## Getting Started

### Accessing the Application

1. Open your web browser
2. Navigate to: `http://localhost:8000`
3. You'll see the main gallery page with artwork thumbnails

### Creating an Account

1. Click **"Sign Up"** button in the top-right corner
2. Fill in the registration form:
   - **Email**: Valid email address (format validated)
   - **Username**: 3-20 characters, alphanumeric with underscore/hyphen allowed
   - **Password**: Minimum 6 characters
   - **Confirm Password**: Must match password
3. Click **"Create Account"**
4. You'll be redirected to login page after successful registration

### Logging In

1. Click **"Login"** in the navigation bar
2. Enter your username and password
3. Click **"Sign In"**
4. You'll be redirected to the gallery

---

## Guest Users

*What you can do without logging in:*

### Browse Gallery
- View all active artworks in the main gallery
- See artwork thumbnails with title, artist, style, and year
- Navigate through paginated results

### Search & Filter
- **Search Bar**: Enter artwork title or artist name
- **Style Filter**: Dropdown menu to filter by art style
  - Options include: Baroque, Renaissance, Impressionism, etc.
- **Clear Filters**: Remove all filters to view full gallery

### View Artwork Details
- Click on any artwork image or title
- See full artwork information:
  - High-resolution image
  - Title and artist name
  - Art style and year (if available)
  - Popularity score
  - View count
  - Artist biography/description

### Limitations
❌ Cannot like artworks
❌ Cannot post comments
❌ Cannot access "My Likes" page
❌ No access to admin/manager features

---

## Registered Users

*Everything guests can do, plus:*

### Like/Unlike Artworks

**From Gallery Page:**
1. Each artwork card shows a heart icon
2. Click the heart to like (turns red)
3. Click again to unlike (turns gray)

**From Artwork Detail Page:**
1. Scroll to the artwork details section
2. Click **"Like"** button (changes to **"Liked"** and turns red)
3. Click **"Liked"** to unlike

### View Your Liked Artworks

1. Click **"My Likes"** in the navigation bar
2. See all artworks you've liked
3. Click **"View Details"** to see full information
4. Click **"Unlike"** to remove from your collection

### Comment on Artworks

1. Navigate to any artwork detail page
2. Scroll to the **Comments** section
3. Type your comment in the text area (max 1000 characters)
4. Character counter shows remaining characters
5. Click **"Post Comment"**
6. Your comment appears at the top of the list with:
   - Your username
   - Relative timestamp (e.g., "2 minutes ago")

### Delete Your Own Comments

1. Find your comment in the comments section
2. Click **"Delete"** button next to your comment
3. Confirm deletion in the popup
4. Comment is immediately removed

### Reset Password

**Option 1: From User Menu**
1. Click your username in the top-right corner
2. Select **"Reset Password"** from dropdown
3. Enter current password
4. Enter new password
5. Confirm new password
6. Click **"Reset Password"**

**Option 2: From Login Page**
1. Click **"Reset Password"** link on login page
2. Follow same steps as above

### Logout

1. Click your username in top-right corner
2. Select **"Logout"** from dropdown menu
3. You'll be redirected to the gallery (as guest)

---

## Manager Role

*Everything regular users can do, plus:*

### Access Manager Panel

1. After logging in as manager, you'll see **"Manager Panel"** button (purple, with gear icon)
2. Click to access the dashboard

### Manager Dashboard

**Overview Statistics:**
- Total artworks count
- Quick access to artwork management

**Available Actions:**
- Manage Artworks (view, search, toggle status)

### Manage Artworks

**Search Artworks:**
1. Click **"Manage Artworks"** from dashboard
2. Use search bar at top to find artworks by title or artist
3. Click **"Search"** or press Enter
4. Click **"Clear"** to reset search

**Toggle Artwork Status:**
1. Find artwork in the list
2. Current status shown as badge:
   - 🟢 **Active**: Visible in gallery
   - ⚫ **Inactive**: Hidden from gallery
3. Click **"Toggle Status"** button
4. Status changes immediately
5. Inactive artworks won't appear in main gallery

**View Artwork Details:**
- Each row shows: Title, Artist, Style, Year, Status, Actions
- Click artwork title to view full details

### Moderate Comments

**Delete Any User's Comments:**
1. Navigate to any artwork detail page
2. View all comments
3. As a manager, you'll see **"Delete"** button on ALL comments (not just your own)
4. Click **"Delete"** on inappropriate comments
5. Confirm deletion
6. Comment is removed immediately

**Manager Moderation Guidelines:**
- Delete spam or inappropriate content
- Remove offensive language
- Maintain community standards

---

## Administrator Role

*Everything managers can do, plus full system control:*

### Access Admin Panel

1. After logging in as admin, you'll see **"Admin Panel"** button (purple, with gear icon)
2. Click to access full dashboard

### Admin Dashboard

**Overview Statistics:**
- Total artworks count
- Total users count

**Available Actions:**
- Manage Artworks
- Manage Users (admin-only)

### Manage Users

**View All Users:**
1. Click **"Manage Users"** from dashboard
2. See complete user list with:
   - Username
   - Email
   - Current role
   - Account status

**Change User Roles:**
1. Find user in the list
2. Click **"Change Role"** dropdown
3. Select new role:
   - User (default)
   - Manager
   - Admin
4. Click **"Update Role"**
5. Role changes immediately
6. User's permissions update on next login

### Manage Artworks (Admin Features)

**All Manager Features PLUS:**

**Import Artworks from Dataset:**
1. Click **"Import from Dataset"** button
2. Modal dialog appears
3. Select style from dropdown (shows available artwork count)
4. List of artworks appears with checkboxes
5. Use **"Select All"** or choose individual artworks
6. Selected count shows at top
7. Click **"Import Selected"**
8. Success message shows import results
9. Artworks appear in gallery immediately

**Delete Artworks Permanently:**
1. Find artwork in manage list
2. Click **"Delete"** button (red)
3. Confirm deletion in popup
4. Artwork is permanently removed from database
5. ⚠️ This action cannot be undone!

**Search and Filter:**
- Same search functionality as managers
- Results update in real-time

### User Management Details

**User Roles Explained:**

1. **User (Default)**
   - Browse gallery
   - Like artworks
   - Post and delete own comments
   - View personal collection

2. **Manager**
   - All user permissions
   - Access manager panel
   - Moderate comments (delete any)
   - Toggle artwork active/inactive status

3. **Admin**
   - All manager permissions
   - Access admin panel
   - Manage all users
   - Change user roles
   - Import artworks from dataset
   - Delete artworks permanently

---

## Common Tasks

### Finding Specific Artwork

**Method 1: Search**
1. Use search bar on gallery page
2. Type part of title or artist name
3. Results filter automatically

**Method 2: Filter by Style**
1. Click style dropdown
2. Select desired style
3. Gallery shows only that style

**Method 3: Combine Search + Filter**
1. Select style
2. Type search term
3. Results match both criteria

### Understanding Artwork Information

**Popularity Score:**
- Percentage (0-100%)
- Based on WikiArt dataset metrics
- Higher = more historically significant/popular

**View Count:**
- Number of times artwork detail page was visited
- Increments each time someone views the artwork

**Status Badge:**
- 🟢 **Active**: Visible to all users
- ⚫ **Inactive**: Only visible to managers/admins

### Comment Timestamps

Comments show relative time:
- "just now" (< 1 minute)
- "X minutes ago" (1-59 minutes)
- "X hours ago" (1-23 hours)
- "X days ago" (1-29 days)
- "X months ago" (1-11 months)
- "X years ago" (1+ years)

### Responsive Design

**Desktop (1920px+):**
- 4-column grid for artworks
- Full navigation bar
- Side-by-side artwork detail layout

**Tablet (768px-1919px):**
- 2-3 column grid
- Collapsed navigation
- Stacked artwork detail layout

**Mobile (< 768px):**
- Single column grid
- Hamburger menu
- Optimized touch targets

---

## Troubleshooting

### Can't Login
- Check username/password spelling
- Passwords are case-sensitive
- Try password reset if forgotten

### Don't See Admin/Manager Panel Button
- Verify your role with administrator
- Logout and login again
- Role changes require new login

### Artwork Images Not Loading
- Check internet connection
- Try refreshing the page
- Report to administrator if persists

### Comments Not Posting
- Check if logged in
- Ensure comment not empty
- Maximum 1000 characters
- Try refreshing page

### Like Button Not Working
- Verify you're logged in
- Try refreshing the page
- Check if artwork is active

---

## Keyboard Shortcuts

- **Enter** in search bar → Submit search
- **Esc** → Close modals/dropdowns
- **Tab** → Navigate form fields

---

## Best Practices

### For Users
✅ Be respectful in comments
✅ Use descriptive search terms
✅ Log out when using shared computers

### For Managers
✅ Review comments regularly
✅ Toggle status instead of deleting when possible
✅ Document moderation actions

### For Administrators
✅ Backup database before major changes
✅ Import artworks in batches
✅ Review user roles periodically
✅ Monitor system usage

---

## Getting Help

### Support Resources
- README.md → Installation and setup
- REPORT.md → Technical architecture
- API Documentation → http://localhost:8000/docs

### Contact
For technical support or bug reports, contact your system administrator.

---

## Appendix: Form Validation Rules

### Registration
- **Email**: Valid email format (name@domain.com)
- **Username**: 
  - 3-20 characters
  - Letters, numbers, underscore, hyphen only
  - No spaces
- **Password**: 
  - Minimum 6 characters
  - No maximum limit
  - Special characters allowed

### Comments
- **Content**: 
  - Not empty
  - Maximum 1000 characters
  - Plain text only

### Search
- **Query**: 
  - Any text
  - Case-insensitive
  - Searches both title and artist

---

*Last Updated: October 2025*
*Version: 1.0*
