"""Async background poller for SportRadar API.

Runs as an asyncio.Task via FastAPI lifespan.
- Polls daily schedule every SR_SCHEDULE_INTERVAL per sport
- Polls game summary for in-progress games, round-robin ~1/sec
- PBP only fetched for games with active viewers (demand-driven)
- Rate limiter: 1 QPS + daily quota cap
"""

import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx

from .. import config
from .sr_cache import cache

log = logging.getLogger("sr_poller")

# SR API base URLs by sport (tier from config)
def _base_url(sport: str) -> str:
    tier = config.SR_TIER  # "trial" or "production"
    return f"https://api.sportradar.com/{sport}/{tier}/v8/en"


class RateLimiter:
    """Enforce 1 QPS and daily quota."""

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
        self.limiter = RateLimiter(config.SR_DAILY_QUOTA)
        self.client: httpx.AsyncClient | None = None
        self._running = False

    async def start(self):
        self.client = httpx.AsyncClient(timeout=15.0)
        self._running = True
        log.info("SR poller started — sports=%s, quota=%d", self.sports, config.SR_DAILY_QUOTA)

    async def stop(self):
        self._running = False
        if self.client:
            await self.client.aclose()
        log.info("SR poller stopped (used %d requests today)", self.limiter.daily_quota - self.limiter.remaining)

    async def _fetch(self, url: str) -> dict | None:
        """Fetch a SR endpoint with rate limiting and error handling."""
        if not await self.limiter.acquire():
            return None
        try:
            resp = await self.client.get(url, params={"api_key": config.SPORTRADAR_API_KEY})
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                log.warning("429 rate limited — backing off 60s")
                await asyncio.sleep(60)
                return None
            if resp.status_code == 403:
                log.error("403 forbidden — check API key")
                return None
            log.warning("SR API %d for %s", resp.status_code, url)
            return None
        except httpx.RequestError as e:
            log.warning("SR request error: %s", e)
            return None

    async def poll_schedule(self, sport: str):
        """Fetch today's schedule for a sport."""
        now = datetime.now(timezone.utc)
        base = _base_url(sport)
        url = f"{base}/games/{now.year}/{now.month:02d}/{now.day:02d}/schedule.json"
        data = await self._fetch(url)
        if data:
            cache.set_schedule(sport, data)
            game_count = len(data.get("games", []))
            log.info("Schedule updated: %s — %d games", sport, game_count)

    async def poll_summary(self, game_id: str):
        """Fetch game summary for a specific game."""
        sport = self._sport_for_game(game_id)
        if not sport:
            return
        base = _base_url(sport)
        url = f"{base}/games/{game_id}/summary.json"
        data = await self._fetch(url)
        if data:
            cache.set_summary(game_id, data)

    async def poll_pbp(self, game_id: str):
        """Fetch play-by-play for a specific game (on-demand only)."""
        sport = self._sport_for_game(game_id)
        if not sport:
            return
        base = _base_url(sport)
        url = f"{base}/games/{game_id}/pbp.json"
        data = await self._fetch(url)
        if data:
            cache.set_pbp(game_id, data)

    def _sport_for_game(self, game_id: str) -> str | None:
        """Look up which sport a game_id belongs to."""
        for sport, entry in cache.schedules.items():
            for game in entry.data.get("games", []):
                if game.get("id") == game_id:
                    return sport
        return None

    async def run(self):
        """Main polling loop."""
        await self.start()
        try:
            # Initial schedule fetch for all sports
            for sport in self.sports:
                await self.poll_schedule(sport)

            schedule_timer = time.time()
            while self._running:
                # Refresh schedules periodically
                if time.time() - schedule_timer >= config.SR_SCHEDULE_INTERVAL:
                    for sport in self.sports:
                        await self.poll_schedule(sport)
                    schedule_timer = time.time()

                # Poll summaries for live games (+ recently scheduled for pre-game data)
                live_ids = cache.get_live_game_ids()
                all_ids = cache.get_all_game_ids()

                # For live games, poll summaries round-robin
                for gid in live_ids:
                    if not self._running:
                        break
                    await self.poll_summary(gid)

                # For non-live games, poll summaries much less often
                # (just one pass through at startup or schedule refresh is enough)
                # Only poll summaries for games that don't have one cached yet
                for gid in all_ids:
                    if not self._running:
                        break
                    if gid not in live_ids and gid not in cache.summaries:
                        await self.poll_summary(gid)

                # PBP: only for games with active viewers
                pbp_requested = cache.get_pbp_requested()
                for gid in pbp_requested:
                    if not self._running:
                        break
                    if gid in live_ids or gid in all_ids:
                        await self.poll_pbp(gid)

                # Sleep between polling cycles — longer if no live games
                if live_ids:
                    await asyncio.sleep(config.SR_GAME_INTERVAL)
                else:
                    await asyncio.sleep(30)

        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()


# Module-level instance
poller = SRPoller()
