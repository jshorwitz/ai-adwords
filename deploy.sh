#!/bin/bash

# Deploy AI AdWords Dashboard to Railway
echo "🚀 Deploying Synter AI AdWords Dashboard to Railway..."

# Ensure we're on the main branch and up to date
echo "📡 Pushing latest changes to GitHub..."
git add . && git commit -m "Deploy: BigQuery-integrated dashboard" --allow-empty
git push origin main

echo "✅ Code pushed to GitHub!"
echo "🌐 Railway will auto-deploy from: https://github.com/jshorwitz/ai-adwords"
echo "🎯 Dashboard URL: https://web-production-97620.up.railway.app"

echo ""
echo "🔧 Next steps:"
echo "1. Set BigQuery environment variables in Railway dashboard:"
echo "   - GOOGLE_CLOUD_PROJECT"
echo "   - BIGQUERY_DATASET_ID=google_ads_data"
echo "   - Upload service account JSON as GOOGLE_APPLICATION_CREDENTIALS"
echo ""
echo "2. Monitor deployment logs at:"
echo "   https://railway.app/project/astonishing-reflection"
