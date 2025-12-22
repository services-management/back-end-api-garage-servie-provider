from fastapi import FastAPI, Depends
from src.routers import admin_router, technical_router,category_router,inventory_router,product_router
from src.config.database import get_db, Base, engine, SessionLocal
from src.repositories.admin_repositorie import  AdminRepository
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.schemas.admin import adminModel
from fastapi.middleware.cors import CORSMiddleware

# admin_repositories = AdminRepository()
app = FastAPI(
    title="Fixing Service API",
    description="Backend API for Garage Service Provider",
    version="1.0.0"

)

origins = [
    "http://localhost:3000",      # Your local React/Next.js frontend
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins, change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

DEFAULT_ADMIN_USERNAME = "super_admin"
DEFAULT_ADMIN_PASSWORD = "change_me_123"
def init_db():
    """Initialize database tables"""
    db = None
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        admin_repo = AdminRepository(db)
        try:
            if db.query(adminModel).filter(adminModel.role == "admin").first() is None:
                print("No admin user found. Creating default admin...")
                # 2. Call the repository method (which you must implement in AdminRepository)
                admin_repo.create_default_admin(
                    username=DEFAULT_ADMIN_USERNAME,
                    password=DEFAULT_ADMIN_PASSWORD,
                    email_phone="default@service.com", # Include other required fields
                )
                print(f"✅ Default admin created: {DEFAULT_ADMIN_USERNAME}")
            else:
                print("✅ Admin user already exists. Skipping creation.")
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


app.include_router(admin_router)
app.include_router(technical_router)
app.include_router(product_router)
app.include_router(category_router)
app.include_router(inventory_router)