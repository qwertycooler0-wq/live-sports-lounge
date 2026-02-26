"""Background poller that reads SportRadar data from the centralized scanner DB.

Runs as an asyncio.Task via FastAPI lifespan.
- Reads schedules and game summaries from the shared scanner SQLite DB
- PBP still fetched directly from SportRadar API (on-demand only)
- No schedule/summary API calls — the centralized scanner handles all polling
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

import httpx

from .. import config
from .scanner_bridge import reader
from .sr_cache import cache

log = logging.getLogger("sr_poller")


# SR API base URLs by sport (still needed for PBP calls)
def _base_url(sport: str) -> str:
    tier = config.SR_TIER  # "trial" or "production"
    return f"https://api.sportradar.com/{sport}/{tier}/v8/en"


class RateLimiter:
    """Enforce 1 QPS and daily quota (used for PBP API calls only)."""

    def __init__(self, daily_quota: int):
        self.daily_quota = daily_quota
        self._last_request = 0.0
        self._daily_count = 0
        self._day_start = self._today()

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async def acquire(self) -> bool:
        """Wait for rate limit, return False if quota exhausted."""
        today = self._today()
        if today != self._day_start:
            self._daily_count = 0
            self._day_start = today

        if self._daily_count >= self.daily_quota:
            log.warning("Daily quota exhausted (%d/%d)", self._daily_count, self.daily_quota)
            return False

        elapsed = time.time() - self._last_request
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)

        self._last_request = time.time()
        self._daily_count += 1
        return True

    @property
    def remaining(self) -> int:
        return max(0, self.daily_quota - self._daily_count)


class SRPoller:
    def __init__(self):
        self.sports = [s.strip() for s in config.SR_SPORTS.split(",") if s.strip()]
        self.limiter = RateLimiter(config.SR_DAILY_QUOTA)  # PBP only
        self.client: httpx.AsyncClient | None = None
        self._running = False

    async def start(self):
        self.client = httpx.AsyncClient(timeout=15.0)  # for PBP only
        self._running = True
        log.info("SR poller started (scanner DB mode) — sports=%s", self.sports)

    async def stop(self):
        self._running = False
        if self.client:
            await self.client.aclose()
        log.info("SR poller stopped (used %d PBP requests today)",
                 self.limiter.daily_quota - self.limiter.remaining)

    # ── DB reads (schedules + summaries from centralized scanner) ──

    def _read_schedules(self) -> bool:
        """Read schedules from scanner DB → populate cache. Returns True if any data found."""
        found_any = False
        for sport in self.sports:
            data = reader.get_sportradar_schedule(sport)
            if data:
                cache.set_schedule(sport, data)
                found_any = True
        return found_any

    def _read_live_summaries(self):
        """Read live game summaries from scanner DB → populate cache."""
        for game_id in cache.get_live_game_ids():
            game = reader.get_sportradar_game(game_id)
            if game and game.game_data_json != "{}":
                cache.set_summary(game_id, json.loads(game.game_data_json))

    def _load_missing_summaries(self):
        """Load summaries for games not yet in cache (completed/scheduled).

        Called at startup and after schedule refreshes so game detail pages
        have player stats for finished games.
        """
        for game_id in cache.get_all_game_ids():
            if game_id in cache.summaries:
                continue
            game = reader.get_sportradar_game(game_id)
            if game and game.game_data_json != "{}":
                cache.set_summary(game_id, json.loads(game.game_data_json))

    # ── PBP (still direct API call) ────────────────────────────────

    def _sport_for_game(self, game_id: str) -> str | None:
        """Look up which sport a game_id belongs to."""
        for sport, entry in cache.schedules.items():
            for game in entry.data.get("games", []):
                if game.get("id") == game_id:
                    return sport
        return None

    async def _fetch_pbp(self, game_id: str):
        """Fetch PBP from SR API (unchanged — still direct API call)."""
        sport = self._sport_for_game(game_id)
        if not sport:
            return
        if not await self.limiter.acquire():
            return
        base = _base_url(sport)
        url = f"{base}/games/{game_id}/pbp.json"
        try:
            resp = await self.client.get(url, params={"api_key": config.SPORTRADAR_API_KEY})
            if resp.status_code == 200:
                cache.set_pbp(game_id, resp.json())
            elif resp.status_code == 429:
                log.warning("PBP 429 rate limited — backing off 60s")
                await asyncio.sleep(60)
            elif resp.status_code == 403:
                log.error("PBP 403 forbidden — check API key")
            else:
                log.warning("PBP API %d for %s", resp.status_code, url)
        except httpx.RequestError as e:
            log.warning("PBP fetch error: %s", e)

    # ── Main loop ──────────────────────────────────────────────────

    async def run(self):
        """Main polling loop — reads from scanner DB, PBP from API."""
        await self.start()
        try:
            # Initial schedule read (off event loop thread)
            found = await asyncio.to_thread(self._read_schedules)
            if not found:
                log.warning(
                    "No schedule data in scanner DB — "
                    "website will show no games until the scanner runs"
                )

            # Load all available summaries (completed games, etc.)
            await asyncio.to_thread(self._load_missing_summaries)

            schedule_timer = time.time()
            while self._running:
                # Refresh schedules from DB every 15s
                # (scanner refreshes from API every 60-120s, so 15s is plenty)
                if time.time() - schedule_timer >= 15:
                    await asyncio.to_thread(self._read_schedules)
                    await asyncio.to_thread(self._load_missing_summaries)
                    schedule_timer = time.time()

                # Read live game summaries from DB (updated frequently)
                await asyncio.to_thread(self._read_live_summaries)

                # PBP: on-demand from API for games with active viewers
                pbp_requested = cache.get_pbp_requested()
                for gid in pbp_requested:
                    if not self._running:
                        break
                    await self._fetch_pbp(gid)

                await asyncio.sleep(2)

        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()


# Module-level instance
poller = SRPoller()
