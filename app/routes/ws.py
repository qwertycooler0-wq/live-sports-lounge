"""WebSocket endpoints: /ws/relay (authenticated relay) + /ws/live (browsers)."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from .. import config
from ..realtime import manager

log = logging.getLogger("ws")
router = APIRouter()


@router.websocket("/ws/relay")
async def ws_relay(ws: WebSocket, secret: str = Query("")):
    """Authenticated endpoint for the local relay script."""
    if not config.RELAY_SECRET or secret != config.RELAY_SECRET:
        await ws.accept()
        await ws.close(code=4001, reason="unauthorized")
        log.warning("Relay auth failed (secret %s)", "not configured" if not config.RELAY_SECRET else "mismatch")
        return

    await ws.accept()
    await manager.connect_relay(ws)

    try:
        while True:
            raw = await ws.receive_text()
            await manager.handle_relay_message(raw)
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("Relay WebSocket error")
    finally:
        await manager.disconnect_relay(ws)


@router.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    """Public endpoint for browser clients."""
    await ws.accept()
    await manager.connect_browser(ws)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "subscribe":
                topic = msg.get("topic", "")
                if not topic:
                    continue

                await manager.subscribe(ws, topic)

                # Send current state immediately
                try:
                    if topic == "scoreboard":
                        payload = await manager.get_scoreboard_payload()
                        await ws.send_text(payload)
                    elif topic.startswith("game:"):
                        game_id = topic.split(":", 1)[1]
                        payload = await manager.get_game_payload(game_id)
                        if payload:
                            await ws.send_text(payload)
                        # Request PBP from relay so it starts streaming it
                        await manager.request_pbp(game_id)
                except Exception:
                    pass

            elif msg_type == "unsubscribe":
                topic = msg.get("topic", "")
                if topic:
                    await manager.unsubscribe(ws, topic)

            elif msg_type == "request_pbp":
                game_id = msg.get("game_id", "")
                if game_id:
                    await manager.request_pbp(game_id)

    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("Browser WebSocket error")
    finally:
        await manager.disconnect_browser(ws)
