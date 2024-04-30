import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from CalendarService import models
from datetime import datetime


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


def test_get_cleaning_id(test_db: Session):
    db_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    test_db.add(db_event)
    test_db.commit()

    print("Getting events from db: ", test_db.query(models.Cleaning).all())