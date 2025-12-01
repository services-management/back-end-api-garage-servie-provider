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

**⚠️ Important:** Change the admin password in production!

## API Endpoints

### Authentication
- `POST /auth/login` - Login and get JWT token
  - Body: `username` and `password` (form-data)
  - Returns: `{"access_token": "...", "token_type": "bearer"}`

### Health Check
- `GET /` - Test database connection
- `GET /app` - Welcome message

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
uvicorn main:app --host 0.0.0.0 --port 8000
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

## Troubleshooting

### Database Connection Issues

**Error: `password authentication failed for user "fixing_service_db"`**

This means your `.env` file has incorrect database credentials. The username should be your PostgreSQL user (usually `postgres`), not the database name.

1. **Check your `.env` file:**
   ```env
   # Correct format:
   DB_USER=postgres          # PostgreSQL username (NOT the database name)
   DB_PASSWORD=your_password # PostgreSQL password
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=fixing_service_db # Database name (can be different from username)
   ```

2. **Verify PostgreSQL is running:**
   ```bash
   # Linux/Mac
   sudo systemctl status postgresql
   
   # Or check if Docker container is running
   docker ps
   ```

3. **Test connection manually:**
   ```bash
   psql -U postgres -h localhost -d fixing_service_db
   ```

4. **If using Docker PostgreSQL, check the container:**
   ```bash
   docker exec -it fixing-service-db psql -U postgres
   ```

### File Watch Limit Error

**Error: `OSError: OS file watch limit reached`**

This happens when the system runs out of file watchers for auto-reload. Fix it:

**Option 1: Increase system limit (Recommended)**
```bash
# Run the provided script
./fix_file_watch_limit.sh

# Or manually:
sudo sysctl fs.inotify.max_user_watches=524288

# Make it permanent:
echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**Option 2: Run without auto-reload**
```bash
# Use uvicorn without --reload
uvicorn main:app --host 0.0.0.0 --port 8000

# Or use FastAPI CLI with --reload=false
fastapi run main.py --host 0.0.0.0 --port 8000
```

**Option 3: Exclude large directories**
The `.watchignore` file has been created to exclude `venv/`, `__pycache__/`, etc. from watching.

### Port Already in Use

If port 8000 is already in use, specify a different port:
```bash
uvicorn main:app --reload --port 8001
```

### Import Errors

Make sure you're in the project root directory and the virtual environment is activated:
```bash
source venv/bin/activate
```

### Database Connection Fails on Startup

If the database connection fails during startup, the app will still start but show a warning. Check:
1. PostgreSQL is running
2. `.env` file has correct credentials
3. Database exists (create it if needed: `CREATE DATABASE fixing_service_db;`)

## Generating Requirements

To update `requirements.txt` after installing new packages:
```bash
pip freeze > requirements.txt
```
