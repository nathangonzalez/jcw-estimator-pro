# JCW Cost Estimator - Cloud Deployment Guide

## 🚀 Complete Web Application with ML Backend

This guide covers deploying the JCW Cost Estimator to various cloud platforms.

---

## Architecture Overview

```
┌─────────────────┐
│  React Frontend │  (Modern UI)
│   Port 3000     │
└────────┬────────┘
         │
         ↓ API Calls
┌─────────────────┐
│ FastAPI Backend │  (Python ML)
│   Port 8000     │
└────────┬────────┘
         │
         ↓ Predictions
┌─────────────────┐
│  ML Model (.pkl)│
│  Training Data  │
└─────────────────┘
```

---

## Quick Start (Local Development)

### 1. Backend Setup
```bash
cd jcw-estimator-pro

# Install dependencies
pip install -r requirements.txt

# Run backend
cd web/backend
python app.py

# Backend now running at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 2. Frontend Setup
```bash
cd web/frontend

# Install dependencies
npm install
# or
yarn install

# Create .env file
echo "REACT_APP_API_URL=http://localhost:8000" > .env

# Run frontend
npm start
# or
yarn start

# Frontend now running at http://localhost:3000
```

---

## Docker Deployment

### Build and Run
```bash
# Build Docker image
docker build -t jcw-cost-estimator .

# Run container
docker run -p 8000:8000 jcw-cost-estimator

# Access API at http://localhost:8000
```

### Docker Compose (Full Stack)
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - PYTHONUNBUFFERED=1
    
  frontend:
    image: node:18
    working_dir: /app
    volumes:
      - ./web/frontend:/app
    ports:
      - "3000:3000"
    command: sh -c "npm install && npm start"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
```

Run with:
```bash
docker-compose up
```

---

## Cloud Deployment Options

### Option 1: Google Cloud Run (Recommended - Easiest)

#### Deploy Backend
```bash
# 1. Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# 2. Login
gcloud auth login

# 3. Set project
gcloud config set project YOUR_PROJECT_ID

# 4. Build and deploy
gcloud run deploy jcw-estimator \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2

# Output will show your service URL:
# https://jcw-estimator-xxxxx-uc.a.run.app
```

#### Deploy Frontend
```bash
cd web/frontend

# 1. Build for production
REACT_APP_API_URL=https://jcw-estimator-xxxxx-uc.a.run.app npm run build

# 2. Deploy to Firebase Hosting (free)
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy

# Or deploy to Cloud Storage + Cloud CDN
gsutil mb gs://jcw-estimator-frontend
gsutil -m cp -r build/* gs://jcw-estimator-frontend
gsutil web set -m index.html gs://jcw-estimator-frontend
```

### Option 2: AWS (EC2 + S3)

#### Deploy Backend to EC2
```bash
# 1. Launch EC2 instance (Ubuntu 22.04, t3.medium)

# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update
sudo apt install python3-pip nginx -y
pip3 install -r requirements.txt

# 4. Run with systemd
sudo nano /etc/systemd/system/jcw-estimator.service
```

```ini
[Unit]
Description=JCW Cost Estimator API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/jcw-estimator-pro
ExecStart=/usr/local/bin/uvicorn web.backend.app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl start jcw-estimator
sudo systemctl enable jcw-estimator

# Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/jcw-estimator
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/jcw-estimator /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### Deploy Frontend to S3
```bash
# 1. Build
cd web/frontend
REACT_APP_API_URL=http://your-ec2-ip npm run build

# 2. Create S3 bucket
aws s3 mb s3://jcw-estimator-frontend

# 3. Enable static website hosting
aws s3 website s3://jcw-estimator-frontend \
  --index-document index.html \
  --error-document index.html

# 4. Upload files
aws s3 sync build/ s3://jcw-estimator-frontend --acl public-read

# 5. Access at:
# http://jcw-estimator-frontend.s3-website-us-east-1.amazonaws.com
```

### Option 3: Azure (App Service)

#### Deploy Backend
```bash
# 1. Install Azure CLI
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# 2. Login
az login

# 3. Create resource group
az group create --name jcw-estimator-rg --location eastus

# 4. Create App Service plan
az appservice plan create \
  --name jcw-estimator-plan \
  --resource-group jcw-estimator-rg \
  --sku B1 \
  --is-linux

