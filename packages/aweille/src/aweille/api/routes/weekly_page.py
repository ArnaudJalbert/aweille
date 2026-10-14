"""Serve the weekly browser shell without reading application data."""

from pathlib import Path

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

WEB_DIRECTORY = Path(__file__).parents[2] / "adapters" / "web"
_templates = Jinja2Templates(directory=WEB_DIRECTORY / "templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def weekly_page(request: Request) -> HTMLResponse:
    """Return the weekly page structure; its browser code reads the shared API.

    Args:
        request: Incoming page request, used to resolve asset URLs.

    Returns:
        Rendered HTML shell with no planned-run data.
    """
    return _templates.TemplateResponse(request=request, name="weekly.html")
