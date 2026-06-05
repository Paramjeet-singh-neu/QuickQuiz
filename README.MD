# QuickQuiz: Ludwitt-Ready Educational Content System

QuickQuiz converts PDF lectures into interactive quizzes with AI-powered analysis, Ludwitt OAuth login, paid-credit AI billing, and hosted quiz history storage.

## Features

- PDF processing with vector retrieval and deterministic quiz generation
- Ludwitt OAuth login and secure server-side token handling
- AI analysis billed through Ludwitt credits (`/api/v1/ai/messages`)
- Hosted-data persistence for quiz history (`quiz_runs` collection)
- Offline mode with zero AI cost
- Legacy CLI and Streamlit entry points for local development

## Architecture

- `backend/` — FastAPI API for OAuth, credits, quiz generation, hosted storage
- `frontend/` — React/Vite marketplace-style web app
- `ecs/` — existing multi-agent PDF/quiz pipeline
- `main.py` — CLI
- `streamlit_app.py` — legacy prototype UI

## Ludwitt Registration

Register a hosted-data app at:

`https://pitchrise.ludwitt.com/learning-engineers/apps/new`

Recommended settings:

- Tier: **Hosted-data**
- Scopes: `profile credits:read credits:spend data:read data:write`
- Redirect URI (local): `http://localhost:8000/auth/callback`
- Hosted-data collection: `quiz_runs`
- Indexed fields: `createdAt`, `sourceName`

Docs:

- [Quickstart](https://pitchrise.ludwitt.com/docs/le/quickstart.md)
- [OAuth](https://pitchrise.ludwitt.com/docs/le/oauth.md)
- [Credits / AI](https://pitchrise.ludwitt.com/docs/le/credits.md)
- [Hosted Data](https://pitchrise.ludwitt.com/docs/le/data-api.md)

## Local Setup

### 1. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in:

- `LUDWITT_CLIENT_ID`
- `LUDWITT_CLIENT_SECRET`
- `SESSION_SECRET`

Run API:

```bash
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### 3. Legacy CLI / Streamlit

CLI:

```bash
python main.py --pdf path/to/lecture.pdf --n 10 --offline
```

Streamlit:

```bash
streamlit run streamlit_app.py
```

Legacy online mode still uses `OPENAI_API_KEY`. The Ludwitt web app uses Ludwitt credits instead.

## API Endpoints

- `GET /health`
- `GET /auth/login`
- `GET /auth/callback`
- `GET /auth/me`
- `POST /auth/logout`
- `GET /api/credits/balance`
- `GET /api/storage/usage`
- `GET /api/quizzes/history`
- `POST /api/quizzes/generate`

## Testing

```bash
pytest -q
```

## Deployment Notes

- Set `COOKIE_SECURE=true` in production
- Set `FRONTEND_URL` to your deployed frontend origin
- Register the production OAuth callback on Ludwitt
- Keep `client_secret` server-side only

## Authors

Paramjeet Singh  
Northeastern University