# 5. Create web app
az webapp create \
  --resource-group jcw-estimator-rg \
  --plan jcw-estimator-plan \
  --name jcw-estimator-api \
  --runtime "PYTHON:3.11"

# 6. Deploy code
az webapp up \
  --name jcw-estimator-api \
  --resource-group jcw-estimator-rg
```

#### Deploy Frontend
```bash
# 1. Build
cd web/frontend
REACT_APP_API_URL=https://jcw-estimator-api.azurewebsites.net npm run build

# 2. Create static web app
az staticwebapp create \
  --name jcw-estimator-frontend \
  --resource-group jcw-estimator-rg \
  --source build/ \
  --location eastus
```

---

## Environment Variables

### Backend (.env)
```bash
# Production settings
ENVIRONMENT=production
DEBUG=false

# CORS origins (comma-separated)
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Optional: Database connection
# DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Frontend (.env.production)
```bash
REACT_APP_API_URL=https://your-backend-api.com
REACT_APP_ENVIRONMENT=production
```

---

## Production Checklist

### Security
- [ ] Enable HTTPS (Let's Encrypt or cloud provider SSL)
- [ ] Configure CORS with specific origins
- [ ] Add rate limiting
- [ ] Enable API authentication
- [ ] Set up monitoring and alerts

### Performance
- [ ] Enable caching (Redis recommended)
- [ ] Configure CDN for static assets
- [ ] Optimize Docker image size
- [ ] Set up auto-scaling
- [ ] Configure load balancer

### Data Persistence
- [ ] Configure volume mounts for ML models
- [ ] Set up automated backups
- [ ] Use managed database for training data
- [ ] Implement data migration strategy

### Monitoring
- [ ] Set up application logging
- [ ] Configure error tracking (Sentry)
- [ ] Add performance monitoring (New Relic/DataDog)
- [ ] Create health check endpoints
- [ ] Set up uptime monitoring

---

## Cost Estimates

### Google Cloud Run (Pay-per-use)
- **Free tier**: 2 million requests/month
- **Estimated**: $10-50/month for moderate usage
- **Scaling**: Automatic, 0-1000 instances

### AWS (EC2 + S3)
- **EC2 t3.medium**: ~$30/month
- **S3 hosting**: ~$1-5/month
- **Total**: ~$35-50/month

### Azure (App Service)
- **Basic B1**: ~$13/month
- **Static Web App**: Free tier available
- **Total**: ~$15-30/month

---

## Scaling Strategy

### Horizontal Scaling
```yaml
# Kubernetes deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jcw-estimator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jcw-estimator
  template:
    metadata:
      labels:
        app: jcw-estimator
    spec:
      containers:
      - name: api
        image: gcr.io/PROJECT/jcw-estimator:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

### Load Balancer
```nginx
# Nginx load balancer config
upstream jcw_backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://jcw_backend;
    }
}
```

---

## Continuous Deployment (CI/CD)

### GitHub Actions Example
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Cloud SDK
      uses: google-github-actions/setup-gcloud@v0
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}
    
    - name: Build and Deploy
      run: |
        gcloud run deploy jcw-estimator \
          --source . \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated
```

---

## Troubleshooting

### Backend not starting
```bash
# Check logs
docker logs container-name

# Or in cloud
gcloud run services logs read jcw-estimator --limit=50
```

### CORS errors
```python
# Update app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Model not found
```bash
# Ensure models directory is accessible
ls -la models/
# Should see: cost_estimator_ml.pkl
```

---

## Support & Maintenance

### Backup Strategy
```bash
# Backup training data and models daily
0 0 * * * cd /app && tar -czf backup-$(date +\%Y\%m\%d).tar.gz data/ models/
```

### Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and deploy
docker build -t jcw-estimator .
docker push gcr.io/PROJECT/jcw-estimator:latest
gcloud run services update jcw-estimator --image gcr.io/PROJECT/jcw-estimator:latest
```

---

## Next Steps

1. **Deploy to Cloud Run** (easiest, recommended for MVP)
2. **Add authentication** if restricting access
3. **Set up monitoring** with Google Cloud Monitoring or equivalent
4. **Configure custom domain** for professional appearance
5. **Enable HTTPS** (automatic with Cloud Run)
6. **Set up CI/CD** for automated deployments

**Your cost estimator is now production-ready! 🚀**
