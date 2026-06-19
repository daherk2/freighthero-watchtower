# Railway Deployment Guide

## 🚀 Deploy on Railway

This guide will help you deploy FreightHero Watchtower to Railway.

## Prerequisites

- Railway account (https://railway.app)
- GitHub account
- Project pushed to GitHub

## Step 1: Prepare Your Repository

### 1.1 Update GitHub Token (IMPORTANT)

⚠️ **Security Warning:** The GitHub token you shared earlier should be revoked immediately!

1. Go to https://github.com/settings/tokens
2. Revoke the compromised token
3. Create a new token with these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)

### 1.2 Initialize Git Repository

```bash
cd /home/ubuntu/FreightHero

# Initialize git if not already done
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: FreightHero Watchtower v0.1.0"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/freighthero-watchtower.git

# Push to GitHub
git push -u origin main
```

## Step 2: Deploy Backend to Railway

### 2.1 Create New Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository: `freighthero-watchtower`

### 2.2 Configure Backend Service

1. Click "New" → "Empty Service"
2. Name it: `freighthero-backend`
3. Go to Settings tab
4. Set Root Directory: (leave empty for root)
5. Set Dockerfile: `Dockerfile.railway`

### 2.3 Add PostgreSQL with PGVector

1. Click "New" → "Database" → "PostgreSQL"
2. Name it: `freighthero-db`
3. **Important:** Railway PostgreSQL should have PGVector extension
4. Go to the database service settings
5. Copy the `DATABASE_URL` connection string

### 2.4 Add Redis

1. Click "New" → "Database" → "Redis"
2. Name it: `freighthero-redis`
3. Copy the `REDIS_URL` connection string

### 2.5 Configure Environment Variables

In the backend service, add these variables:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@host:5432/freighthero
REDIS_URL=redis://host:6379/0
CELERY_BROKER_URL=redis://host:6379/1
CELERY_RESULT_BACKEND=redis://host:6379/2
OPENAI_API_KEY=your-openrouter-api-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=z-ai/glm-5
DEBUG=false
LOG_LEVEL=INFO
```

### 2.6 Deploy Backend

1. Go to Deployments tab
2. Click "Deploy"
3. Wait for deployment to complete (~3-5 minutes)
4. Check health: `https://your-backend.railway.app/health`

## Step 3: Deploy Frontend to Railway

### 3.1 Configure Frontend Service

1. Click "New" → "Empty Service"
2. Name it: `freighthero-frontend`
3. Go to Settings tab
4. Set Root Directory: `console`
5. Set Dockerfile: `Dockerfile.frontend`

### 3.2 Configure Environment Variables

In the frontend service, add:

```bash
VITE_API_URL=https://your-backend.railway.app
```

### 3.3 Deploy Frontend

1. Go to Deployments tab
2. Click "Deploy"
3. Wait for deployment to complete (~2-3 minutes)
4. Access: `https://your-frontend.railway.app`

## Step 4: Configure CORS

Update backend environment variables to allow frontend domain:

```bash
ALLOWED_ORIGINS=https://your-frontend.railway.app
```

Update `src/interfaces/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 5: Run Database Migrations

Railway will automatically run migrations on startup, but you can also run manually:

```bash
# In Railway, open a shell for the backend service
railway run bash

# Run migrations
python -m alembic upgrade head
```

## Step 6: Verify Deployment

### Backend Checks

```bash
# Health check
curl https://your-backend.railway.app/health

# List loads
curl https://your-backend.railway.app/api/v1/loads/

# Dashboard stats
curl https://your-backend.railway.app/api/v1/monitoring/dashboard
```

### Frontend Checks

1. Open `https://your-frontend.railway.app`
2. Verify dashboard loads
3. Check browser console for errors
4. Test creating a new load
5. Test simulation page

## Troubleshooting

### Backend Won't Start

1. Check logs in Railway dashboard
2. Verify DATABASE_URL is correct
3. Ensure PGVector extension is available
4. Check environment variables are set

### Frontend Shows API Errors

1. Verify VITE_API_URL is set correctly
2. Check CORS configuration in backend
3. Ensure backend is healthy
4. Check network tab in browser dev tools

### Database Errors

1. Verify PostgreSQL has PGVector extension
2. Check connection string format
3. Ensure database user has correct permissions
4. Run migrations manually

## Cost Estimation

Railway pricing (as of 2024):

- **Backend:** ~$5-10/month (512MB RAM)
- **Frontend:** ~$5/month (static site)
- **PostgreSQL:** ~$5-10/month (500MB)
- **Redis:** ~$5/month
- **Total:** ~$20-30/month

## Monitoring

Railway provides:

- Real-time logs
- Resource usage metrics
- Deployment history
- Health checks
- Automatic restarts

## Next Steps

1. Set up custom domain (optional)
2. Configure CI/CD with GitHub Actions
3. Set up monitoring alerts
4. Enable automatic deployments on push
5. Configure backup strategy for database

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: https://github.com/YOUR_USERNAME/freighthero-watchtower/issues

---

**Last Updated:** 2026-06-12
**Version:** 0.1.0
