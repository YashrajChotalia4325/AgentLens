# AgentLens

A small observability and evaluation tool for AI agents. It records everything an agent does during a run (every LLM call, tool call, token count and millisecond), grades the result, and tells you when a new version of the agent got worse.

It's a learning project, inspired by tools like LangSmith and Langfuse but built from scratch. Every piece is simple enough to read in one sitting.

## Why it exists

When an agent gives a bad answer, the final text doesn't tell you why. Did it call the wrong tool? Did the tool return an error? Did it ignore the tool result and make something up? And when you change the prompt or switch to a cheaper model, how do you know you didn't break something?

AgentLens answers three questions:

1. **What happened?** A step-by-step trace of each run.
2. **Was it good?** Rule-based checks plus an LLM judge.
3. **Did it get worse?** Run the same test dataset on two versions and compare.

## Architecture

```
          ┌────────────────────────────┐
          │  Next.js dashboard (:3000) │   Server Components fetch from the API.
          └──────────────┬─────────────┘   The browser never calls FastAPI directly.
                         │ HTTP/JSON
          ┌──────────────▼─────────────┐
 CLI ────►│   FastAPI backend (:8000)  │
          │                            │
          │  agent loop ──► Groq LLM   │
          │    │  └─ tools             │
          │  tracer (records steps)    │
          │  evaluators ──► LLM judge  │
          │  regression comparison     │
          └──────────────┬─────────────┘
                         │ SQLAlchemy
          ┌──────────────▼─────────────┐
          │ PostgreSQL                 │
          │ experiments · runs ·       │
          │ steps · evaluations        │
          └────────────────────────────┘
```

**What happens in one run:**

```
input ─► run_agent()                      agent/support_agent.py
           ├─ tracer.step("llm")    planner decides to call lookup_order
           ├─ tracer.step("tool")   lookup_order(order_id="1042")
           └─ tracer.step("llm")    final answer
         ─► Trace (plain data)        tracing/tracer.py
         ─► save_trace()              database/save.py   → runs + steps
         ─► evaluate_run()            services/run_service.py → evaluations
```

## Features

- **Tracing:** run ID, agent name/version, model, input and output, start/end time, latency, token usage, estimated cost and status. It also records every step, including the tool arguments and results.
- **Evaluation**, stored with each run:
  - **Task success (rules):** each test case lists required tools and required phrases.
  - **Faithfulness (rules):** every number, price, date and tracking ID in the answer must appear in what the agent was given.
  - **Faithfulness (LLM-as-a-judge):** a second model scores groundedness from 1 to 5 and explains its score.
  - **Efficiency:** steps, tokens and latency against a per-test-case budget.
- **Regression testing:** run a 14-case dataset against v1 and v2, then compare task success, eval scores, latency, tokens and cost. You get alerts like *"Performance regression detected: task success decreased by 7.1 percentage points."* The comparison also lists every test case that went from pass to fail.
- **Dashboard pages:**
  - **Overview:** stat tiles, trend charts, the latest regression check, a "try the agent" form and recent runs.
  - **Run details:** a step-by-step timeline.
  - **Experiments** and **Compare**.
- **Docker:** a single `docker compose up` starts Postgres, the backend and the frontend.

## Tech stack

| Part | Choice | Why |
|---|---|---|
| LLM | Groq (`openai/gpt-oss-120b` and `openai/gpt-oss-20b`) | free tier, fast, supports tool calling, OpenAI-compatible API |
| Agent | a custom loop of about 60 lines | the loop is the thing being observed, so it shouldn't be hidden inside a framework |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2 | |
| Database | PostgreSQL (tests use SQLite) | |
| Frontend | Next.js 16, Tailwind CSS 4, Recharts | |
| Infra | Docker Compose | |

There's no Redis, queue or microservices. Experiments run one test case at a time, which is fast enough for 14 cases.

## Project structure

```
backend/
  llm.py                  the only file that talks to the LLM (with rate-limit retries)
  agent/                  support agent: loop, tools, v1/v2 configs, demo data
  tracing/                Tracer + pricing table
  database/               SQLAlchemy models, session, save_trace
  evaluators/             task_success, faithfulness (rules), llm_judge, efficiency
  services/               run pipeline, experiments, regression comparison
  routes/                 FastAPI endpoints
  datasets/support_v1.json  test cases
  scripts/                run_agent, run_experiment, compare (CLI)
  tests/                  19 tests, using a scripted fake LLM and SQLite
frontend/
  app/                    pages: /, /runs, /runs/[id], /experiments, /compare
  components/             tables, step timeline, charts, forms
  lib/                    API client, formatting helpers
docker-compose.yml
```

