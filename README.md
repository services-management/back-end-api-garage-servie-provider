# Backend API - Garage Service Provider

FastAPI backend application with PostgreSQL database and JWT authentication.

## Prerequisites

- Python 3.12 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Local Development Setup

### 1. Clone the Repository

```bash
cd "back-end-api-garage-servie-provider"
```

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

#### Option A: Using Docker (Recommended for quick setup)

```bash
docker run --name fixing-service-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=fixing_service_db \
  -p 5432:5432 \
  -d postgres:15
```

#### Option B: Local PostgreSQL Installation

1. Install PostgreSQL on your system
2. Create a database:
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE fixing_service_db;

# Exit psql
\q
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
# Database Configuration (REQUIRED)
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fixing_service_db
DB_DRIVER=psycopg2

# JWT Configuration (OPTIONAL - only needed for /auth/login endpoint)
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

**Important Notes:**
- **Database connection works WITHOUT SECRET_KEY** - Only database credentials are required
- `SECRET_KEY` is only needed if you want to use the `/auth/login` endpoint for JWT tokens
- If `SECRET_KEY` is not provided, a default value will be used (not recommended for production)

**Alternative:** You can also use a complete `DATABASE_URL` instead of individual variables:
```env
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/fixing_service_db
```

### 5.1. Test Database Connection (Without SECRET_KEY)

You can test the database connection independently:

```bash
# Using the example script
python examples/test_db_connection.py

# Or test via the API endpoint
curl http://localhost:8000/
```

### 6. Run the Application

```bash
# Option 1: Using FastAPI CLI (Recommended)
fastapi dev main.py

# Option 2: Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option 3: Using Python directly
python main.py
```

The application will be available at:
- **API**: http://localhost:8000
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc

### 7. Verify the Setup

1. **Test database connection:**
   ```bash
   curl http://localhost:8000/
   ```
   Should return: `{"message": "Database connection successful!"}`

2. **Test login endpoint:**
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin"
   ```
   Should return a JWT token.

## Default Admin User

On first startup, the application automatically creates an admin user:
- **Username**: `admin`
- **Password**: `admin`

## API Endpoints

### Authentication
- `POST /auth/login` - Login and get JWT token

### Health Check
- `GET /` - Test database connection
- `GET /app` - Welcome message

### Admin Management
- `POST /admin/login`: Admin Login
- `GET /admin/me`: Get Current Admin User Details
- `POST /admin/`: Create a new Admin
- `PUT /admin/{admin_id}`: Update Admin Details
- `POST /admin/technical`: Provision Technical Account

### Technical Staff
- `POST /technical/login`: Technical Staff Login
- `GET /technical/me`: Get Current Technical User Details
- `PUT /technical/me`: Update My Technical User Details
- `PATCH /technical/me/status`: Update Technical Status

### Category Management
- `POST /category/`: Create a new category (Requires admin authentication)
- `GET /category/{category_id}`: Get a specific category by ID
- `GET /category/`: List all categories
- `PATCH /category/{category_id}`: Update a category (Requires admin authentication)
- `DELETE /category/{category_id}`: Delete a category (Requires admin authentication)

### Product Management
- `POST /product/`: Create a new product (Requires admin authentication)
- `GET /product/{product_id}`: Get a specific product by ID
- `GET /product/`: List all products
- `GET /product/by-category/{category_id}`: List products by category
- `PUT /product/{product_id}`: Update a product (Requires admin authentication)
- `DELETE /product/{product_id}`: Delete a product (Requires admin authentication)

### Inventory Management
- `GET /inventory/{product_id}`: Fetch the inventory details for a specific product (Requires admin or technical user authentication)
- `PATCH /inventory/{product_id}/stock`: Directly set the current stock level (Requires admin authentication)
- `POST /inventory/{product_id}/restock`: Add to existing stock (Requires admin authentication)
- `POST /inventory/{product_id}/deduct`: Deduct stock (Requires admin or technical user authentication)
- `GET /inventory/alerts/low-stock`: Get a list of Product IDs where stock is at or below the minimum level (Requires admin or technical user authentication)

## Development Commands

### Run Tests
```bash
pytest
```

### Run with Auto-reload (Development)
```bash
uvicorn main:app --reload
```

### Run in Production Mode
```bash
uvicorn main:app 
```

## Project Structure

```
.
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
├── src/
│   ├── app/               # Application configuration
│   ├── config/            # Settings and database configuration
│   ├── models/            # SQLAlchemy database models
│   ├── repositories/      # Data access layer
│   ├── routers/           # API route handlers
│   ├── schemas/           # Pydantic models for request/response
│   └── tests/             # Test files
```

## Database Connection Without SECRET_KEY

**Important:** The database connection works **independently** of `SECRET_KEY`. 

- ✅ **Database connection** only requires: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` (or `DATABASE_URL`)
- ❌ **SECRET_KEY is NOT required** for database operations
- 🔑 **SECRET_KEY is only needed** for JWT token generation in `/auth/login` endpoint

### Minimal .env for Database Connection Only

If you only need database connection (without authentication), your `.env` can be:

```env
# Only database configuration needed
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fixing_service_db
```

The `GET /` endpoint will work perfectly without `SECRET_KEY`!

### Test Database Connection

```bash
# Test using the example script
python examples/test_db_connection.py

# Or test via API
curl http://localhost:8000/
```

## Generating Requirements

To update `requirements.txt` after installing new packages:
```bash
pip freeze > requirements.txt
```
