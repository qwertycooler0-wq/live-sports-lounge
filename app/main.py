from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config
from .data.mock_provider import MockProvider
from .data.dsg_provider import DSGProvider
from .routes import pages, api

app = FastAPI(title="The Live Sports Lounge")

# ── Static files + templates ────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ── Data provider ───────────────────────────────────────────────────
if config.DATA_SOURCE == "dsg" and config.DSG_API_KEY:
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
