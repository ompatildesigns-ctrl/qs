# 🎯 Railway Dashboard - Complete Setup Steps

## Based on Your Current Dashboard State

You're on the Railway dashboard for service "easygoing-kindness". Here's exactly what to do:

## ✅ Step-by-Step Actions

### 1. Fix Root Directory (CRITICAL)

**Location:** Settings → Source → "Add Root Directory"

1. Click "Add Root Directory" link
2. Enter: `backend`
3. Click Save/Apply

**Why:** This tells Railway where your Python code lives.

### 2. Add Start Command (CRITICAL)

**Location:** Settings → Deploy → "Custom Start Command"

1. Click "+ Start Command" button
2. Enter exactly:
   ```
   uvicorn server:app --host 0.0.0.0 --port $PORT
   ```
3. Click Save/Apply

**Why:** This starts your FastAPI server.

### 3. Add Build Command (Recommended)

**Location:** Settings → Build → "Custom Build Command"

1. Click "+ Build Command" button
2. Enter:
   ```
   pip install -r requirements.txt
   ```
3. Click Save/Apply

**Why:** This installs your Python dependencies before deployment.

### 4. Fix Branch Connection

**Location:** Settings → Source → "Branch connected to production"

**Option A:** If code was pushed to main branch:
1. Wait a few seconds for Railway to detect the branch
2. Refresh the page
3. Select "main" from dropdown

**Option B:** Disconnect and reconnect:
1. Click "Disconnect" next to branch dropdown
2. Click "Connect Branch"
3. Select "main" branch

### 5. Set Environment Variables

**Location:** Variables tab (top of dashboard)

Click "New Variable" for each:

```
MONGO_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```
*(Replace <username> and <password> with your MongoDB credentials)*

```
DB_NAME=quantumsprout_production
```

```
JIRA_CLIENT_ID=RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg
```

```
JIRA_CLIENT_SECRET=ATOAwGM94of8TKIFcKndcob-3QOoYjuOaBu7b9RYLGyz02fHDdYlhjt29gg1vTtjJJ8988AF6550
```

```
JIRA_ENC_KEY=GGDbQ4i49uRqSyo2YIfTNUIs5WOlUlQXGFY6ods7JuQ=
```

```
JIRA_REDIRECT_URI=https://easygoing-kindness-production-cd75.up.railway.app/api/auth/jira/callback
```

```
FRONTEND_URL=https://quantumsprout.com
```

```
CORS_ORIGINS=https://quantumsprout.com,http://localhost:3000
```

```
JWT_SECRET_KEY=FF4im6Q67g8jOEm8cotgL1nftjNQ2mYzvs8bQI6WT00
```

```
LOG_LEVEL=INFO
```

### 6. Deploy

**Location:** Top right of dashboard

1. Click "Deploy" button
2. Or if auto-deploy is enabled, push to main branch
3. Watch deployment logs

### 7. Verify Deployment

After deployment completes:

1. Go to "Deployments" tab
2. Click on latest deployment
3. Check logs for errors
4. Test: `https://easygoing-kindness-production-cd75.up.railway.app/api/health`

## 🎯 Priority Order

Do these in this order:

1. ✅ **Root Directory** → `backend` ← **DO THIS FIRST**
2. ✅ **Start Command** → `uvicorn server:app --host 0.0.0.0 --port $PORT` ← **DO THIS SECOND**
3. ✅ **Build Command** → `pip install -r requirements.txt`
4. ✅ **Environment Variables** → Add all 10 variables
5. ✅ **Branch** → Ensure main branch is connected
6. ✅ **Deploy** → Click Deploy button

## ⚡ Quick Actions Summary

**In Dashboard Right Now:**
1. Click "Add Root Directory" → Enter `backend`
2. Click "+ Start Command" → Enter `uvicorn server:app --host 0.0.0.0 --port $PORT`
3. Go to Variables tab → Add all 10 variables
4. Go back to Settings → Ensure branch is connected
5. Click "Deploy" button at top

---

**After these steps, your backend will deploy automatically!**

