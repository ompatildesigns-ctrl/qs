#!/bin/bash
# Auto-deployment script - runs without prompts

set -e

echo "🚀 Quantum Sprout - Automated Deployment"
echo "========================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm i -g @railway/cli
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm i -g vercel
fi

echo "✅ Prerequisites ready"
echo ""

# Check if logged into Railway
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "⚠️  Please login to Railway first:"
    echo "   railway login"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if logged into Vercel
echo "🔐 Checking Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    echo "⚠️  Please login to Vercel first:"
    echo "   vercel login"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo ""
echo "📦 Starting backend deployment..."
cd backend

# Initialize Railway project if needed
if [ ! -f ".railway/railway.toml" ]; then
    echo "📦 Initializing Railway project..."
    railway init --yes || railway link
fi

echo "🚀 Deploying backend..."
railway up --detach

# Get the deployment URL
echo "⏳ Waiting for deployment..."
sleep 5
BACKEND_URL=$(railway domain 2>/dev/null | head -1 || railway status | grep -o 'https://[^ ]*' | head -1)

if [ -z "$BACKEND_URL" ]; then
    echo "⚠️  Could not get backend URL automatically."
    echo "   Please get it from Railway dashboard and run:"
    echo "   ./scripts/setup-env.sh <your-backend-url>"
else
    echo "✅ Backend deployed at: $BACKEND_URL"
    echo ""
    echo "🔧 Setting up environment variables..."
    cd ..
    ./scripts/setup-env.sh "$BACKEND_URL"
fi

echo ""
echo "🌐 Frontend deployment requires manual step:"
echo "   cd frontend"
echo "   vercel --prod"
echo ""
echo "✅ Backend deployment complete!"
