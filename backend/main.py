"""AgentLens API.

Run from the backend/ folder:
    uvicorn main:app --reload
Then open http://localhost:8000/docs to try the endpoints.
"""

import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException

import config
from database.db import init_db
from routes import experiments, runs, stats


@asynccontextmanager
async def lifespan(app):
    init_db()  # create tables on startup if they don't exist
    yield


def require_token(authorization: str | None = Header(default=None)):
    # Once deployed, this API is on the public internet. Without a check, anyone
    # who found the URL could run the agent on our Groq quota or read every run.
    if not config.API_TOKEN:
        return  # local development: no token configured
    # compare_digest takes the same time whether the first or last character is
    # wrong, so the token can't be guessed by timing the responses.
    if not secrets.compare_digest(authorization or "", f"Bearer {config.API_TOKEN}"):
        raise HTTPException(status_code=401, detail="Missing or invalid API token")


app = FastAPI(title="AgentLens", lifespan=lifespan)

# No CORS setup needed: the browser never calls this API directly. The Next.js
# server fetches data (and submits new runs) on the browser's behalf.
protected = [Depends(require_token)]
app.include_router(runs.router, dependencies=protected)
app.include_router(experiments.router, dependencies=protected)
app.include_router(stats.router, dependencies=protected)


@app.get("/api/health")
def health():
    return {"status": "ok"}
