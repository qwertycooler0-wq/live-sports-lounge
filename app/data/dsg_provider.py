import httpx
from .provider import (
    DataProvider, GameSummary, GameDetail, PlayerStats, PlayEvent
)


class DSGProvider(DataProvider):
    """DSG API integration — stub until API key arrives."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://dsg-api.com/api/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=10.0,
        )

    async def get_scoreboard(self, sport: str = "all") -> list[GameSummary]:
        # TODO: implement once DSG API key + docs are available
        # Expected endpoint: GET /sports/{sport}/scoreboard?date=today
        raise NotImplementedError("DSG provider not yet implemented — awaiting API key")

    async def get_game(self, game_id: str) -> GameDetail | None:
        # TODO: implement once DSG API key + docs are available
        # Expected endpoint: GET /games/{game_id}/detail
        raise NotImplementedError("DSG provider not yet implemented — awaiting API key")

    async def get_play_by_play(self, game_id: str) -> list[PlayEvent]:
        # TODO: implement once DSG API key + docs are available
        # Expected endpoint: GET /games/{game_id}/pbp
        raise NotImplementedError("DSG provider not yet implemented — awaiting API key")
