#!/bin/bash
# Automated Railway deployment script

set -e

echo "🚂 Deploying Quantum Sprout Backend to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm i -g @railway/cli
fi

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway:"
    railway login
fi

# Initialize if needed
if [ ! -f ".railway/railway.toml" ]; then
    echo "📦 Initializing Railway project..."
    railway init
fi

echo "✅ Railway project ready!"
echo ""
echo "📝 Next steps:"
echo "1. Set environment variables in Railway dashboard or via CLI:"
echo "   railway variables set MONGO_URL='...'"
echo "   railway variables set JWT_SECRET_KEY='FF4im6Q67g8jOEm8cotgL1nftjNQ2mYzvs8bQI6WT00'"
echo "   (See secrets.txt for all secrets)"
echo ""
echo "2. Deploy:"
echo "   railway up"
echo ""
echo "3. Get deployment URL:"
echo "   railway domain"

