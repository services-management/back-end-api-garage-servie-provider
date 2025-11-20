from fastapi import FastAPI, Depends
from src.routers import auth
from src.config.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

app = FastAPI()

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

