"""In-memory cache singleton for SportRadar data.

All website visitors read from this one cache — zero per-user API calls.
The background poller (sr_poller.py) is the only writer.
"""

import time
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    data: dict
    updated_at: float = 0.0


class SRCache:
    """Thread-safe (GIL) in-memory cache for SR responses."""

    def __init__(self):
        # {sport: schedule_json}
        self.schedules: dict[str, CacheEntry] = {}
        # {game_id: summary_json}
        self.summaries: dict[str, CacheEntry] = {}
        # {game_id: pbp_json}
        self.pbp: dict[str, CacheEntry] = {}
        # Games that have active viewers wanting PBP data
        self._pbp_requested: set[str] = set()

    # ── Writers (called by poller) ──────────────────────────────────

    def set_schedule(self, sport: str, data: dict):
        self.schedules[sport] = CacheEntry(data=data, updated_at=time.time())

    def set_summary(self, game_id: str, data: dict):
        self.summaries[game_id] = CacheEntry(data=data, updated_at=time.time())

    def set_pbp(self, game_id: str, data: dict):
        self.pbp[game_id] = CacheEntry(data=data, updated_at=time.time())

    # ── Readers (called by provider) ────────────────────────────────

    def get_schedule(self, sport: str) -> dict | None:
        entry = self.schedules.get(sport)
        return entry.data if entry else None

    def get_summary(self, game_id: str) -> dict | None:
        entry = self.summaries.get(game_id)
        return entry.data if entry else None

    def get_pbp_data(self, game_id: str) -> dict | None:
        entry = self.pbp.get(game_id)
        return entry.data if entry else None

    def get_schedule_age(self, sport: str) -> float:
        entry = self.schedules.get(sport)
        return time.time() - entry.updated_at if entry else float("inf")

    # ── Live game tracking ──────────────────────────────────────────

    def get_live_game_ids(self) -> list[str]:
        """Return game IDs from schedules that are currently in-progress."""
        live = []
        for sport, entry in self.schedules.items():
            for game in entry.data.get("games", []):
                status = game.get("status", "")
                if status in ("inprogress", "halftime"):
                    live.append(game.get("id", ""))
        return [g for g in live if g]

    def get_all_game_ids(self) -> list[str]:
        """Return all game IDs from today's schedules."""
        ids = []
        for sport, entry in self.schedules.items():
            for game in entry.data.get("games", []):
                gid = game.get("id", "")
                if gid:
                    ids.append(gid)
        return ids

    # ── PBP demand tracking ─────────────────────────────────────────

    def request_pbp(self, game_id: str):
        """Mark a game as needing PBP data (user viewing game detail)."""
        self._pbp_requested.add(game_id)

    def get_pbp_requested(self) -> set[str]:
        """Return and clear the set of games needing PBP."""
        requested = self._pbp_requested.copy()
        self._pbp_requested.clear()
        return requested


# Module-level singleton
cache = SRCache()
