# FHIR ISO-TS-22220-2011 — ITADP Identity Management

Monorepo for the FHIR-to-ISO identity converter dashboard.

## Structure

```
fhir-iso-monorepo/
├── backend/        # FastAPI — deployed on Render
├── frontend/       # React + Vite — deployed on Render (static site)
└── README.md
```

## Live URLs

| Service  | URL |
|----------|-----|
| Backend API | https://iso-ts-22220-2011.onrender.com |
| Frontend | https://iso-ts-22220-2011.onrender.com (static) |

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deploy on Render

### Backend (Web Service)
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend (Static Site)
- **Root Directory:** `frontend`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `frontend/dist`
