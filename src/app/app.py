from fastapi import FastAPI, Depends
from src.routers import auth
from src.routers import auth_user
from src.config.database import get_db, Base, engine, SessionLocal
from src.repositories import  UserRepository
from sqlalchemy.orm import Session
from sqlalchemy import text

user_repositories = UserRepository()
app = FastAPI(
    title="Fixing Service API",
    description="Backend API for Garage Service Provider",
    version="1.0.0"

)

def init_db():
    """Initialize database tables and create admin user if needed."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create admin user if it doesn't exist
        db = SessionLocal()
        try:
            user_repositories.create_admin_user_if_not_exists(db)
            db.commit()
            print("✅ Database initialized successfully")
        except Exception as e:
            db.rollback()
            print(f"⚠️  Warning: Error initializing admin user: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("   Please check your database configuration in .env file")
        print("   The application will continue, but database features may not work.")


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()


app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/app")
def read_root():
    return {"message": "Welcome to the Fixing Service API"}


@app.get("/")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        print("Database connection successful!")
        return {"message": "Database connection successful!"}
    except Exception as e:
        return {"message": f"Database connection failed: {e}"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth_user.router)  # or prefix="/api"