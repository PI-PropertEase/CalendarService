import firebase_admin
from fastapi import FastAPI, status
from contextlib import asynccontextmanager

from firebase_admin import credentials

from CalendarService import models
from CalendarService.database import engine
from CalendarService.messaging_operations import consume
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from CalendarService.routers.apirouter import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(consume(loop))
    yield


cred = credentials.Certificate(".secret.json")
firebase_admin.initialize_app(cred)
models.Base.metadata.create_all(bind=engine)
app = FastAPI(lifespan=lifespan, root_path="/api/CalendarService")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["healthcheck"], summary="Perform a Health Check",
         response_description="Return HTTP Status Code 200 (OK)", status_code=status.HTTP_200_OK)
def get_health():
    return {"status": "ok"}


app.include_router(api_router)

