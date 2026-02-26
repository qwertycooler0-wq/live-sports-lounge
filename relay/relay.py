"""Local relay script — reads scanner DB, pushes changes to Railway via WebSocket.

Runs alongside the centralized scanner. Detects changes in the DB and pushes
only deltas to the Railway app over a single authenticated WebSocket.

Env vars:
    RELAY_SECRET       - shared secret for authentication
    RELAY_URL          - WebSocket URL (e.g. wss://thelivesportslounge.com/ws/relay)
    SCANNER_ROOT       - path to centralized-scanner directory
    SPORTRADAR_API_KEY - for PBP API calls
    SR_TIER            - "trial" or "production"
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────

RELAY_SECRET = os.getenv("RELAY_SECRET", "")
RELAY_URL = os.getenv("RELAY_URL", "")
SCANNER_ROOT = Path(os.getenv("SCANNER_ROOT", "C:/Claude-Coding/centralized-scanner"))
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
SR_TIER = os.getenv("SR_TIER", "trial")
SR_SPORTS = os.getenv("SR_SPORTS", "nba,ncaamb").split(",")

POLL_INTERVAL = 1.0  # seconds between DB checks
HEARTBEAT_INTERVAL = 30.0  # seconds between heartbeats
RECONNECT_DELAY = 5.0  # seconds before reconnect attempt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("relay")

# ── Scanner DB access ─────────────────────────────────────────────

if str(SCANNER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCANNER_ROOT))

from client.db_reader import DBReader  # noqa: E402

DB_PATH = str(SCANNER_ROOT / "scanner.db")
reader = DBReader(DB_PATH, cache_ttl_ms=200, stale_threshold_ms=30_000)


# ── Change tracker ────────────────────────────────────────────────

class ChangeTracker:
    """Tracks content hashes / timestamps to detect actual changes in scanner DB."""

    def __init__(self):
        self._schedule_hash: dict[str, int] = {}  # sport -> hash of schedule JSON
        self._summary_ts: dict[str, float] = {}   # game_id -> last updated_at

    def check_schedule(self, sport: str, data: dict) -> bool:
        """Returns True if schedule content has changed since last check."""
        h = hash(json.dumps(data, sort_keys=True))
        prev = self._schedule_hash.get(sport)
        if prev != h:
            self._schedule_hash[sport] = h
            return True
        return False

    def check_summary(self, game_id: str, updated_at: float) -> bool:
        """Returns True if summary has changed since last check."""
        prev = self._summary_ts.get(game_id, 0.0)
        if updated_at > prev:
            self._summary_ts[game_id] = updated_at
            return True
        return False


# ── PBP fetcher ───────────────────────────────────────────────────

def _base_url(sport: str) -> str:
    return f"https://api.sportradar.com/{sport}/{SR_TIER}/v8/en"


async def fetch_pbp(game_id: str, sport: str) -> dict | None:
    """Fetch PBP from SportRadar API."""
    import httpx

    base = _base_url(sport)
    url = f"{base}/games/{game_id}/pbp.json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params={"api_key": SPORTRADAR_API_KEY})
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                log.warning("PBP 429 rate limited — backing off 60s")
                await asyncio.sleep(60)
            else:
                log.warning("PBP API %d for %s", resp.status_code, game_id)
    except Exception as e:
        log.warning("PBP fetch error for %s: %s", game_id, e)
    return None


def find_sport_for_game(game_id: str) -> str | None:
    """Look up which sport a game belongs to by checking schedules."""
    for sport in SR_SPORTS:
        data = reader.get_sportradar_schedule(sport)
        if not data:
            continue
        for game in data.get("games", []):
            if game.get("id") == game_id:
                return sport
    return None


# ── Main relay ────────────────────────────────────────────────────

async def run_relay():
    """Main entry point — connect to Railway and push data."""
    import websockets

    tracker = ChangeTracker()
    pbp_queue: asyncio.Queue = asyncio.Queue()

    while True:
        url = f"{RELAY_URL}?secret={RELAY_SECRET}"
        log.info("Connecting to %s ...", RELAY_URL)

        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                log.info("Connected to Railway relay endpoint")

                # Run three concurrent tasks
                await asyncio.gather(
                    _poll_and_push(ws, tracker),
                    _listen_for_server_messages(ws, pbp_queue),
                    _process_pbp_queue(ws, pbp_queue),
                )

        except asyncio.CancelledError:
            log.info("Relay shutting down")
            return
        except Exception as e:
            log.warning("Relay connection lost: %s — reconnecting in %ds", e, int(RECONNECT_DELAY))
            await asyncio.sleep(RECONNECT_DELAY)


async def _poll_and_push(ws, tracker: ChangeTracker):
    """Poll scanner DB every 1s and push changes to Railway."""
    last_heartbeat = time.time()

    while True:
        try:
            # Check schedules for changes
            for sport in SR_SPORTS:
                sport = sport.strip()
                data = reader.get_sportradar_schedule(sport)
                if not data:
                    continue

                if tracker.check_schedule(sport, data):
                    await ws.send(json.dumps({
                        "type": "schedule",
                        "sport": sport,
                        "data": data,
                    }))
                    log.debug("Pushed schedule update for %s", sport)

                # Check summaries for live games
                for game in data.get("games", []):
                    status = game.get("status", "")
                    game_id = game.get("id", "")
                    if not game_id:
                        continue

                    # Only actively push summaries for live/halftime games
                    if status not in ("inprogress", "halftime"):
                        continue

                    game_obj = reader.get_sportradar_game(game_id)
                    if not game_obj or game_obj.game_data_json == "{}":
                        continue

                    # Use the model's updated_at for change detection
                    updated = game_obj.updated_at if hasattr(game_obj, 'updated_at') else 0.0
                    if isinstance(updated, str):
                        updated = time.time()  # fallback if string

                    if tracker.check_summary(game_id, updated):
                        await ws.send(json.dumps({
                            "type": "summary",
                            "game_id": game_id,
                            "data": json.loads(game_obj.game_data_json),
                        }))
                        log.debug("Pushed summary update for %s", game_id)

            # Heartbeat
            if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
                await ws.send(json.dumps({"type": "heartbeat"}))
                last_heartbeat = time.time()

        except Exception as e:
            log.warning("Poll loop error: %s", e)
            raise  # Let the outer loop handle reconnection

        await asyncio.sleep(POLL_INTERVAL)


async def _listen_for_server_messages(ws, pbp_queue: asyncio.Queue):
    """Listen for messages from Railway (e.g., PBP requests)."""
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "request_pbp":
                game_id = msg.get("game_id", "")
                if game_id:
                    await pbp_queue.put(game_id)
                    log.info("PBP requested for %s", game_id)

    except Exception as e:
        log.warning("Server listener error: %s", e)
        raise


async def _process_pbp_queue(ws, pbp_queue: asyncio.Queue):
    """Process PBP requests — fetch from SR API and push to Railway."""
    last_request = 0.0

    while True:
        game_id = await pbp_queue.get()

        # Rate limit: 1 QPS for SR API
        elapsed = time.time() - last_request
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)

        sport = find_sport_for_game(game_id)
        if not sport:
            log.warning("Could not find sport for game %s", game_id)
            continue

        data = await fetch_pbp(game_id, sport)
        last_request = time.time()

        if data:
            await ws.send(json.dumps({
                "type": "pbp",
                "game_id": game_id,
                "data": data,
            }))
            log.info("Pushed PBP for %s (%d bytes)", game_id, len(json.dumps(data)))


# ── Entry point ───────────────────────────────────────────────────

if __name__ == "__main__":
    if not RELAY_SECRET:
        log.error("RELAY_SECRET not set — aborting")
        sys.exit(1)
    if not RELAY_URL:
        log.error("RELAY_URL not set — aborting")
        sys.exit(1)
    if not Path(DB_PATH).exists():
        log.error("Scanner DB not found at %s", DB_PATH)
        sys.exit(1)

    log.info("Starting relay — DB=%s → %s", DB_PATH, RELAY_URL)
    asyncio.run(run_relay())
