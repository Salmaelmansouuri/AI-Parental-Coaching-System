from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


router = APIRouter(
    prefix="/web",
    tags=["Web Interface"],
)


@router.get(
    "/login",
    response_class=HTMLResponse,
)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "page_title": "Connexion",
        },
    )


@router.get(
    "/parent",
    response_class=HTMLResponse,
)
def parent_dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="parent_dashboard.html",
        context={
            "page_title": "Espace parent",
        },
    )


@router.get(
    "/coach",
    response_class=HTMLResponse,
)
def coach_dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="coach_dashboard.html",
        context={
            "page_title": "Espace coach",
        },
    )
@router.get(
    "/parent/paths/{path_id}",
    response_class=HTMLResponse,
)
def parent_path_page(
    request: Request,
    path_id: int,
):
    return templates.TemplateResponse(
        request=request,
        name="path_detail.html",
        context={
            "page_title": "Parcours de coaching",
            "path_id": path_id,
        },
    )
@router.get(
    "/coach/paths/{path_id}",
    response_class=HTMLResponse,
)
def coach_path_page(
    request: Request,
    path_id: int,
):
    return templates.TemplateResponse(
        request=request,
        name="coach_path_detail.html",
        context={
            "page_title": "Évaluation du parcours",
            "path_id": path_id,
        },
    )