**Demo data vs real data:** `backend/agent/data/` (a fictional store's orders and help articles) and `backend/datasets/` (test cases) are sample inputs. Nothing in the database is seeded. Every run, score and chart comes from actually running the agent.

## How to run

### 1. Get a free Groq API key

Create a key at https://console.groq.com/keys, then:

```bash
cd backend
cp .env.example .env        # then put your key in LLM_API_KEY
```

### 2. Get a PostgreSQL database (pick one)

- **Neon (free, hosted, no local RAM):** create a project at https://neon.tech and paste its connection string into `DATABASE_URL` in `backend/.env`.
- **Docker, database only:** `docker compose up db`. The default `DATABASE_URL` already points at it.
- **Native install:** install PostgreSQL, then create user, password and database `agentlens`.

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest                             # 19 tests, no API key or database needed
uvicorn main:app --reload          # http://localhost:8000/docs
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev                        # http://localhost:3000
```

### Everything in Docker

```bash
docker compose up --build
```

On a machine with 8 GB of RAM, give WSL a memory cap first by putting `[wsl2]` and `memory=3GB` in `%UserProfile%\.wslconfig`. Close other heavy apps too.

## Example: one agent run

```bash
python -m scripts.run_agent "Where is my order 1042?"
python -m scripts.run_agent "Where is my order 1042?" --version v2 --save
```

This prints the trace: each step with its latency and tokens, the total cost, and the answer. `--save` also stores the run and evaluates it, so it shows up in the dashboard.

## Example: evaluation

Each test case in `datasets/support_v1.json` describes what a good run looks like:

```json
{
  "id": "return-order-1041",
  "input": "Can I return the headphones from order 1041?",
  "expected": {
    "must_call_tools": ["lookup_order", "search_knowledge_base"],
    "must_contain": ["15"],
    "must_contain_any": ["cannot", "can't", "unfortunately", "past", "expired"]
  }
}
```

The correct answer needs two tools. Order 1041 was delivered on Sept 8, and electronics have a 15-day return window, so on the store's date (Sept 25) it's too late. The rule checks confirm the agent looked up both facts. The faithfulness checks confirm it didn't invent any dates or numbers.

## Example: regression comparison

```bash
python -m scripts.run_experiment --version v1              # creates experiment #1
python -m scripts.run_experiment --version v2 --compare-to 1
```

The comparison prints both experiments' task success, eval score, average latency, tokens and cost per run. It then prints any alerts and the exact test cases that got worse, with run IDs to inspect. The same report is at `/compare?a=1&b=2` in the dashboard.

Groq's free tier allows about 8K tokens per minute, so a full experiment takes a few minutes. `llm.py` waits and retries on rate limits. That waiting time is **not** counted as latency.

## Screenshots

| Overview | Run details | Compare |
|---|---|---|
| ![overview](docs/screenshots/overview.png) | ![run](docs/screenshots/run-details.png) | ![compare](docs/screenshots/compare.png) |

*(Add your own screenshots to `docs/screenshots/`.)*

## Known limitations

- Rule-based faithfulness only checks numbers and IDs. It can't catch a wrong claim written in words.
- The LLM judge can be wrong. It's kept next to the rules, not instead of them.
- Cost is an estimate based on Groq's paid-tier prices in `tracing/pricing.py`. The free tier costs $0.
- Each version-and-dataset pair is run once. LLMs are non-deterministic, so a real regression test would run each case several times.
- Tables are created with `create_all`, and there are no migrations.

## Future improvements

- Run each test case N times and report variance, not a single pass/fail.
- Re-run the evaluators on stored runs after changing an evaluator.
- Alembic migrations.
- A tracing decorator or SDK so other agents can send traces to AgentLens over HTTP.
- Start experiments from the dashboard, with a background job.
- Compare the judge's scores with human labels to measure how reliable the judge is.

## What I learned

*(Rewrite this in your own words once you've built and run it. These are starting points.)*

- An agent is a loop around an LLM call. Tool calling is just the model returning JSON that asks us to run a function.
- Tracing is structured logging with a parent-child shape (run → steps). The hard parts are deciding what to capture and keeping it separate from storage.
- Wall-clock latency can lie: rate-limit waits made the model look slow until I timed only the successful request.
- Evaluation is layered. Cheap, strict rules catch clear failures. An LLM judge catches subtle ones but needs its own checks.
- Averages hide regressions. Comparing test case by test case shows fixes and breakages that cancel out in the average.
