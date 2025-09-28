# Laptop Intelligence Chat UI

A lightweight Next.js interface for chatting with the FastAPI-based Laptop Intelligence agent.

## Getting started

```bash
cp .env.local.example .env.local
# adjust NEXT_PUBLIC_BACKEND_URL if your backend is on a different host/port
npm install
npm run dev
```

Once the dev server is up, visit http://localhost:3000 and start chatting. The frontend forwards messages to the FastAPI `/chat` endpoint defined by `NEXT_PUBLIC_BACKEND_URL`.

## Features

- Polished assistant experience with suggestions, timestamps, and gradient styling
- User and session identifiers are configurable from the UI for quick testing
- Clear surface for backend errors and the active API endpoint
- No authentication required—ideal for demos or internal tooling

## Configuration

- `NEXT_PUBLIC_BACKEND_URL`: base URL of the FastAPI service (default `http://localhost:8000`).
- The UI expects the `/chat` endpoint to accept `query`, `user_id`, and `session_id` fields in the request body.

## Development notes

- If macOS blocks the native SWC binary, run the dev server with `NEXT_DISABLE_SWC_NATIVE_BUILD=1 npm run dev`.
- The layout uses inline styles for simplicity; swap in Tailwind or CSS modules if you prefer a different styling approach.
