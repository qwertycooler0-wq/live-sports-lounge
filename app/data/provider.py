from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict


@dataclass
class GameSummary:
    game_id: str
    sport: str              # "nba" or "ncaamb"
    status: str             # "scheduled", "live", "final"
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    period: int
    clock: str
    start_time: str

    def to_dict(self):
        return asdict(self)


@dataclass
class PlayerStats:
    name: str
    position: str
    minutes: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    fg: str
    three_pt: str
    ft: str
    plus_minus: int

    def to_dict(self):
        return asdict(self)


@dataclass
class PlayEvent:
    event_id: int
    clock: str
    period: int
    team: str
    player: str
    description: str
    home_score: int
    away_score: int

    def to_dict(self):
        return asdict(self)


@dataclass
class GameDetail:
    summary: GameSummary
    home_players: list[PlayerStats] = field(default_factory=list)
    away_players: list[PlayerStats] = field(default_factory=list)
    play_by_play: list[PlayEvent] = field(default_factory=list)
    home_team_stats: dict = field(default_factory=dict)
    away_team_stats: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "summary": self.summary.to_dict(),
            "home_players": [p.to_dict() for p in self.home_players],
            "away_players": [p.to_dict() for p in self.away_players],
            "play_by_play": [e.to_dict() for e in self.play_by_play],
            "home_team_stats": self.home_team_stats,
            "away_team_stats": self.away_team_stats,
        }


class DataProvider(ABC):
    @abstractmethod
    async def get_scoreboard(self, sport: str = "all") -> list[GameSummary]:
        ...

    @abstractmethod
    async def get_game(self, game_id: str) -> GameDetail | None:
        ...

    @abstractmethod
    async def get_play_by_play(self, game_id: str) -> list[PlayEvent]:
        ...
