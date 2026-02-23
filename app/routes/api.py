from fastapi import APIRouter, HTTPException

from ..data.provider import DataProvider

router = APIRouter()
provider: DataProvider = None  # injected by main.py


@router.get("/scoreboard")
async def scoreboard(sport: str = "all"):
    games = await provider.get_scoreboard(sport)
    return {"games": [g.to_dict() for g in games]}


@router.get("/game/{game_id}")
async def game_detail(game_id: str):
    detail = await provider.get_game(game_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Game not found")
    return detail.to_dict()


@router.get("/game/{game_id}/pbp")
async def game_pbp(game_id: str):
    events = await provider.get_play_by_play(game_id)
    if events is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"events": [e.to_dict() for e in events]}
