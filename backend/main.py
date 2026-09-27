"""AgentLens API.

Run from the backend/ folder:
    uvicorn main:app --reload
Then open http://localhost:8000/docs to try the endpoints.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.db import init_db
from routes import experiments, runs, stats


@asynccontextmanager
async def lifespan(app):
    init_db()  # create tables on startup if they don't exist
    yield


app = FastAPI(title="AgentLens", lifespan=lifespan)

# No CORS setup needed: the browser never calls this API directly. The Next.js
# server fetches data (and submits new runs) on the browser's behalf.
app.include_router(runs.router)
app.include_router(experiments.router)
app.include_router(stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
