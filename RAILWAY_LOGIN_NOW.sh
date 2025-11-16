#!/bin/bash
# Quick Railway login and deployment script
# Run this in your interactive terminal

echo "🚂 Railway Login & Deployment"
echo "=============================="
echo ""
echo "Step 1: Login to Railway"
echo "This will open your browser..."
echo ""

railway login

echo ""
echo "Step 2: Verifying login..."
if railway whoami &> /dev/null; then
    echo "✅ Login successful!"
    echo ""
    echo "Step 3: Deploying backend..."
    cd backend
    railway init
    railway up
    echo ""
    echo "Step 4: Getting deployment URL..."
    BACKEND_URL=$(railway domain 2>/dev/null | head -1 || echo "")
    if [ ! -z "$BACKEND_URL" ]; then
        echo "Backend URL: $BACKEND_URL"
        echo ""
        echo "Step 5: Setting environment variables..."
        cd ..
        ./scripts/setup-env.sh "$BACKEND_URL" || echo "Set env vars manually in Railway dashboard"
    fi
    echo ""
    echo "✅ Backend deployment complete!"
else
    echo "❌ Login failed. Please try again."
fi
