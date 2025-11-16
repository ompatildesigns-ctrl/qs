#!/bin/bash
# Master deployment script for Quantum Sprout
# This script orchestrates the entire deployment process

set -e

echo "🚀 Quantum Sprout - Master Deployment Script"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if secrets exist
if [ ! -f "secrets.txt" ]; then
    echo -e "${YELLOW}⚠️  Generating secrets...${NC}"
    python3 scripts/generate-secrets-simple.py --save
fi

echo -e "${GREEN}✅ Secrets ready${NC}"
echo ""

# Display secrets (masked)
echo "📋 Generated Secrets:"
echo "   JWT_SECRET_KEY: $(grep JWT_SECRET_KEY secrets.txt | cut -d'=' -f2 | cut -c1-10)..."
echo "   JIRA_ENC_KEY: $(grep JIRA_ENC_KEY secrets.txt | cut -d'=' -f2 | cut -c1-10)..."
echo ""

# Check for required tools
echo "🔍 Checking prerequisites..."

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠️  Railway CLI not found. Install with: npm i -g @railway/cli${NC}"
    RAILWAY_AVAILABLE=false
else
    echo -e "${GREEN}✅ Railway CLI found${NC}"
    RAILWAY_AVAILABLE=true
fi

# Check Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}⚠️  Vercel CLI not found. Install with: npm i -g vercel${NC}"
    VERCEL_AVAILABLE=false
else
    echo -e "${GREEN}✅ Vercel CLI found${NC}"
    VERCEL_AVAILABLE=true
fi

echo ""
echo "📚 Deployment Options:"
echo ""
echo "1. Backend Deployment (Railway)"
echo "2. Frontend Deployment (Vercel)"
echo "3. Full Deployment (Backend + Frontend)"
echo "4. Setup Environment Variables"
echo "5. Generate New Secrets"
echo "6. View Deployment Status"
echo ""

read -p "Select option (1-6): " option

case $option in
    1)
        echo ""
        echo "🚂 Deploying Backend to Railway..."
        if [ "$RAILWAY_AVAILABLE" = false ]; then
            echo -e "${RED}❌ Railway CLI not available. Please install it first.${NC}"
            exit 1
        fi
        cd backend
        if ! railway whoami &> /dev/null; then
            echo "🔐 Please login to Railway:"
            railway login
        fi
        railway init || true
        railway up
        echo ""
        echo -e "${GREEN}✅ Backend deployment initiated!${NC}"
        echo "📝 Next: Set environment variables using option 4"
        ;;
    2)
        echo ""
        echo "🌐 Deploying Frontend to Vercel..."
        if [ "$VERCEL_AVAILABLE" = false ]; then
            echo -e "${RED}❌ Vercel CLI not available. Please install it first.${NC}"
            exit 1
        fi
        cd frontend
        if ! vercel whoami &> /dev/null; then
            echo "🔐 Please login to Vercel:"
            vercel login
        fi
        vercel --prod
        echo ""
        echo -e "${GREEN}✅ Frontend deployment initiated!${NC}"
        ;;
    3)
        echo ""
        echo "🚀 Full Deployment..."
        echo ""
        echo "Step 1: Backend"
        $0 1
        echo ""
        echo "Step 2: Frontend"
        $0 2
        ;;
    4)
        echo ""
        echo "🔧 Setting up environment variables..."
        read -p "Enter your Railway backend URL: " backend_url
        if [ -z "$backend_url" ]; then
            echo -e "${RED}❌ Backend URL is required${NC}"
            exit 1
        fi
        ./scripts/setup-env.sh "$backend_url"
        ;;
    5)
        echo ""
        echo "🔐 Generating new secrets..."
        python3 scripts/generate-secrets-simple.py --save
        echo -e "${GREEN}✅ New secrets generated in secrets.txt${NC}"
        ;;
    6)
        echo ""
        echo "📊 Deployment Status"
        echo "==================="
        echo ""
        echo "Backend Files:"
        ls -1 backend/{Procfile,Dockerfile,start.sh,runtime.txt} 2>/dev/null | wc -l | xargs echo "   Config files:"
        echo ""
        echo "Frontend Files:"
        ls -1 {railway.json,render.yaml,vercel.json} 2>/dev/null | wc -l | xargs echo "   Config files:"
        echo ""
        echo "Scripts:"
        ls -1 scripts/*.{sh,py} 2>/dev/null | wc -l | xargs echo "   Available:"
        echo ""
        if [ -f "secrets.txt" ]; then
            echo -e "${GREEN}✅ Secrets file exists${NC}"
        else
            echo -e "${YELLOW}⚠️  Secrets file not found${NC}"
        fi
        ;;
    *)
        echo -e "${RED}❌ Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "📚 For detailed instructions, see:"
echo "   - AUTO_DEPLOY.md (automated steps)"
echo "   - DEPLOYMENT_GUIDE.md (complete guide)"
echo "   - QUICK_START.md (fast deployment)"

