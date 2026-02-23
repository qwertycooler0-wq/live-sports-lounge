import os
from dotenv import load_dotenv

load_dotenv()

DATA_SOURCE = os.getenv("DATA_SOURCE", "mock")  # "mock" or "dsg"
DSG_API_KEY = os.getenv("DSG_API_KEY", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
