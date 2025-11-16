#!/bin/bash
# Quantum Sprout - Full Deployment Execution Script
# This script executes the complete deployment process

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  QUANTUM SPROUT - AUTOMATED DEPLOYMENT EXECUTION             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Verify prerequisites
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Verifying Prerequisites"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Railway CLI
if command -v railway &> /dev/null; then
    echo -e "${GREEN}✅ Railway CLI installed${NC}"
    RAILWAY_VERSION=$(railway --version)
    echo "   Version: $RAILWAY_VERSION"
else
    echo -e "${YELLOW}📦 Installing Railway CLI...${NC}"
    npm i -g @railway/cli
    echo -e "${GREEN}✅ Railway CLI installed${NC}"
fi

# Check Vercel CLI
if command -v vercel &> /dev/null; then
    echo -e "${GREEN}✅ Vercel CLI installed${NC}"
else
    echo -e "${YELLOW}📦 Installing Vercel CLI...${NC}"
    npm i -g vercel
    echo -e "${GREEN}✅ Vercel CLI installed${NC}"
fi

# Check Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python 3 available${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

echo ""

# Step 2: Verify secrets
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Verifying Secrets"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "secrets.txt" ]; then
    echo -e "${GREEN}✅ Secrets file found${NC}"
    JWT_SECRET=$(grep JWT_SECRET_KEY secrets.txt | cut -d'=' -f2)
    ENC_KEY=$(grep JIRA_ENC_KEY secrets.txt | cut -d'=' -f2)
    echo "   JWT_SECRET_KEY: ${JWT_SECRET:0:20}..."
    echo "   JIRA_ENC_KEY: ${ENC_KEY:0:20}..."
else
    echo -e "${YELLOW}⚠️  Generating secrets...${NC}"
    python3 scripts/generate-secrets-simple.py --save
    echo -e "${GREEN}✅ Secrets generated${NC}"
fi

echo ""

# Step 3: Check authentication
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Checking Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

RAILWAY_LOGGED_IN=false
VERCEL_LOGGED_IN=false

if railway whoami &> /dev/null; then
    echo -e "${GREEN}✅ Logged into Railway${NC}"
    RAILWAY_USER=$(railway whoami 2>/dev/null | head -1 || echo "Unknown")
    echo "   User: $RAILWAY_USER"
    RAILWAY_LOGGED_IN=true
else
    echo -e "${YELLOW}⚠️  Not logged into Railway${NC}"
    echo "   Run: railway login"
fi

if vercel whoami &> /dev/null; then
    echo -e "${GREEN}✅ Logged into Vercel${NC}"
    VERCEL_USER=$(vercel whoami 2>/dev/null | head -1 || echo "Unknown")
    echo "   User: $VERCEL_USER"
    VERCEL_LOGGED_IN=true
else
    echo -e "${YELLOW}⚠️  Not logged into Vercel${NC}"
    echo "   Run: vercel login"
fi

echo ""

# Step 4: Deploy Backend (if logged in)
if [ "$RAILWAY_LOGGED_IN" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 4: Deploying Backend to Railway"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    cd backend
    
    # Initialize Railway project if needed
    if [ ! -f ".railway/railway.toml" ]; then
        echo "📦 Initializing Railway project..."
        railway init --yes 2>/dev/null || railway link
    fi
    
    echo "🚀 Deploying backend..."
    railway up --detach || railway deploy
    
    echo "⏳ Waiting for deployment to complete..."
    sleep 10
    
    # Try to get the URL
    BACKEND_URL=$(railway domain 2>/dev/null | head -1 || railway status 2>/dev/null | grep -o 'https://[^ ]*' | head -1 || echo "")
    
    if [ -z "$BACKEND_URL" ]; then
        echo -e "${YELLOW}⚠️  Could not automatically get backend URL${NC}"
        echo "   Check Railway dashboard for your deployment URL"
        echo "   Then run: cd .. && ./scripts/setup-env.sh <your-backend-url>"
    else
        echo -e "${GREEN}✅ Backend deployed!${NC}"
        echo "   URL: $BACKEND_URL"
        echo ""
        echo "🔧 Setting up environment variables..."
        cd ..
        ./scripts/setup-env.sh "$BACKEND_URL" || echo "⚠️  Could not set env vars automatically"
    fi
    
    cd ..
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 4: Backend Deployment (Manual)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "To deploy backend:"
    echo "1. railway login"
    echo "2. cd backend"
    echo "3. railway init"
    echo "4. railway up"
    echo ""
fi

echo ""

# Step 5: Deploy Frontend (if logged in)
if [ "$VERCEL_LOGGED_IN" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 5: Deploying Frontend to Vercel"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [ -d "frontend" ]; then
        cd frontend
        echo "🚀 Deploying frontend..."
        vercel --prod --yes || vercel deploy --prod
        cd ..
        echo -e "${GREEN}✅ Frontend deployment initiated!${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend directory not found${NC}"
    fi
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 5: Frontend Deployment (Manual)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "To deploy frontend:"
    echo "1. vercel login"
    echo "2. cd frontend"
    echo "3. vercel --prod"
    echo ""
fi

echo ""

# Final Summary
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT SUMMARY                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if [ "$RAILWAY_LOGGED_IN" = true ] && [ "$VERCEL_LOGGED_IN" = true ]; then
    echo -e "${GREEN}✅ All deployments initiated!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Wait for deployments to complete"
    echo "2. Get backend URL from Railway dashboard"
    echo "3. Update REACT_APP_BACKEND_URL in Vercel:"
    echo "   vercel env add REACT_APP_BACKEND_URL production"
    echo "4. Update OAuth callback in Atlassian Console"
    echo "5. Configure DNS in Squarespace"
elif [ "$RAILWAY_LOGGED_IN" = true ]; then
    echo -e "${YELLOW}⚠️  Backend ready, frontend needs login${NC}"
    echo "   Run: vercel login"
    echo "   Then: cd frontend && vercel --prod"
elif [ "$VERCEL_LOGGED_IN" = true ]; then
    echo -e "${YELLOW}⚠️  Frontend ready, backend needs login${NC}"
    echo "   Run: railway login"
    echo "   Then: cd backend && railway init && railway up"
else
    echo -e "${YELLOW}⚠️  Please login to both platforms:${NC}"
    echo "   railway login"
    echo "   vercel login"
    echo "   Then run this script again"
fi

echo ""
echo "📚 For detailed instructions, see:"
echo "   - START_HERE.md"
echo "   - DEPLOYMENT_GUIDE.md"
echo "   - QUICK_START.md"
echo ""

