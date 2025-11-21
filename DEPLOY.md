# Vercel Deployment Guide

This guide explains how to deploy `polyseek_sentient` to Vercel.

## Prerequisites

- [Vercel account](https://vercel.com/signup)
- [GitHub account](https://github.com) (recommended)
- Project committed to a Git repository

## Deployment Steps

### 1. Push to GitHub Repository

```bash
# Initialize repository (if not already done)
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository and push
git remote add origin https://github.com/your-username/polyseek_sentient.git
git push -u origin main
```

### 2. Import Project to Vercel

1. Access [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Select GitHub repository
4. Import project

### 3. Configure Environment Variables

Set the following environment variables in Vercel dashboard:

#### Required Environment Variables

```
GOOGLE_API_KEY=your-google-api-key
# or
OPENAI_API_KEY=your-openai-api-key
# or
OPENROUTER_API_KEY=your-openrouter-api-key
```

#### Optional Environment Variables

```
NEWS_API_KEY=your-news-api-key
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
X_BEARER_TOKEN=your-x-bearer-token
LITELLM_MODEL_ID=gemini/gemini-2.0-flash-001
```

### 4. Verify Build Settings

Vercel automatically detects the following:
- **Root Directory**: Project root
- **Framework Preset**: Other
- **Build Command**: None (auto-detected)
- **Output Directory**: Auto-detected

### 5. Deploy

1. Click "Deploy" button
2. Wait for build to complete (usually 1-3 minutes)
3. URL will be displayed when deployment completes

## Configuration Files

### `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/assets/(.*)",
      "dest": "/frontend/assets/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "env": {
    "PYTHONPATH": "src"
  }
}
```

- `/api/*` requests are routed to Python API
- Other requests are routed to static files (frontend)
- `PYTHONPATH` is set to enable Python module imports

### `api/index.py`

Entry point for Vercel. Imports the FastAPI app.

## Troubleshooting

### Build Errors

1. **Python Path Issues**
   - Verify `PYTHONPATH=src` is set in environment variables
   - Check `env` section in `vercel.json`

2. **Dependency Installation Errors**
   - Verify `requirements.txt` is correctly placed
   - Check Python version (Vercel supports Python 3.9+)

3. **Module Import Errors**
   - Verify `src/polyseek_sentient/` directory structure
   - Check import path in `api/index.py`

### Runtime Errors

1. **Environment Variables Not Set**
   - Check environment variables in Vercel dashboard
   - Verify they are set for Production environment

2. **API Endpoint Not Found**
   - Verify `API_BASE_URL` in frontend is correctly configured
   - Check Vercel routing configuration

### Debugging Methods

1. **Check Vercel Logs**
   - Vercel Dashboard → Project → "Logs" tab
   - Check build logs and runtime logs

2. **Test Locally**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Run locally
   vercel dev
   ```

## Custom Domain Setup

1. Vercel Dashboard → Project → "Settings" → "Domains"
2. Add domain
3. Update DNS settings

## Continuous Deployment

Pushing to GitHub repository automatically triggers deployment:
- Push to `main` branch → Deploy to production
- Other branches → Preview deployment

## Reference Links

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/runtimes/python)
- [FastAPI on Vercel](https://vercel.com/guides/deploying-fastapi-with-vercel)
