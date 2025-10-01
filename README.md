# Laptop Intelligence Platform

Laptop Intelligence combines a FastAPI backend and a Next.js frontend to analyze laptop listings across marketplaces, summarize technical specifications, and power an AI-assisted chat experience.

## Features
- Aggregates canonical laptop specifications and enriches them with live Lenovo data via automated scraping.
- Stores normalized products in MongoDB and precomputes embeddings for semantic search.
- AI assistant built on Google ADK + LangChain that tracks session history, price ranges, and tooling context.
- Frontend chat client with persistent sessions, suggestion chips, and clear visibility into backend responses.

## Project Structure
- `BackEnd/app/` – FastAPI application, MongoDB session service, scraping utilities, and LLM orchestration.
- `FrontEnd/` – Next.js 14 application exposing the chat UI.
- `BackEnd/.env.example` – Template for required backend secrets (copy to `BackEnd/.env`).
- `FrontEnd/.env.local.example` – Template for frontend configuration.

## Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- MongoDB Atlas cluster (or compatible instance)
- OpenAI API key (for LangChain models)
- ChromeDriver-compatible browser for Selenium scraping

## Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd BackEnd
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r app/requirements.txt
   ```
3. Copy the environment template and provide your values:
   ```bash
   cp .env.example .env
   ```
   Required keys:
   - `OPENAI_API_KEY` – used by LangChain and LiteLLM.
   - `OPENAI_CHAT_MODEL` (optional) – defaults to `gpt-4.1-nano`.
   - `OPENAI_EMBEDDING_MODEL` (optional) – defaults to `text-embedding-3-small`.
   - `MONGODB_URL` – connection string for your MongoDB cluster.
   - `DB_NAME` – database where products and sessions are stored.
4. Start the API with uvicorn:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   On startup the service connects to MongoDB, seeds canonical PDF specs, and schedules a 12-hour refresh job.

## Frontend Setup
1. Navigate to the frontend folder:
   ```bash
   cd FrontEnd
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy the environment template and make adjustments:
   ```bash
   cp .env.local.example .env.local
   ```
   Set `NEXT_PUBLIC_BACKEND_URL` to the FastAPI base URL (default `http://localhost:8000`).
4. Run the development server:
   ```bash
   npm run dev
   ```
   The app listens on http://localhost:3000 and relays chat messages to `/chat` on the backend.

## Key Workflows
- **Product ingestion**: `initialize_canonical_data` downloads reference PDFs, scrapes live Lenovo data with Selenium, and writes enriched products with embeddings.
- **Chat**: POST `/chat` captures user queries, maintains session context in MongoDB, invokes the Google ADK agent, and returns the assistant's answer.
- **Search**: GET `/products` and `/search` expose filtered product data for dashboards or future UI integration.

## Testing & Tooling
- Backend tests: `cd BackEnd && pytest`
- Frontend linting: `cd FrontEnd && npm run lint`
- Selenium scraping depends on a ChromeDriver supplied by `webdriver-manager`; ensure Chrome is installed and accessible.

## Troubleshooting
- If the backend logs `OPENAI_API_KEY is not set`, verify `.env` is loaded or export the variable before running uvicorn.
- MongoDB connection issues typically stem from IP allowlisting or missing credentials—confirm the URL and database name in `.env`.
- For long-running scrapes, ensure the server has a display or configured driver for Selenium; headless Chrome is recommended in production.

## Future Enhancements
- Prompt caching layer to reduce latency and manage cost for repeated intents.
- Conversation history summarization so sessions stay within token limits while retaining context.
- Harden `/chat` and supporting APIs with authenticated headers or signed requests.
- Apply IAM-based role separation for agent runners and supporting services.
- Integrate Guardrails or similar content filters to keep responses on-policy.
- Automatic masking of PII before logging or storing conversation data.
- Move agent prompts and behaviors into database-managed configs so production changes do not require redeploys.

## License
Specify your preferred license here before distributing the project.
