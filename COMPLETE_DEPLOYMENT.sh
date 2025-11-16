#!/bin/bash
# Complete deployment script - runs after Railway login
# This automates the entire deployment process

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     QUANTUM SPROUT - COMPLETE DEPLOYMENT                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check Railway auth
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged into Railway"
    echo ""
    echo "Please login first:"
    echo "   railway login"
    echo ""
    exit 1
fi

echo "✅ Railway authenticated"
RAILWAY_USER=$(railway whoami | head -1)
echo "   User: $RAILWAY_USER"
echo ""

# Step 1: Deploy Backend
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Deploying Backend to Railway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd backend

# Check if already initialized
if [ -f ".railway/railway.toml" ]; then
    echo "📦 Railway project already initialized"
else
    echo "📦 Initializing Railway project..."
    # Use link instead of init if possible (non-interactive)
    railway link 2>/dev/null || {
        echo "⚠️  Could not auto-link, you may need to:"
        echo "   1. Go to Railway dashboard and create a project"
        echo "   2. Run: railway link"
        echo "   Or run: railway init (in interactive terminal)"
        exit 1
    }
fi

echo "🚀 Deploying backend..."
railway up --detach || railway deploy

echo "⏳ Waiting for deployment to complete..."
sleep 25

# Try multiple methods to get the URL
echo "📋 Getting deployment URL..."
BACKEND_URL=$(railway domain 2>/dev/null | head -1)

if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL=$(railway status 2>/dev/null | grep -o 'https://[^ ]*\.up\.railway\.app' | head -1)
fi

if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL=$(railway status 2>/dev/null | grep -o 'https://[^ ]*' | head -1)
fi

cd ..

if [ -z "$BACKEND_URL" ]; then
    echo "⚠️  Could not automatically get backend URL"
    echo "   Check Railway dashboard for your deployment URL"
    echo "   It will be something like: https://xxx.up.railway.app"
    echo ""
    echo "   Then run:"
    echo "   ./scripts/setup-env.sh <your-backend-url>"
    exit 1
fi

echo "✅ Backend deployed!"
echo "   URL: $BACKEND_URL"
echo ""

# Step 2: Set Environment Variables
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Setting Environment Variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "scripts/setup-env.sh" ]; then
    echo "🔧 Setting environment variables..."
    ./scripts/setup-env.sh "$BACKEND_URL" || echo "⚠️  Some env vars may need manual setup in Railway dashboard"
else
    echo "⚠️  setup-env.sh not found, set env vars manually in Railway dashboard"
fi

echo ""

# Step 3: Summary
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT COMPLETE                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Backend deployed: $BACKEND_URL"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Verify environment variables in Railway dashboard:"
echo "   - Go to Railway project → Variables tab"
echo "   - Ensure all variables are set (see secrets.txt)"
echo "   - Update JIRA_REDIRECT_URI: $BACKEND_URL/api/auth/jira/callback"
echo ""
echo "2. Update frontend environment variable:"
echo "   cd frontend"
echo "   vercel env add REACT_APP_BACKEND_URL production"
echo "   Enter: $BACKEND_URL"
echo ""
echo "3. Update OAuth callback in Atlassian Console:"
echo "   URL: $BACKEND_URL/api/auth/jira/callback"
echo "   Go to: https://developer.atlassian.com/console/myapps/"
echo ""
echo "4. Test backend:"
echo "   curl $BACKEND_URL/api/health"
echo ""
echo "✅ Deployment process complete!"
