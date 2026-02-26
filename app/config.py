import os
from dotenv import load_dotenv

load_dotenv()

DATA_SOURCE = os.getenv("DATA_SOURCE", "mock")  # "mock", "dsg", or "sportradar"
DSG_API_KEY = os.getenv("DSG_API_KEY", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# SportRadar
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
SR_TIER = os.getenv("SR_TIER", "trial")  # "trial" or "production"
SR_SPORTS = os.getenv("SR_SPORTS", "nba,ncaamb")
SR_SCHEDULE_INTERVAL = int(os.getenv("SR_SCHEDULE_INTERVAL", "300"))  # seconds
SR_GAME_INTERVAL = int(os.getenv("SR_GAME_INTERVAL", "120"))  # seconds between live game polls
SR_DAILY_QUOTA = int(os.getenv("SR_DAILY_QUOTA", "1000"))

# WebSocket relay
RELAY_SECRET = os.getenv("RELAY_SECRET", "")
