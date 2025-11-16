#!/bin/bash
# Backend deployment script - run after Railway login
# This will deploy the backend once you're authenticated

set -e

echo "🚂 Quantum Sprout Backend Deployment"
echo "===================================="
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged into Railway"
    echo ""
    echo "Please login first:"
    echo "   railway login"
    echo ""
    echo "This will open your browser for authentication."
    echo "After login, run this script again."
    exit 1
fi

echo "✅ Logged into Railway"
RAILWAY_USER=$(railway whoami 2>/dev/null | head -1 || echo "Unknown")
echo "   User: $RAILWAY_USER"
echo ""

cd "$(dirname "$0")/backend"

# Check if already initialized
if [ -f ".railway/railway.toml" ]; then
    echo "📦 Railway project already initialized"
    echo ""
else
    echo "📦 Initializing Railway project..."
    railway init --yes || railway link
    echo ""
fi

echo "🚀 Deploying backend..."
railway up --detach || railway deploy

echo ""
echo "⏳ Waiting for deployment..."
sleep 15

echo ""
echo "📋 Getting deployment information..."

# Try to get the URL
BACKEND_URL=$(railway domain 2>/dev/null | head -1 || railway status 2>/dev/null | grep -o 'https://[^ ]*' | head -1 || echo "")

if [ ! -z "$BACKEND_URL" ]; then
    echo ""
    echo "✅ Backend deployed successfully!"
    echo ""
    echo "🌐 Backend URL: $BACKEND_URL"
    echo ""
    echo "🔧 Next steps:"
    echo ""
    echo "1. Set environment variables:"
    echo "   cd .."
    echo "   ./scripts/setup-env.sh \"$BACKEND_URL\""
    echo ""
    echo "2. Or set manually in Railway dashboard:"
    echo "   - Go to Railway project → Variables tab"
    echo "   - Add all variables from secrets.txt"
    echo "   - Update JIRA_REDIRECT_URI to: $BACKEND_URL/api/auth/jira/callback"
    echo ""
    echo "3. Update frontend environment variable:"
    echo "   cd frontend"
    echo "   vercel env add REACT_APP_BACKEND_URL production"
    echo "   Enter: $BACKEND_URL"
    echo ""
    echo "4. Update OAuth callback in Atlassian Console:"
    echo "   $BACKEND_URL/api/auth/jira/callback"
    echo ""
else
    echo ""
    echo "⚠️  Could not automatically get backend URL"
    echo "   Check Railway dashboard for your deployment URL"
    echo "   Then run: cd .. && ./scripts/setup-env.sh <your-backend-url>"
fi

echo ""
echo "✅ Deployment complete!"
echo ""

