"""Serve the weekly browser shell without reading application data."""

from pathlib import Path

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

WEB_DIRECTORY = Path(__file__).parents[1]
_templates = Jinja2Templates(directory=WEB_DIRECTORY / "templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def weekly_page(request: Request) -> HTMLResponse:
    """Return the weekly page structure; its browser code reads the shared API.

    Args:
        request: Incoming page request, used to resolve asset URLs.

    Returns:
        Rendered HTML shell with no planned-course data.
    """
    return _templates.TemplateResponse(request=request, name="weekly.html")


@router.get(
    "/planned-courses/new", response_class=HTMLResponse, include_in_schema=False
)
def creation_page(request: Request) -> HTMLResponse:
    """Return the manual creation form, which saves through the shared API.

    Args:
        request: Incoming page request, used to resolve asset URLs.

    Returns:
        Rendered form shell with no access to planned-course storage.
    """
    return _templates.TemplateResponse(request=request, name="create_course.html")


@router.get(
    "/planned-courses/{id}/edit", response_class=HTMLResponse, include_in_schema=False
)
def edit_page(request: Request, id: str) -> HTMLResponse:
    """Return an editing shell; JavaScript loads current data through the API."""
    return _templates.TemplateResponse(request=request, name="edit_course.html")
