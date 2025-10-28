#!/bin/bash
# JCW Cost Estimator - Google Cloud Run Deployment Script

echo "🚀 JCW Cost Estimator - Deploying to Google Cloud Run"
echo "=================================================="

# Check if user is logged in
echo ""
echo "Step 1: Checking authentication..."
gcloud auth list

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo ""
    echo "⚠️  No project set. Please set your GCP project:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo ""
echo "📋 Deploying to project: $PROJECT_ID"
echo ""

# Enable required APIs
echo "Step 2: Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

echo ""
echo "Step 3: Deploying to Cloud Run..."
echo ""

# Deploy to Cloud Run
gcloud run deploy jcw-cost-estimator \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8000

echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""
echo "Your API is now live! 🎉"
echo ""
echo "📝 Next steps:"
echo "   1. Copy the service URL from above"
echo "   2. Test the API: curl [SERVICE_URL]/health"
echo "   3. View API docs: [SERVICE_URL]/docs"
echo ""
echo "💰 Cost estimate: ~$10-50/month for moderate usage"
echo "   (2 million requests/month free tier)"
echo ""
