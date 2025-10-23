# WWW Art Gallery - Classic Artwork Exhibition Platform

A full-stack web application for browsing, managing, and interacting with classic artworks from WikiArt dataset. Built with FastAPI, PostgreSQL, and modern web technologies.

## 📋 Project Overview

This application demonstrates a complete web system with role-based access control, allowing users to explore art collections, interact with artworks through likes and comments, while managers and administrators can moderate content and manage the gallery.

### 🎯 Key Features

#### For All Users
- **Art Gallery Browsing**: View curated collection of classic artworks
- **Advanced Filtering**: Search by title, artist, or style
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Artwork Details**: View high-resolution images with comprehensive metadata

#### For Authenticated Users
- **User Registration**: Self-service account creation with validation
- **Secure Authentication**: JWT-based login system
- **Password Reset**: Change password functionality
- **Like Artworks**: Save favorite artworks to personal collection
- **Comment System**: Share thoughts and engage with art community
- **Personal Collection**: View all liked artworks in one place

#### For Managers
- **Content Moderation**: Delete inappropriate comments
- **Artwork Management**: Toggle artwork visibility (active/inactive)
- **Gallery Overview**: View statistics and manage content

#### For Administrators
- **Full Gallery Control**: Import, activate, deactivate, and delete artworks
- **Batch Import**: Import multiple artworks from dataset by style
- **User Management**: View users and change roles
- **Search Functionality**: Find artworks quickly in admin panel

## 🏗️ Architecture

### Technology Stack

**Backend:**
- FastAPI 0.109.0 (Python web framework)
- PostgreSQL 15 (Database)
- SQLAlchemy & SQLModel (ORM)
- JWT Authentication (python-jose, passlib)
- PyTorch (Artist descriptions ML model)

**Frontend:**
- Jinja2 Templates (Server-side rendering)
- Alpine.js 3.x (Reactive components)
- Tailwind CSS (Styling via CDN)
- Vanilla JavaScript (API integration)

**Infrastructure:**
- Docker & Docker Compose (Containerization)
- DigitalOcean Spaces CDN (Image hosting)

### CDN-Only Architecture

**Important**: This application uses a **CDN-first architecture** where all artwork images are hosted on DigitalOcean Spaces CDN:

- **Image Storage**: All images served from `https://artappspace.nyc3.digitaloceanspaces.com`
- **No Local Files**: The application does **not** require local WikiArt dataset (70GB)
- **Database Records**: Store CDN URLs (e.g., `https://artappspace.nyc3.digitaloceanspaces.com/Baroque/rembrandt_night-watch.jpg`)
- **Seeding Method**: `seed_from_cdn.py` imports artwork metadata and CDN URLs from curated list
- **Admin Import**: Queries CDN via S3 API to discover additional artworks
- **Benefits**: 
  - Fast deployment (no large dataset download)
  - Scalable (CDN handles traffic)
  - Simple Docker setup

### Database Schema

**Users Table**
- UUID primary key
- Email (unique, indexed)
- Username (unique, indexed)
- Hashed password (bcrypt)
- Role (user/manager/admin)
- Timestamps

**Artworks Table**
- UUID primary key
- Title, artist, year
- Style (foreign key to Category)
- Image path and URL
- Popularity score (indexed)
- Views count
- Active status
- Timestamps

**Categories Table**
- Integer primary key
- Name (unique)
- Slug (unique, indexed)

**Comments Table**
- UUID primary key
- User ID (foreign key)
- Artwork ID (foreign key)
- Content (max 1000 chars)
- Timestamp

**Likes Table**
- Composite primary key (user_id, artwork_id)
- Timestamps

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed
- Git
- 4GB+ RAM available
- 2GB+ disk space (images hosted on CDN)
- Internet connection (for CDN image access)

### Installation

**Total Setup Time**: ~5 minutes (no large dataset download required)

