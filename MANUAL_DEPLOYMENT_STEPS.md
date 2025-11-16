# 🚀 Manual Deployment Steps (After Railway Login)

You're authenticated to Railway! Here are the manual steps to complete deployment:

## ✅ Current Status
- ✅ Railway authenticated: ompatildesigns@gmail.com
- ✅ Frontend deployed to Vercel
- ⚠️ Backend needs manual Railway project setup

## 📋 Step-by-Step Instructions

### Step 1: Create/Link Railway Project

**Option A: Via Railway Dashboard (Recommended)**
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo" or "Empty Project"
4. If using GitHub: Connect your QuantumSprout repository
5. If empty: We'll deploy via CLI

**Option B: Via CLI (Interactive Terminal)**
```bash
cd /Users/ompatil/Desktop/QuantumSprout/backend
railway init
# Select workspace: ompatildesigns-ctrl's Projects
# Select project or create new
```

**Option C: Link to Existing Project**
```bash
cd /Users/ompatil/Desktop/QuantumSprout/backend
railway link <project-id>
# Or just: railway link (will prompt)
```

### Step 2: Deploy Backend

Once project is linked/created:

```bash
cd /Users/ompatil/Desktop/QuantumSprout/backend
railway up
```

This will:
- Build your Python application
- Deploy to Railway
- Provide a deployment URL

### Step 3: Get Backend URL

After deployment completes:

```bash
railway domain
```

Or check Railway dashboard for your deployment URL (format: `https://xxx.up.railway.app`)

### Step 4: Set Environment Variables

**Via CLI:**
```bash
cd /Users/ompatil/Desktop/QuantumSprout
BACKEND_URL="https://your-railway-url.up.railway.app"
./scripts/setup-env.sh "$BACKEND_URL"
```

**Via Railway Dashboard:**
1. Go to Railway project → Variables tab
2. Add these variables:

```env
MONGO_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
DB_NAME=quantumsprout_production
JIRA_CLIENT_ID=RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg
JIRA_CLIENT_SECRET=ATOAwGM94of8TKIFcKndcob-3QOoYjuOaBu7b9RYLGyz02fHDdYlhjt29gg1vTtjJJ8988AF6550
JIRA_ENC_KEY=GGDbQ4i49uRqSyo2YIfTNUIs5WOlUlQXGFY6ods7JuQ=
JIRA_REDIRECT_URI=https://<your-railway-url>/api/auth/jira/callback
FRONTEND_URL=https://quantumsprout.com
CORS_ORIGINS=https://quantumsprout.com,http://localhost:3000
JWT_SECRET_KEY=FF4im6Q67g8jOEm8cotgL1nftjNQ2mYzvs8bQI6WT00
LOG_LEVEL=INFO
```

**Important:** Replace `<your-railway-url>` with your actual Railway deployment URL.

### Step 5: Update Frontend Environment Variable

```bash
cd /Users/ompatil/Desktop/QuantumSprout/frontend
vercel env add REACT_APP_BACKEND_URL production
# Enter your Railway backend URL when prompted
```

### Step 6: Update OAuth Callback

1. Go to: https://developer.atlassian.com/console/myapps/
2. Find app: `RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg`
3. Update Authorization Callback URL to:
   `https://<your-railway-url>/api/auth/jira/callback`

### Step 7: Test Deployment

```bash
# Test backend health
curl https://<your-railway-url>/api/health

# Should return: {"status":"ok"} or similar
```

### Step 8: Configure DNS (Optional)

In Squarespace DNS, add:
- CNAME: www → cname.vercel-dns.com
- A: @ → (check Vercel dashboard for IPs)

## 🎯 Quick Commands (Copy-Paste)

```bash
# 1. Navigate to backend
cd /Users/ompatil/Desktop/QuantumSprout/backend

# 2. Create/link Railway project (interactive)
railway init
# OR
railway link

# 3. Deploy
railway up

# 4. Get URL
railway domain

# 5. Set environment variables
cd ..
./scripts/setup-env.sh "https://your-railway-url.up.railway.app"
```

## 📊 Current Status

| Component | Status |
|-----------|--------|
| Railway Auth | ✅ Authenticated |
| Frontend | ✅ Deployed to Vercel |
| Backend | ⚠️ Needs project setup |
| Environment Vars | ⚠️ Pending |
| OAuth | ⚠️ Pending |

## ✅ After Deployment

Once backend is deployed:
1. ✅ Backend URL will be available
2. ✅ Environment variables can be set
3. ✅ OAuth callback can be updated
4. ✅ Frontend can connect to backend
5. ✅ Full deployment complete!

---

**You're almost there! Just need to create/link the Railway project.**

