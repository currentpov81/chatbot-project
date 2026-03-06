# AnonymChat — Telegram Anonymous Chat Bot

A high-performance Telegram anonymous chat bot designed to scale to 1M+ users.

## Stack

| Layer | Technology |
|---|---|
| Bot framework | aiogram 3 (async) |
| Database | PostgreSQL (asyncpg) |
| Cache / Queue | Redis |
| Hosting | Railway |
| Language | Python 3.12 |

## Architecture

```
Telegram API
    │
aiogram (polling / webhook)
    │
Handlers → Services
    │           │
PostgreSQL    Redis
(user data)  (matching queue + active chats)
```

**Redis keys:**
- `waiting_queue` — LIST of users waiting for a match (FIFO, O(1) pop)
- `active_chat:{uid}` — partner_id for active session (TTL 24h)
- `queue_joined:{uid}` — join timestamp for timeout cleanup (TTL 35s)

## Local Setup

### Prerequisites
- Python 3.12+
- PostgreSQL running locally
- Redis running locally

### Steps

```bash
# 1. Clone
git clone <your-repo>
cd chatbot-project

# 2. Create virtual env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your BOT_TOKEN, DATABASE_URL, REDIS_URL

# 5. Run
python main.py
```

### Local .env example
```
BOT_TOKEN=1234567890:ABCdef...
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/anonymchat
REDIS_URL=redis://localhost:6379
```

## Railway Deployment

1. Push to GitHub
2. Create new Railway project → Deploy from GitHub repo
3. Add **PostgreSQL** plugin
4. Add **Redis** plugin
5. Set environment variables:
   - `BOT_TOKEN` → your token
   - `DATABASE_URL` → from Railway PostgreSQL plugin (use `postgresql+asyncpg://...`)
   - `REDIS_URL` → from Railway Redis plugin
6. Deploy ✅

Railway will auto-detect the Dockerfile and build.

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Register & onboard |
| `/chat` | Find a random partner |
| `/next` | Skip to new partner |
| `/stop` | End current chat |
| `/profile` | View your profile |
| `/stats` | Live queue stats |
| `/help` | Show commands |

## Project Structure

```
chatbot-project/
├── main.py                     # Entry point
├── requirements.txt
├── Dockerfile
├── railway.toml
├── .env.example
└── app/
    ├── config.py               # Settings (pydantic)
    ├── handlers/
    │   ├── start.py            # /start command
    │   ├── onboarding.py       # FSM onboarding flow
    │   ├── chat.py             # Matching + relay + /next /stop
    │   └── commands.py         # /help /profile /stats
    ├── services/
    │   ├── matcher.py          # Redis matching logic (core)
    │   └── user_service.py     # User business logic
    ├── database/
    │   ├── models.py           # SQLAlchemy models
    │   ├── connection.py       # Async engine + session
    │   └── queries.py          # DB operations
    ├── cache/
    │   └── redis_client.py     # Shared Redis connection
    ├── keyboards/
    │   ├── onboarding_kb.py
    │   └── chat_kb.py
    ├── middlewares/
    │   └── auth.py             # Auto-register + ban check
    └── utils/
        └── states.py           # FSM states
```

## Scaling to 1M Users

The current architecture handles ~50k concurrent users on a single server.

To scale further:
1. Switch from polling to **webhook** (FastAPI)
2. Add a **load balancer** in front of multiple bot worker instances
3. Redis already supports all workers sharing state — no changes needed
4. PostgreSQL connection pooling via **PgBouncer**

## Planned Features (Premium)

- [ ] Gender filter
- [ ] Country filter  
- [ ] Priority matching queue
- [ ] Verified profile badge
- [ ] /next limit for free users

## Safety

- Auto-ban after 10 reports
- Report system with reason categorization
- Banned users blocked at middleware level
- No messages stored — relay only
