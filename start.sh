#!/usr/bin/env bash
set -e
trap 'kill 0' EXIT INT TERM

cd "$(dirname "$0")"

if [ ! -d backend/.venv ]; then
  echo "[setup] creating venv + installing backend"
  (cd backend && python3 -m venv .venv && .venv/bin/pip install -e .)
fi

if [ ! -f backend/.env ]; then
  echo "[setup] copying backend/.env.example -> backend/.env"
  cp backend/.env.example backend/.env
fi

if [ ! -f backend/data/carbonlens.db ]; then
  echo "[setup] seeding database"
  (cd backend && .venv/bin/python -m app.seed)
fi

if [ ! -d frontend/node_modules ]; then
  echo "[setup] installing frontend"
  (cd frontend && npm install)
fi

echo "[run] backend  -> http://localhost:8000/docs"
echo "[run] frontend -> http://localhost:5173"

(cd backend && .venv/bin/uvicorn app.main:app --port 8000) &
(cd frontend && npm run dev) &

(
  until curl -sf http://localhost:8000/health >/dev/null; do sleep 0.5; done
  until curl -sf http://localhost:5173 >/dev/null; do sleep 0.5; done
  echo "[run] opening browser tabs"
  xdg-open http://localhost:5173 >/dev/null 2>&1 || true
  xdg-open http://localhost:8000/docs >/dev/null 2>&1 || true
) &

wait
