from backend.app.models.child import Child
from backend.app.models.rating import Rating
from backend.app.routes.ratings import router as ratings_router
from backend.app.routes.ai_coach import router as ai_coach_router
from backend.app.models.message import Message
from backend.app.routes.messages import router as messages_router
from backend.app.routes.children import router as children_router
from fastapi import FastAPI
from backend.app.models.coach_evaluation import CoachEvaluation
from backend.app.routes.coach import router as coach_router
from backend.app.routes.auth import router as auth_router
from backend.app.models.coaching_path import CoachingPath
from backend.app.routes.coaching_paths import (
    router as coaching_paths_router,
)
from backend.app.database import Base, engine
from backend.app.models.user import User
from backend.app.routes.users import router as users_router
from backend.app.routes.statistics import router as statistics_router
from pathlib import Path
from backend.app.routes.web import router as web_router
from fastapi.staticfiles import StaticFiles
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Coach parental intelligent",
    description="API du système de coaching parental basé sur le RAG et l'IA",
    version="0.2.0",
)
BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

app.include_router(users_router)
app.include_router(coach_router)
app.include_router(ratings_router)
app.include_router(auth_router)
app.include_router(ai_coach_router)
app.include_router(children_router)
app.include_router(coaching_paths_router)
app.include_router(messages_router)
app.include_router(statistics_router)
app.include_router(web_router)


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "API Coach parental intelligente opérationnelle"
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok"
    }