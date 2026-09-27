# Price Intelligence Dashboard

A Unified E-commerce Price Intelligence & Historical Price Dashboard. 

This application takes a natural-language product query, searches across multiple e-commerce platforms, normalizes products, extracts real-time prices, retrieves historical data (from external providers like Keepa or its own database), and renders a rich analytics dashboard. 

## Architecture

```text
Frontend (React/Vite)
   ↓
FastAPI Backend
   ↓
Search Provider (Serper / Demo)
   ↓
Product Resolution & Extraction (LLM + Adapters)
   ↓
Ecommerce Adapters (Amazon, Flipkart, Generic, etc.)
   ↓
Historical Providers (Keepa, Own Database, Demo)
   ↓
PostgreSQL / SQLite Database
   ↓
Analytics (Volatility, Averages, Consistency)
```

## Setup

1. **Install dependencies:**
   For Backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
   For Frontend:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure `.env` in `backend/.env`:**
   ```env
   # Example variables
   DATABASE_URL=sqlite+aiosqlite:///../data/pricetracker.db
   SEARCH_API_KEY=your_serper_key
   LLM_API_KEY=your_gemini_key
   KEEPA_API_KEY=your_keepa_key
   DEMO_MODE=false
   ```
   
   Similarly configure `frontend/.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

3. **Initialize the Database:**
   ```bash
   cd backend
   alembic upgrade head
   ```

## Running the Application

**Start Backend (FastAPI):**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend (React/Vite):**
```bash
cd frontend
npm run dev
```

## Demo Mode

If `DEMO_MODE=true` (or if `SERPER_API_KEY` and `GEMINI_API_KEY` are not provided), the backend will automatically fall back to using synthetic data. This ensures the dashboard UI and backend functionality can still be previewed seamlessly. Note that demo/synthetic data is clearly labeled in the frontend UI.

## Live Providers

In production mode (`DEMO_MODE=false`), the following APIs require keys:
- **Serper**: Used for candidate discovery (`SERPER_API_KEY`).
- **Gemini**: Used for query classification (`GEMINI_API_KEY`).
- **Keepa (Optional)**: Used to retrieve historical prices for Amazon products (`KEEPA_API_KEY`). If omitted, the application uses its own tracking database to build history natively over time.
