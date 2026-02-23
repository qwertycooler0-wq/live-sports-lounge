from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from ..data.provider import DataProvider

router = APIRouter()
templates: Jinja2Templates = None  # injected by main.py
provider: DataProvider = None  # injected by main.py


@router.get("/")
async def home(request: Request, sport: str = "all"):
    games = await provider.get_scoreboard(sport)
    return templates.TemplateResponse("home.html", {
        "request": request,
        "games": games,
        "current_sport": sport,
    })


@router.get("/game/{game_id}")
async def game(request: Request, game_id: str):
    detail = await provider.get_game(game_id)
    if not detail:
        return templates.TemplateResponse("home.html", {
            "request": request,
            "games": [],
            "current_sport": "all",
        })
    return templates.TemplateResponse("game.html", {
        "request": request,
        "game": detail,
    })


@router.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})
