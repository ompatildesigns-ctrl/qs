#!/usr/bin/env python3
"""
Quantum Sprout - Simple Secret Generation (no dependencies)
Generates secure secrets for production deployment
"""
import secrets
import base64
import sys

def generate_jwt_secret():
    """Generate a secure JWT secret (32+ characters)."""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """Generate a Fernet encryption key (base64 encoded 32 bytes)."""
    key = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(key).decode()

def main():
    print("🔐 Quantum Sprout - Secret Generation")
    print("=" * 40)
    print()
    
    # Generate JWT Secret
    jwt_secret = generate_jwt_secret()
    print("1. JWT_SECRET_KEY (32+ characters):")
    print(f"   {jwt_secret}")
    print()
    
    # Generate Encryption Key
    encryption_key = generate_encryption_key()
    print("2. JIRA_ENC_KEY (Fernet key - base64 encoded):")
    print(f"   {encryption_key}")
    print()
    
    # Instructions
    print("=" * 40)
    print("📝 Instructions:")
    print()
    print("1. Copy JWT_SECRET_KEY to your backend environment variables")
    print("2. If you need a new JIRA_ENC_KEY, use the generated value above")
    print("   ⚠️  WARNING: Changing JIRA_ENC_KEY will invalidate all stored OAuth tokens!")
    print()
    print("3. Save these secrets securely:")
    print("   - Use your platform's secret manager (Railway, Render, etc.)")
    print("   - Never commit secrets to Git")
    print("   - Store in password manager for backup")
    print()
    print("✅ Secrets generated successfully!")
    
    # Optionally write to file
    if len(sys.argv) > 1 and sys.argv[1] == "--save":
        filename = "secrets.txt"
        with open(filename, "w") as f:
            f.write("# Quantum Sprout Production Secrets\n")
            f.write("# Generated: " + secrets.token_hex(8) + "\n")
            f.write("# ⚠️  KEEP THIS FILE SECRET - DO NOT COMMIT TO GIT!\n\n")
            f.write(f"JWT_SECRET_KEY={jwt_secret}\n")
            f.write(f"JIRA_ENC_KEY={encryption_key}\n")
        print(f"\n💾 Secrets saved to {filename}")
        print("   ⚠️  Remember to delete this file after copying secrets!")

if __name__ == "__main__":
    main()

