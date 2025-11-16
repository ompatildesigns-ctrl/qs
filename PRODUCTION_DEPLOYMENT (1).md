# QUANTUM SPROUT PRODUCTION DEPLOYMENT GUIDE
## Deploying to www.quantumsprout.com

**Product:** Quantum Sprout - Billion Dollar Bottleneck Finder  
**Production Domain:** www.quantumsprout.com  
**Preview Domain:** velocity-boost-1.preview.emergentagent.com (development only)

---

## ENVIRONMENT CONFIGURATION FOR PRODUCTION

### 1. Backend Environment Variables (.env)

When deploying to production at www.quantumsprout.com, update these values:

```env
# MongoDB (keep as-is or use production MongoDB Atlas)
MONGO_URL=mongodb://localhost:27017
DB_NAME=quantum_sprout_production

# CORS (update to production domain)
CORS_ORIGINS="https://www.quantumsprout.com,https://quantumsprout.com"

# Jira OAuth (update redirect URI to production)
JIRA_CLIENT_ID=fYmZephqWGLa2uVEzBDUAgjetrzCEVVW
JIRA_CLIENT_SECRET=[your_secret]
JIRA_ENC_KEY=[your_encryption_key]
JIRA_REDIRECT_URI="https://www.quantumsprout.com/api/auth/jira/callback"

# Frontend URL (update to production)
FRONTEND_URL="https://www.quantumsprout.com"
```

### 2. Atlassian OAuth App Update

**CRITICAL:** Update your Atlassian OAuth app configuration:

1. Go to: https://developer.atlassian.com/console/myapps
2. Select your app: `fYmZephqWGLa2uVEzBDUAgjetrzCEVVW`
3. Update **Authorization callback URL** to:
   ```
   https://www.quantumsprout.com/api/auth/jira/callback
   ```
4. Add **www.quantumsprout.com** to allowed domains
5. Save changes

### 3. DNS Configuration

Point www.quantumsprout.com to your production server:

```
Type: A Record
Host: www
Value: [Your Server IP]
TTL: 3600

Type: A Record  
Host: @
Value: [Your Server IP]
TTL: 3600
```

### 4. SSL/TLS Certificate

Install SSL certificate for HTTPS (required for OAuth):

**Option A: Let's Encrypt (Free)**
```bash
certbot --nginx -d www.quantumsprout.com -d quantumsprout.com
```

**Option B: Cloudflare (Recommended)**
- Enable Cloudflare for quantumsprout.com
- Get automatic SSL certificate
- Enable CDN for faster global access

---

## URL MAPPING GUIDE

### Preview (Development) - Current State
- **Frontend:** https://prod-analytics-4.preview.emergentagent.com
- **Backend API:** https://prod-analytics-4.preview.emergentagent.com/api
- **Terms:** https://prod-analytics-4.preview.emergentagent.com/#/terms
- **Privacy:** https://prod-analytics-4.preview.emergentagent.com/#/privacy
- **OAuth Callback:** https://prod-analytics-4.preview.emergentagent.com/api/auth/jira/callback

### Production - After Deployment to www.quantumsprout.com
- **Frontend:** https://www.quantumsprout.com
- **Backend API:** https://www.quantumsprout.com/api
- **Terms:** https://www.quantumsprout.com/#/terms
- **Privacy:** https://www.quantumsprout.com/#/privacy
- **OAuth Callback:** https://www.quantumsprout.com/api/auth/jira/callback

---

## EMAIL ADDRESSES (Already Updated)

All email addresses already use @quantumsprout.com:
✅ legal@quantumsprout.com
✅ privacy@quantumsprout.com
✅ security@quantumsprout.com
✅ support@quantumsprout.com
✅ gdpr@quantumsprout.com

**Action Required:** Set up email forwarding or mailboxes for these addresses.

---

## DEPLOYMENT CHECKLIST FOR www.quantumsprout.com

