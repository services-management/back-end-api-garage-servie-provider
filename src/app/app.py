from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session, configure_mappers

from src.config.database import Base, SessionLocal, engine, get_db
from src.repositories.admin_repositories import AdminRepository
from src.routers import (admin_router, category_router, inventory_router,
                         product_router, service_router, technical_router, combo_service_router,
                         booking_router, telegram_router, auth_router, vehicle_router, user_router)
# Import all models to register them with SQLAlchemy Base
from src.schemas.admin import adminModel
# src/app/app.py
import httpx
from src.config.database import settings

# admin_repositories = AdminRepository()
app = FastAPI(
    title="Fixing Service API",
    description="Backend API for Garage Service Provider",
    version="1.0.0"

)
configure_mappers()
origins = [
    "https://garas-admin.domrey.online/",      # Your local React/Next.js frontend  
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

@app.on_event("startup")
async def startup_event():
    # --- 1. Initialize Database ---
    try:
        init_db()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

    # --- 2. Setup Telegram Webhook ---
    webhook_url = f"{settings.DOMAIN}/webhook/telegram"
    telegram_api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(telegram_api_url, json={"url": webhook_url})
            result = response.json()
            if result.get("ok"):
                print(f"✅ Telegram Webhook set to: {webhook_url}")
            else:
                print(f"❌ Telegram Webhook Error: {result}")
        except Exception as e:
            print(f"❌ Connection Error during Webhook setup: {e}")

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
            print(f"❌ Error connecting to database: {e}")
            print("   Please check your database configuration in .env file")
            print("   The application will continue, but database features may not work.")
    except Exception as e:
        print(f"Error during initialization: {e}")
    finally:
        if db:
            db.close()


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

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(technical_router)
app.include_router(product_router)
app.include_router(category_router)
app.include_router(inventory_router)
app.include_router(service_router)
app.include_router(combo_service_router)
app.include_router(booking_router)
app.include_router(telegram_router)
app.include_router(vehicle_router)
app.include_router(user_router)
