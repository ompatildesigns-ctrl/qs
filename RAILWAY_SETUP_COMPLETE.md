# 🚀 Railway Setup - Complete These Steps

Based on your Railway dashboard, here's what you need to do:

## ✅ Current Status
- ✅ Service created: easygoing-kindness
- ✅ GitHub repo connected: ompatildesigns-ctrl/qs
- ✅ Domain: easygoing-kindness-production-cd75.up.railway.app
- ⚠️ Branch issue: "main" branch doesn't exist
- ⚠️ Root directory not set: Need to set to "backend"
- ⚠️ Start command not set: Need to set uvicorn command
- ⚠️ Environment variables: Need to be set

## 🔧 Fix These Issues in Railway Dashboard

### Step 1: Fix Branch Connection

**Option A: Create main branch locally and push**
```bash
cd /Users/ompatil/Desktop/QuantumSprout
git checkout -b main  # Create main branch
git add .
git commit -m "Initial commit for Railway deployment"
git push origin main
```

**Option B: Use existing branch**
In Railway dashboard:
1. Click the branch dropdown
2. Select an existing branch (or create "main" in GitHub)
3. Click "Disconnect" and reconnect to correct branch

### Step 2: Set Root Directory

In Railway dashboard → Settings → Source:
1. Click "Add Root Directory"
2. Enter: `backend`
3. This tells Railway where your Python code is

### Step 3: Set Start Command

In Railway dashboard → Settings → Deploy:
1. Click "+ Start Command"
2. Enter: `uvicorn server:app --host 0.0.0.0 --port $PORT`
3. This starts your FastAPI server

### Step 4: Set Build Command (Optional but Recommended)

In Railway dashboard → Settings → Build:
1. Click "+ Build Command"
2. Enter: `pip install -r requirements.txt`
3. This installs Python dependencies

### Step 5: Set Environment Variables

In Railway dashboard → Variables tab:
Click "New Variable" and add each:

```
MONGO_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
DB_NAME=quantumsprout_production
JIRA_CLIENT_ID=RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg
JIRA_CLIENT_SECRET=ATOAwGM94of8TKIFcKndcob-3QOoYjuOaBu7b9RYLGyz02fHDdYlhjt29gg1vTtjJJ8988AF6550
JIRA_ENC_KEY=GGDbQ4i49uRqSyo2YIfTNUIs5WOlUlQXGFY6ods7JuQ=
JIRA_REDIRECT_URI=https://easygoing-kindness-production-cd75.up.railway.app/api/auth/jira/callback
FRONTEND_URL=https://quantumsprout.com
CORS_ORIGINS=https://quantumsprout.com,http://localhost:3000
JWT_SECRET_KEY=FF4im6Q67g8jOEm8cotgL1nftjNQ2mYzvs8bQI6WT00
LOG_LEVEL=INFO
```

**Important:** Replace `<username>` and `<password>` in MONGO_URL with your MongoDB Atlas credentials.

### Step 6: Deploy

Once all settings are configured:
1. Click "Deploy" button at the top
2. Or push to the connected branch (if auto-deploy is enabled)
3. Watch the deployment logs

### Step 7: Verify Deployment

After deployment completes:
```bash
curl https://easygoing-kindness-production-cd75.up.railway.app/api/health
```

Should return: `{"status":"ok"}`

### Step 8: Update OAuth Callback

1. Go to: https://developer.atlassian.com/console/myapps/
2. Find app: RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg
3. Update Authorization Callback URL to:
   ```
   https://easygoing-kindness-production-cd75.up.railway.app/api/auth/jira/callback
   ```

## 📋 Quick Checklist

- [ ] Fix branch connection (create/main or use existing)
- [ ] Set Root Directory to `backend`
- [ ] Set Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set all 10 environment variables
- [ ] Click "Deploy" button
- [ ] Verify health endpoint works
- [ ] Update OAuth callback in Atlassian Console

## 🎯 Priority Actions

**Do these first:**
1. Set Root Directory: `backend` ← **CRITICAL**
2. Set Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT` ← **CRITICAL**
3. Fix branch connection ← **CRITICAL**
4. Set environment variables (especially MONGO_URL)
5. Deploy

---

**After these steps, your backend will be live!**

