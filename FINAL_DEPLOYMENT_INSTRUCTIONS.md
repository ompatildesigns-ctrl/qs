# 🚀 Final Deployment Instructions

## ✅ What's Done

### Frontend - DEPLOYED ✅
- ✅ **URL:** https://frontend-kerrzak8x-oms-projects-ac94f1bd.vercel.app
- ✅ **Environment Variable:** REACT_APP_BACKEND_URL set to https://easygoing-kindness-production-ed75.up.railway.app
- ✅ **Status:** Live and ready

### Backend - CONFIGURED ⚠️
- ✅ **Project:** easygoing-kindness (linked)
- ✅ **URL:** https://easygoing-kindness-production-ed75.up.railway.app
- ✅ **Domain:** Created
- ⚠️ **Service:** Needs to be created in Railway dashboard
- ⚠️ **Deployment:** Waiting for service creation

## 🔧 Complete These Final Steps

### Step 1: Create Service in Railway Dashboard

1. Go to: https://railway.app/dashboard
2. Open project: **easygoing-kindness**
3. Click **"New Service"** or **"Add Service"**
4. Choose **"GitHub Repo"** (connect your repo) OR **"Empty Service"**
5. Configure service:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Watch Paths:** `backend/`

### Step 2: Set Environment Variables in Railway Dashboard

Once service is created, go to **Variables** tab and add:

```env
MONGO_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
DB_NAME=quantumsprout_production
JIRA_CLIENT_ID=RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg
JIRA_CLIENT_SECRET=ATOAwGM94of8TKIFcKndcob-3QOoYjuOaBu7b9RYLGyz02fHDdYlhjt29gg1vTtjJJ8988AF6550
JIRA_ENC_KEY=GGDbQ4i49uRqSyo2YIfTNUIs5WOlUlQXGFY6ods7JuQ=
JIRA_REDIRECT_URI=https://easygoing-kindness-production-ed75.up.railway.app/api/auth/jira/callback
FRONTEND_URL=https://quantumsprout.com
CORS_ORIGINS=https://quantumsprout.com,http://localhost:3000
JWT_SECRET_KEY=FF4im6Q67g8jOEm8cotgL1nftjNQ2mYzvs8bQI6WT00
LOG_LEVEL=INFO
```

**Important:** Replace `<username>` and `<password>` in MONGO_URL with your MongoDB Atlas credentials.

### Step 3: Deploy Backend

After service is created and variables are set:

**Option A: Via Dashboard**
- Railway will auto-deploy when you connect GitHub repo
- Or click **"Deploy"** button

**Option B: Via CLI**
```bash
cd /Users/ompatil/Desktop/QuantumSprout/backend
railway service <service-name>
railway up
```

### Step 4: Update OAuth Callback

1. Go to: https://developer.atlassian.com/console/myapps/
2. Find app: **RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg**
3. Update **Authorization Callback URL** to:
   ```
   https://easygoing-kindness-production-ed75.up.railway.app/api/auth/jira/callback
   ```
4. Save changes

### Step 5: Verify Deployment

```bash
# Test backend health
curl https://easygoing-kindness-production-ed75.up.railway.app/api/health

# Should return: {"status":"ok"}
```

### Step 6: Configure DNS (Optional)

In Squarespace DNS:
- **CNAME:** www → cname.vercel-dns.com
- **A:** @ → (check Vercel dashboard for IP addresses)

## 📊 Current URLs

| Component | URL | Status |
|-----------|-----|--------|
| **Frontend** | https://frontend-kerrzak8x-oms-projects-ac94f1bd.vercel.app | ✅ Live |
| **Backend** | https://easygoing-kindness-production-ed75.up.railway.app | ⚠️ Waiting for service |
| **OAuth Callback** | https://easygoing-kindness-production-ed75.up.railway.app/api/auth/jira/callback | ⚠️ Update after deploy |

## ✅ Status Summary

| Task | Status |
|------|--------|
| Frontend Deployment | ✅ Complete |
| Frontend Environment Variable | ✅ Set |
| Railway Project | ✅ Linked |
| Railway Domain | ✅ Created |
| Service Creation | ⚠️ Do in dashboard |
| Environment Variables | ⚠️ Set in dashboard |
| Backend Deployment | ⚠️ After service creation |
| OAuth Update | ⚠️ After backend deploys |
| MongoDB Setup | ⚠️ Set MONGO_URL |

## 🎯 Next Actions

1. **Open Railway dashboard:** https://railway.app/dashboard/project/easygoing-kindness
2. **Create service** (GitHub repo or empty)
3. **Set environment variables** (Variables tab)
4. **Deploy backend** (auto or manual)
5. **Update OAuth callback** in Atlassian Console
6. **Test deployment**

---

**You're 90% there! Just need to create the service and set variables in Railway dashboard!**