1. **Clone the repository**
   ```bash
   git clone https://github.com/quteroc/WWW_ArtGallery.git
   cd WWW_ArtGallery
   ```

2. **Set up environment variables**
   
   The `.env` file is already configured with DigitalOcean Spaces CDN. No changes needed for basic deployment.
   
   ```bash
   # View current configuration (optional)
   cat .env
   ```

3. **Start the application**
   ```bash
   docker-compose up --build -d
   ```

4. **Wait for services to be ready** (30-60 seconds)
   ```bash
   docker-compose logs -f backend
   # Wait until you see "Application startup complete"
   ```

5. **Create admin user**
   ```bash
   docker-compose exec backend python -m app.scripts.create_admin --username admin --email admin@example.com --password admin123
   ```

6. **Seed the database with artworks from CDN**
   
   **IMPORTANT**: This application uses a **CDN-only architecture**. All images are hosted on DigitalOcean Spaces CDN, no local files needed.
   
   ```bash
   # Import 732 curated artworks from CDN (recommended - fast)
   docker-compose exec backend python -m app.scripts.seed_from_cdn
   ```
   
   This will import:
   - 732 verified artworks from 10 art styles
   - All images served from: https://artappspace.nyc3.digitaloceanspaces.com
   - Styles included: Baroque, Impressionism, Post-Impressionism, Art Nouveau, Cubism, Early Renaissance, Expressionism, Abstract Expressionism, Analytical Cubism, Action Painting
   - Takes ~30 seconds to complete

7. **Access the application**
   - Gallery: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Login: http://localhost:8000/login

### Quick Setup (Copy-Paste Commands)

For convenience, here are all commands in sequence:

**Linux/macOS/Git Bash:**
```bash
# Clone and navigate
git clone https://github.com/quteroc/WWW_ArtGallery.git
cd WWW_ArtGallery

# Start containers
docker-compose up --build -d

# Wait 60 seconds for services to initialize
# Then create admin and seed database
docker-compose exec backend python -m app.scripts.create_admin --username admin --email admin@example.com --password admin123
docker-compose exec backend python -m app.scripts.seed_from_cdn

# Access: http://localhost:8000
```

**Windows PowerShell:**
```powershell
# Clone and navigate
git clone https://github.com/quteroc/WWW_ArtGallery.git
cd WWW_ArtGallery

# Start containers
docker-compose up --build -d

# Wait 60 seconds for services to initialize
# Then create admin and seed database
docker-compose exec backend python -m app.scripts.create_admin `
  --username admin `
  --email admin@example.com `
  --password admin123

docker-compose exec backend python -m app.scripts.seed_from_cdn