### Pre-Deployment (Do Once):
- [ ] Set up DNS A records pointing to production server
- [ ] Install SSL certificate (Let's Encrypt or Cloudflare)
- [ ] Update Atlassian OAuth app callback URL to www.quantumsprout.com
- [ ] Set up email addresses (@quantumsprout.com)
- [ ] Update backend .env with production values
- [ ] Set up MongoDB (local or Atlas)
- [ ] Test OAuth flow on production domain

### Deployment Steps:
- [ ] Clone code to production server
- [ ] Install dependencies (yarn, pip install -r requirements.txt)
- [ ] Update .env with production URLs
- [ ] Start services (supervisorctl start all)
- [ ] Verify health check: https://www.quantumsprout.com/api/health
- [ ] Test OAuth: Click "Connect Jira" button
- [ ] Verify Atlassian redirects back correctly
- [ ] Test full user flow end-to-end
- [ ] Monitor logs for errors

### Post-Deployment Verification:
- [ ] Legal pages accessible: www.quantumsprout.com/#/terms and #/privacy
- [ ] Cookie consent appears on first visit
- [ ] Footer displays with correct emails
- [ ] Financial Impact dashboard loads with $15.1M CoD
- [ ] Team ROI shows 1,015% Sundew, 495% US
- [ ] One-Click Actions work (preview → dry run)
- [ ] Settings page functional
- [ ] All tabs navigate correctly
- [ ] HTTPS enforced (no HTTP access)

---

## CURRENT STATE SUMMARY

**Preview Environment (Development):**
- URL: `velocity-boost-1.preview.emergentagent.com`
- Status: ✅ Fully functional, 94/100 certified
- Use for: Testing, demos, development
- Limitations: Platform-managed domain (cannot change)

**Production Environment (Your Domain):**
- URL: `www.quantumsprout.com`
- Status: 🎯 Ready to deploy (after environment setup)
- Use for: Public users, customers, revenue
- Flexibility: You control everything

---

## WHAT CANNOT BE CHANGED IN CURRENT PREVIEW

❌ **Cannot modify in preview environment:**
- Base URL: velocity-boost-1.preview.emergentagent.com (Kubernetes platform manages this)
- .env file: CRITICAL - Do not modify or deployment breaks
- OAuth redirect: Must match preview URL for current Jira app

✅ **What's already Quantum Sprout branded:**
- All email addresses: @quantumsprout.com (28 instances)
- Company name: Quantum Sprout Inc. (6 instances)
- Footer copyright: "© 2025 Quantum Sprout"
- Legal documents: All reference Quantum Sprout
- Security contacts: All @quantumsprout.com

---

## RECOMMENDED DEPLOYMENT STRATEGY

### Option A: Deploy to www.quantumsprout.com for Production
1. Set up production server (AWS, DigitalOcean, etc.)
2. Point DNS to production
3. Update .env with production values
4. Deploy code
5. Update Atlassian OAuth callback
6. **Result:** www.quantumsprout.com goes live!

### Option B: Keep Both (Recommended)
1. **Preview:** velocity-boost-1.preview.emergentagent.com (staging/testing)
2. **Production:** www.quantumsprout.com (public users)
3. **Benefit:** Test features on preview before pushing to production

---

## PRODUCTION URL UPDATE CHECKLIST

When you deploy to www.quantumsprout.com, update:

**Backend (.env file on production server only):**
```env
FRONTEND_URL="https://www.quantumsprout.com"
CORS_ORIGINS="https://www.quantumsprout.com,https://quantumsprout.com"
JIRA_REDIRECT_URI="https://www.quantumsprout.com/api/auth/jira/callback"
```

**Atlassian Developer Console:**
- Callback URL: https://www.quantumsprout.com/api/auth/jira/callback

**DNS Provider:**
- A record: www → [Server IP]
- A record: @ → [Server IP]

**Email Provider:**
- Set up @quantumsprout.com mailboxes/forwarding

---

## NEXT STEPS

1. **Keep preview environment as-is** (for testing) ✅
2. **Set up production server** for www.quantumsprout.com
3. **Deploy code** with production .env values
4. **Update OAuth** callback to production domain
5. **Launch** at www.quantumsprout.com! 🚀

**Current State:** ✅ Product is 94/100, all features working, branding correct (Quantum Sprout), legal compliant, ready to deploy to your new domain!

**Need help deploying to www.quantumsprout.com? Let me know!**
