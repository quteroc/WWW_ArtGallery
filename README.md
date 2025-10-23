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
- DigitalOcean Spaces (CDN for images - optional)

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
- 10GB+ disk space

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yahorlahunovich/WWW_ArtGallery.git
   cd WWW_ArtGallery
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings (optional)
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
   docker-compose exec backend python -m app.scripts.create_admin \
     --username admin \
     --email admin@example.com \
     --password admin123
   ```

6. **Seed the database with artworks**
   ```bash
   # Import sample artworks (1% of dataset, ~800 artworks)
   docker-compose exec backend python -m app.scripts.seed_data --percentage 0.01
   
   # Or import full dataset (~80,000 artworks) - takes longer
   docker-compose exec backend python -m app.scripts.seed_data
   ```

7. **Access the application**
   - Gallery: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Login: http://localhost:8000/login

### Test Accounts

After running the seed script, you'll have these accounts:

- **Admin**: admin / admin123
- **Manager**: manager / manager123
- **User**: user / user123

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

Create a `.env` file (or use `.env.example`):

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/artgallery

# JWT Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CDN (Optional - for serving images from cloud)
ARTWORKS_BASE_URL=https://your-cdn-url.com

# File Paths
STATIC_FILES_DIR=/app/ml/input/wikiart
```

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

### Missing Images
- Ensure you've run the seed script
- Check `ARTWORKS_BASE_URL` in .env
- Verify image files exist in `ml/input/wikiart/`

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