# Access: http://localhost:8000
```

### Test Accounts

After running the seed script, use these accounts to test different roles:

- **Admin**: admin / admin123 (created in step 5)
- **Manager**: manager / manager123 (auto-created by seed script)
- **User**: user / user123 (auto-created by seed script)

## 📚 User Guide

See [USER_GUIDE.md](USER_GUIDE.md) for detailed instructions on using the application for each user role.

## 📊 Testing

### Run All Tests
```bash
docker-compose exec backend pytest -v
```

### Run with Coverage
```bash
docker-compose exec backend pytest --cov=app --cov-report=html --cov-report=term
```

### View Coverage Report
Open `backend/htmlcov/index.html` in your browser

### Test Coverage
- **Overall**: >80%
- **API Routes**: >85%
- **Authentication**: 100%
- **Database Models**: 100%

## 🎨 Requirements Compliance

✅ **User Authentication**
- Login and password reset functionality
- JWT-based secure authentication

✅ **Role-Based Access Control**
- 3 roles: User, Manager, Admin
- Restricted resources require authentication

✅ **Data Browsing & Filtering**
- Artworks table: browse, search, filter by style
- Users table: admin can view and manage

✅ **Aesthetic Design**
- Modern, clean UI with Tailwind CSS
- Consistent color scheme and typography

✅ **Responsive Design**
- Desktop (1920px)
- Tablet (768px)
- Mobile (375px)

✅ **Form Validation**
- Client-side: HTML5 + JavaScript
- Server-side: Pydantic models

✅ **CRUD Operations**
- Create: Register users, post comments, import artworks
- Read: Browse gallery, view details
- Update: Change roles, toggle artwork status, reset password
- Delete: Remove comments, artworks

✅ **AJAX Technology**
- Dynamic like/unlike without page reload
- Real-time comment posting
- Asynchronous artwork loading

✅ **Good Programming Practices**
- Clean architecture (separation of concerns)
- Type hints throughout
- Comprehensive error handling
- RESTful API design

✅ **Version Control**
- Git repository with meaningful commits
- Branching strategy

✅ **Easy Deployment**
- Docker Compose setup
- One-command deployment
- Environment configuration

✅ **Automated Testing**
- Unit tests for models and services
- Integration tests for API endpoints
- 80%+ code coverage

✅ **Documentation**
- README with setup instructions
- User guide for all roles
- Project report with architecture

## 📁 Project Structure

```
WWW_ArtGallery/
├── backend/
│   ├── app/
│   │   ├── api/            # API routes and dependencies
│   │   ├── core/           # Configuration and security
│   │   ├── db/             # Database setup
│   │   ├── models/         # SQLModel database models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── scripts/        # Seeding and admin creation
│   │   │   ├── create_admin.py         # Create admin user
│   │   │   ├── seed_from_cdn.py        # CDN-based seeding (main)
│   │   │   └── cdn_artworks_list.txt   # 732 curated CDN artwork paths
│   │   ├── services/       # Business logic (ML descriptions)
│   │   ├── tests/          # Automated tests
│   │   ├── web/            # Web routes (HTML rendering)
│   │   └── main.py         # FastAPI application
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── www/
│       ├── templates/      # Jinja2 HTML templates
│       └── static/         # CSS and JavaScript
├── ml/
│   └── output/            # ML model files
├── docker-compose.yml
├── .env.example
├── README.md
├── USER_GUIDE.md
└── REPORT.md
```

## 🔧 Configuration

### Environment Variables

The `.env` file is pre-configured with the following settings:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/artgallery

# JWT Security
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CDN Configuration (DigitalOcean Spaces)
ARTWORKS_BASE_URL=https://artappspace.nyc3.digitaloceanspaces.com
STATIC_FILES_DIR=/app/ml/input/wikiart
```

**Note**: All artwork images are served from the DigitalOcean Spaces CDN. The application does **not** require local image files.

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check if database is ready
docker-compose exec db psql -U postgres -c "\l"

# Reset database
docker-compose down -v
docker-compose up -d
```

### Backend Not Starting
```bash
# View logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### No Artworks Showing
```bash
# Re-run the CDN seed script
docker-compose exec backend python -m app.scripts.seed_from_cdn

# Verify artworks were imported
docker-compose exec db psql -U postgres -d artgallery -c "SELECT COUNT(*) FROM artworks;"
```

### Images Not Loading
- All images are hosted on CDN: https://artappspace.nyc3.digitaloceanspaces.com
- Check browser console for CORS or network errors
- Verify `ARTWORKS_BASE_URL` in .env matches: `https://artappspace.nyc3.digitaloceanspaces.com`
- No local image files are needed

### Admin Import Feature Shows Few Artworks
The admin panel can import additional artworks from the CDN:
1. Login as admin
2. Go to Admin Panel → Artworks
3. Click "Import from Dataset"
4. Select a style (e.g., Baroque, Impressionism)
5. The system scans up to 500 CDN images per style and filters out already-imported ones

## 📝 API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

This is an academic project. For educational purposes only.

## 📄 License

This project uses WikiArt dataset for educational purposes. All artwork images remain property of their respective owners.

## 👨‍💻 Author

Yauheni Butsialevich
Warsaw University of Technology
WWW Project 2025
