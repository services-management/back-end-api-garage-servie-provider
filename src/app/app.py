from fastapi import FastAPI, Depends
from src.routers import auth
from src.routers import auth_user
from src.config.database import get_db, Base, engine, SessionLocal
from src.repositories import  UserRepository
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
user_repositories = UserRepository()
app = FastAPI(
    title="Fixing Service API",
    description="Backend API for Garage Service Provider",
    version="1.0.0"

)
app.add_middleware(
    CORSMiddleware,
    # Add both local and production frontend URLs here
    allow_origins=[
        "http://localhost:3000", 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def init_db():
    """Initialize database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            # user_repositories.create_admin(db)
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


app.include_router(auth.router)
app.include_router(auth_user.router)