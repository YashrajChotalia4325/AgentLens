import os

from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://agentlens:agentlens@localhost:5432/agentlens")

# The model that grades answers in the LLM-as-a-judge evaluator.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")

# Shared secret between the dashboard and this API. Leave it unset locally.
# When deployed, set the same value on both, so only the dashboard can call the API.
API_TOKEN = os.getenv("API_TOKEN")
