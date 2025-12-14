# conftest.py

import pytest
from starlette.testclient import TestClient
from src.app.app import app # Import your main FastAPI app instance
from src.config.database import Base, engine, SessionLocal, get_db
from sqlalchemy.orm import sessionmaker

# 1. Create a clean, isolated database for testing
@pytest.fixture(scope="session")
def db_engine():
    # This fixture yields the database engine bound to the test database
    Base.metadata.drop_all(bind=engine)  # Clean previous test tables (optional but recommended)
    Base.metadata.create_all(bind=engine) # Create all tables needed for tests
    yield engine
    Base.metadata.drop_all(bind=engine)  # Teardown: Drop all tables after testing

# 2. Create a test session fixture
@pytest.fixture(scope="function")
def db_session(db_engine):
    # Use a transactional approach for function-scoped fixtures for isolation
    connection = db_engine.connect()
    transaction = connection.begin()
    
    # Bind a new session to the connection and transaction
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    db = TestingSessionLocal()

    yield db # Provide the session to the test

    # Teardown: Rollback the transaction to clean up any changes made by the test
    db.close()
    transaction.rollback()
    connection.close()

# 3. Override the application's database dependency (get_db)
@pytest.fixture(scope="session")
def client(db_engine):
    
    # Define a dependency override function
    def override_get_db():
        try:
            # We must create a new session here, NOT yield the session from the db_session fixture,
            # to prevent connection pool exhaustion.
            db = SessionLocal()
            yield db
        finally:
            db.close()
            
    # Apply the dependency override
    app.dependency_overrides[get_db] = override_get_db

    # Create the TestClient instance
    with TestClient(app) as c:
        yield c

# 4. Optional: Create the initial admin user for the tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_admin(db_engine):
    # Ensure the admin user exists for test_1 to pass
    # This should be done using the repository logic you defined in init_db
    db = SessionLocal()
    try:
        from src.repositories import AdminRepository
        repo = AdminRepository(db)
        # You need a method in your repository to create the default user.
        # repo.create_default_admin_for_tests() 
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding admin user for tests: {e}")
    finally:
        db.close()