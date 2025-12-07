from src.app.app import app
import uvicorn

# Export app for fastapi dev command and tests
__all__ = ["app"]

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)