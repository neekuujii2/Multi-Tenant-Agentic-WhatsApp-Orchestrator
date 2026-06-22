# Deployment Guide

This repo is split into:

- `frontend`: Vite + React dashboard
- `backend`: FastAPI service for webhooks, dashboard APIs, and SSE

## Recommended Docker approach

Use **multi-stage Dockerfiles with a hardened runtime**.

- For minimum final image size, multi-stage builds are the right base choice.
- For lower vulnerability exposure, the runtime stage should be slim, contain only production artifacts, and run as a non-root user.
- In this repo, both Dockerfiles follow that pattern.

Short answer: do **not** choose between "multi-stage" and "hardened" as if they are separate options. The best setup is **multi-stage plus hardened runtime**.

## 1. Pre-deploy checklist

Before deploying anywhere, verify these locally:

1. Backend config values are ready.
2. MongoDB and Redis are available.
3. The frontend points to the deployed backend URL.
4. Meta WhatsApp webhook settings will use your deployed backend `/webhook` URL.

Backend environment variables:

- `META_VERIFY_TOKEN`
- `META_APP_SECRET`
- `ANTHROPIC_API_KEY`
- `MONGODB_URI`
- `REDIS_URL`
- `LOG_LEVEL`
- `ENVIRONMENT`
- `CORS_ORIGINS`

Frontend environment variable:

- `VITE_API_URL`

Local verification commands:

```bash
cd frontend && npm run lint && npm run build
cd backend && python -m compileall app
```

## 2. Deploy backend on Render

Render is a good first hosted target for the FastAPI backend.

### Create the backend service

1. Push this repo to GitHub.
2. In Render, create a new `Web Service`.
3. Connect the repo.
4. Set:

```text
Root Directory: backend
Environment: Docker
```

Render will detect `backend/Dockerfile`.

### Add backend environment variables

Add these in Render:

```text
META_VERIFY_TOKEN=...
META_APP_SECRET=...
ANTHROPIC_API_KEY=...
MONGODB_URI=...
REDIS_URL=...
LOG_LEVEL=INFO
ENVIRONMENT=production
CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]
```

### Health check

Use:

```text
/health
```

### After deploy

Confirm these URLs work:

- `https://your-render-service.onrender.com/health`
- `https://your-render-service.onrender.com/dashboard/tenants`

Then configure the Meta webhook URL:

```text
https://your-render-service.onrender.com/webhook
```

## 3. Deploy frontend on Vercel

Vercel is the best fit for this `frontend` app because it is a static Vite build.

### Create the frontend project

1. In Vercel, import the same GitHub repo.
2. Set:

```text
Root Directory: frontend
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
```

### Add frontend environment variable

Point the UI to the Render backend:

```text
VITE_API_URL=https://your-render-service.onrender.com
```

### Important CORS update

After Vercel gives you the production URL, update Render:

```text
CORS_ORIGINS=["https://your-project.vercel.app"]
```

If you use a custom frontend domain, include that instead.

## 4. Validate the hosted stack

After Render and Vercel are both live, verify:

1. Frontend loads without console API errors.
2. Tenant list loads from the backend.
3. Session list loads for a tenant.
4. Analytics tab loads.
5. Campaign broadcast request reaches the backend.
6. SSE works from `/dashboard/tenants/{tenant_id}/events`.
7. Meta webhook verification succeeds.

## 5. Deploy on GCP after everything is stable

Once Render and Vercel are confirmed working, move to GCP for a more consolidated setup.

### Recommended GCP target

Use **Cloud Run** for both services.

- It works well with these Dockerfiles.
- It gives HTTPS, revisions, and simple rollout control.
- It is a good fit for a FastAPI API and a static frontend container.

### Build and push images

Set your values first:

```bash
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID
gcloud auth configure-docker
```

Build backend:

```bash
docker build -t gcr.io/YOUR_GCP_PROJECT_ID/whatsapp-backend:latest ./backend
docker push gcr.io/YOUR_GCP_PROJECT_ID/whatsapp-backend:latest
```

Build frontend:

```bash
docker build \
  --build-arg VITE_API_URL=https://YOUR_BACKEND_CLOUD_RUN_URL \
  -t gcr.io/YOUR_GCP_PROJECT_ID/whatsapp-frontend:latest \
  ./frontend
docker push gcr.io/YOUR_GCP_PROJECT_ID/whatsapp-frontend:latest
```

### Deploy backend to Cloud Run

```bash
gcloud run deploy whatsapp-backend \
  --image gcr.io/YOUR_GCP_PROJECT_ID/whatsapp-backend:latest \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO \
  --set-env-vars META_VERIFY_TOKEN=YOUR_VALUE \
  --set-env-vars META_APP_SECRET=YOUR_VALUE \
  --set-env-vars ANTHROPIC_API_KEY=YOUR_VALUE \
  --set-env-vars MONGODB_URI=YOUR_VALUE \
  --set-env-vars REDIS_URL=YOUR_VALUE \
  --set-env-vars CORS_ORIGINS='["https://YOUR_FRONTEND_CLOUD_RUN_URL"]'
```

### Deploy frontend to Cloud Run

```bash
gcloud run deploy whatsapp-frontend \
  --image gcr.io/YOUR_GCP_PROJECT_ID/whatsapp-frontend:latest \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8080
```

### Final GCP checks

Validate:

- Frontend URL loads
- Frontend can call backend
- Backend `/health` works
- CORS allows the frontend origin
- Meta webhook now points to the GCP backend URL

## 6. Notes

- Vercel is ideal for the frontend.
- Render is simpler for the first backend deployment.
- GCP Cloud Run is the clean next step after both pieces are proven.
- The frontend Docker image is only needed for container-based hosting like Cloud Run; for Vercel, it is not used.
