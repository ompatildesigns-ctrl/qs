#!/bin/bash

# Quantum Sprout - Secret Generation Script
# Generates secure secrets for production deployment

echo "🔐 Quantum Sprout - Secret Generation"
echo "======================================"
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 found"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo "✅ Python found"
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3."
    exit 1
fi

echo ""
echo "Generating secrets..."
echo ""

# Generate JWT Secret
echo "1. JWT_SECRET_KEY (32+ characters):"
JWT_SECRET=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(32))")
echo "   $JWT_SECRET"
echo ""

# Generate Encryption Key (if needed)
echo "2. JIRA_ENC_KEY (Fernet key - base64 encoded):"
ENCRYPTION_KEY=$($PYTHON_CMD -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "   $ENCRYPTION_KEY"
echo ""

# Instructions
echo "======================================"
echo "📝 Instructions:"
echo ""
echo "1. Copy JWT_SECRET_KEY to your backend environment variables"
echo "2. If you need a new JIRA_ENC_KEY, use the generated value above"
echo "   ⚠️  WARNING: Changing JIRA_ENC_KEY will invalidate all stored OAuth tokens!"
echo ""
echo "3. Save these secrets securely:"
echo "   - Use your platform's secret manager (Railway, Render, etc.)"
echo "   - Never commit secrets to Git"
echo "   - Store in password manager for backup"
echo ""
echo "✅ Secrets generated successfully!"

