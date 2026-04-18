# CarbonLens — Backend

FastAPI + SQLAlchemy 2.0 + SQLite + Alembic.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
```

## Seed the demo database

```bash
python -m app.seed
```

Creates `data/carbonlens.db` with Greenfield Manufacturing Pvt. Ltd.,
3 facilities, 15 suppliers, 50 emission factors, and 24 months of
activity data (Jan 2024 – Dec 2025) including four intentional anomalies
for the AI anomaly-detector demo:

1. Pune electricity 3x normal in Jul 2024 (data entry error)
2. Pune DG diesel spike in Sep 2024
3. Mumbai office electricity missing for Nov–Dec 2024
4. (Supplier zero-emissions anomaly added when supplier submissions seed)

## Run the API

```bash
uvicorn app.main:app --reload
```

- http://localhost:8000/health
- http://localhost:8000/api/v1/emission-factors
- http://localhost:8000/docs — OpenAPI

## Alembic

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

The seed script calls `Base.metadata.create_all()` for dev convenience.
For production, use Alembic exclusively.
