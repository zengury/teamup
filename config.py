import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

AGENT_MODELS = {
    "elon": "claude-opus-4-7",
    "jobs": "claude-opus-4-7",
    "linux": "claude-opus-4-7",
    "turing": "claude-sonnet-4-6",
    "bezos": "claude-sonnet-4-6",
}

MAX_TOKENS = {
    "elon": 16384,
    "jobs": 8192,
    "linux": 8192,
    "turing": 8192,
    "bezos": 8192,
}
