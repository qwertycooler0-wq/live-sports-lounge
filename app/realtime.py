"""ConnectionManager — manages relay + browser WebSocket connections, broadcasts updates."""

import asyncio
import json
import logging
import time

from fastapi import WebSocket

from .data.sr_cache import cache
from .data.sr_provider import SRProvider

log = logging.getLogger("realtime")


class ConnectionManager:
    def __init__(self):
        self.relay_ws: WebSocket | None = None
        self._browsers: set[WebSocket] = set()
        # topic -> set of browser websockets
        self._subscriptions: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._provider = SRProvider()
        self._relay_connected_at: float = 0.0

    # ── Relay connection ────────────────────────────────────────────

    async def connect_relay(self, ws: WebSocket):
        async with self._lock:
            if self.relay_ws is not None:
                try:
                    await self.relay_ws.close()
                except Exception:
                    pass
            self.relay_ws = ws
            self._relay_connected_at = time.time()
        log.info("Relay connected")

    async def disconnect_relay(self):
        async with self._lock:
            self.relay_ws = None
        log.info("Relay disconnected")

    @property
    def relay_is_connected(self) -> bool:
        return self.relay_ws is not None

    # ── Browser connections ─────────────────────────────────────────

    async def connect_browser(self, ws: WebSocket):
        async with self._lock:
            self._browsers.add(ws)
        log.debug("Browser connected (%d total)", len(self._browsers))

    async def disconnect_browser(self, ws: WebSocket):
        async with self._lock:
            self._browsers.discard(ws)
            # Remove from all subscriptions
            for topic_subs in self._subscriptions.values():
                topic_subs.discard(ws)
        log.debug("Browser disconnected (%d remaining)", len(self._browsers))

    async def subscribe(self, ws: WebSocket, topic: str):
        async with self._lock:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = set()
            self._subscriptions[topic].add(ws)
        log.debug("Browser subscribed to %s", topic)

    async def unsubscribe(self, ws: WebSocket, topic: str):
        async with self._lock:
            if topic in self._subscriptions:
                self._subscriptions[topic].discard(ws)

    # ── Handle relay messages ───────────────────────────────────────

    async def handle_relay_message(self, raw: str):
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("Invalid JSON from relay")
            return

        msg_type = msg.get("type")

        if msg_type == "schedule":
            sport = msg.get("sport", "")
            data = msg.get("data", {})
            if sport and data:
                cache.set_schedule(sport, data)
                await self._broadcast_scoreboard()

        elif msg_type == "summary":
            game_id = msg.get("game_id", "")
            data = msg.get("data", {})
            if game_id and data:
                cache.set_summary(game_id, data)
                await self._broadcast_scoreboard()
                await self._broadcast_game_update(game_id)

        elif msg_type == "pbp":
            game_id = msg.get("game_id", "")
            data = msg.get("data", {})
            if game_id and data:
                cache.set_pbp(game_id, data)
                await self._broadcast_game_update(game_id)

        elif msg_type == "heartbeat":
            pass  # Keep-alive, no action needed

        else:
            log.debug("Unknown relay message type: %s", msg_type)

    # ── Request PBP from relay ──────────────────────────────────────

    async def request_pbp(self, game_id: str):
        if self.relay_ws:
            try:
                await self.relay_ws.send_json({
                    "type": "request_pbp",
                    "game_id": game_id,
                })
            except Exception:
                log.warning("Failed to send PBP request to relay")

    # ── Broadcast helpers ───────────────────────────────────────────

    async def _broadcast_scoreboard(self):
        subs = self._subscriptions.get("scoreboard", set()).copy()
        if not subs:
            return

        try:
            games = await self._provider.get_scoreboard("all")
            payload = json.dumps({
                "type": "scoreboard",
                "games": [g.to_dict() for g in games],
            })
        except Exception:
            log.exception("Error building scoreboard payload")
            return

        await self._send_to_many(subs, payload)

    async def _broadcast_game_update(self, game_id: str):
        topic = f"game:{game_id}"
        subs = self._subscriptions.get(topic, set()).copy()
        if not subs:
            return

        try:
            detail = await self._provider.get_game(game_id)
            if not detail:
                return
            payload = json.dumps({
                "type": "game_update",
                "game_id": game_id,
                "data": detail.to_dict(),
            })
        except Exception:
            log.exception("Error building game update payload")
            return

        await self._send_to_many(subs, payload)

    async def _send_to_many(self, websockets: set[WebSocket], payload: str):
        dead = []
        sends = []
        for ws in websockets:
            sends.append(self._safe_send(ws, payload, dead))
        await asyncio.gather(*sends)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._browsers.discard(ws)
                    for topic_subs in self._subscriptions.values():
                        topic_subs.discard(ws)

    async def _safe_send(self, ws: WebSocket, payload: str, dead: list):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)

    # ── Initial state for new subscribers ───────────────────────────

    async def get_scoreboard_payload(self) -> str:
        games = await self._provider.get_scoreboard("all")
        return json.dumps({
            "type": "scoreboard",
            "games": [g.to_dict() for g in games],
        })

    async def get_game_payload(self, game_id: str) -> str | None:
        detail = await self._provider.get_game(game_id)
        if not detail:
            return None
        return json.dumps({
            "type": "game_update",
            "game_id": game_id,
            "data": detail.to_dict(),
        })


# Module-level singleton
manager = ConnectionManager()
