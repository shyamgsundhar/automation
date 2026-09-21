import os

from dotenv import load_dotenv

load_dotenv()


# =========================================================
# API KEYS
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

DATABASE_URL = os.getenv("DATABASE_URL")


# =========================================================
# REQUEST SETTINGS
# =========================================================

REQUEST_TIMEOUT = 20

AI_TIMEOUT = 60


# =========================================================
# ARTICLE SETTINGS
# =========================================================

MAX_ARTICLE_CHARS = 12000


# =========================================================
# NEWS FILTERING
# =========================================================

MAX_NEWS_AGE_HOURS = 24


# =========================================================
# ARTICLE SELECTION
# =========================================================

MAX_CANDIDATES = 20

MAX_ARTICLES_TO_SUMMARIZE = 5


# =========================================================
# GROQ MODELS
# =========================================================

GROQ_PRIMARY_MODEL = "qwen/qwen3.8-27b"

GROQ_FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]


# =========================================================
# NVIDIA
# =========================================================

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

NVIDIA_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1.5"


# =========================================================
# SUMMARIZATION
# =========================================================

GROQ_MAX_TOKENS = 220

NVIDIA_MAX_TOKENS = 220

GROQ_TEMPERATURE = 0.7

NVIDIA_TEMPERATURE = 0.7

MAX_SUMMARY_CHARS = 900


# =========================================================
# DISCORD
# =========================================================

MAX_DISCORD_CHARS = 1900

DISCORD_RETRIES = 3

DISCORD_RETRY_DELAY = 0.7

DISCORD_MESSAGE_DELAY = 0.7
