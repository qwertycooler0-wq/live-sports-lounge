import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config
from .data.mock_provider import MockProvider
from .data.dsg_provider import DSGProvider
from .routes import pages, api, ws

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# ── Lifespan ─────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    if config.DATA_SOURCE == "sportradar":
        logging.getLogger("main").info(
            "Relay mode — waiting for relay WebSocket connection"
        )
    yield


app = FastAPI(title="The Live Sports Lounge", lifespan=lifespan)

# ── Static files + templates ────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ── Data provider ───────────────────────────────────────────────────
if config.DATA_SOURCE == "sportradar" and config.SPORTRADAR_API_KEY:
    from .data.sr_provider import SRProvider
    provider = SRProvider()
elif config.DATA_SOURCE == "dsg" and config.DSG_API_KEY:
    provider = DSGProvider(api_key=config.DSG_API_KEY)
else:
    provider = MockProvider()

# Inject into route modules
pages.templates = templates
pages.provider = provider
api.provider = provider

# ── Routes ──────────────────────────────────────────────────────────
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
app.include_router(ws.router)
