import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from CalendarService import models

@pytest.fixture
def test_db():
    print("Creating in-memory database...")
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    print("Cleaning up in-memory database...")
    models.Base.metadata.create_all(bind=engine)