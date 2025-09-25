#!/bin/bash

# Railway Deployment Script for AI AdWords Platform

echo "🚀 Deploying AI AdWords Platform to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Railway CLI not found. Installing..."
    curl -fsSL https://railway.app/install.sh | sh
fi

# Login to Railway (if not already logged in)
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Initialize Railway project if needed
if [ ! -f .railway.json ]; then
    echo "🎯 Initializing Railway project..."
    railway init
fi

# Add PostgreSQL database if not already added
echo "🗄️ Setting up PostgreSQL database..."
railway add --database postgresql

# Deploy the application
echo "🚀 Deploying application..."
railway up --detach

# Set environment variables
echo "🔧 Configuring environment variables..."
railway variables set PYTHONUNBUFFERED=1
railway variables set PYTHONDONTWRITEBYTECODE=1
railway variables set LOG_LEVEL=info
railway variables set MOCK_REDDIT=true
railway variables set MOCK_TWITTER=true
railway variables set ENABLE_REAL_MUTATES=false

# Generate secure secret key
SECRET_KEY=$(openssl rand -base64 32)
railway variables set SECRET_KEY="$SECRET_KEY"

# Get deployment URL
echo "🌐 Getting deployment URL..."
DEPLOY_URL=$(railway status --json | jq -r '.deployments[0].url')

echo ""
echo "✅ Deployment Complete!"
echo "🌐 Your app is available at: $DEPLOY_URL"
echo "📊 Dashboard: $DEPLOY_URL/dashboard"
echo "📚 API Docs: $DEPLOY_URL/docs"
echo "🔍 Health Check: $DEPLOY_URL/health"
echo ""
echo "🎯 Next Steps:"
echo "1. Visit your app at the URL above"
echo "2. Add your Google Ads API credentials in Railway dashboard"
echo "3. Create an admin account via the signup page"
echo "4. Test the dashboard and agents"
echo ""
echo "⚙️ Railway Dashboard: https://railway.app/dashboard"
