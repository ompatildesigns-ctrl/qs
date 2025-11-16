# 🎯 What to Do Now - Next Steps

## Current Status:
✅ MongoDB cluster created: quantumsprout-cluster
✅ Database user created: ompatildesigns_db_user
✅ Connection string obtained
⚠️ Network Access: Need to configure for Railway
⚠️ Railway: Need to add MONGO_URL variable

---

## 📋 Step-by-Step Actions

### Step 1: Configure Network Access (MongoDB Atlas)

**IMPORTANT:** Railway needs to connect to MongoDB, so we must allow all IPs.

1. In MongoDB Atlas (where you are now):
   - Click **"SECURITY"** in left sidebar (expand it)
   - Click **"Database & Network Access"**
   - OR click **"Network Access"** directly

2. Click **"Add IP Address"** button

3. Click **"Allow Access from Anywhere"** button
   - This adds `0.0.0.0/0` (allows all IP addresses)
   - Click **"Confirm"**

**Why:** Railway uses dynamic IPs, so we need to allow all IPs for your backend to connect.

---

### Step 2: Add MONGO_URL to Railway

1. **Go to Railway Dashboard:**
   - Open Railway in a new tab: https://railway.app/dashboard
   - Navigate to project: **easygoing-kindness**
   - Click **"Variables"** tab

2. **Add MONGO_URL variable:**
   - Click **"New Variable"** button
   - **Variable Name:** `MONGO_URL`
   - **Variable Value:** Paste this (your formatted connection string):
     ```
     mongodb+srv://ompatildesigns_db_user:oMlGENOBJ90KfP0h@quantumsprout-cluster.hvqlwm5.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
     ```
   - Click **"Add"**

---

### Step 3: Complete Railway Configuration

**Still need to do in Railway Dashboard:**

1. **Set Root Directory:**
   - Go to **Settings** tab → **Source** section
   - Click **"Add Root Directory"**
   - Enter: `backend`
   - Save

2. **Set Start Command:**
   - Go to **Settings** tab → **Deploy** section
   - Click **"+ Start Command"**
   - Enter: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Save

3. **Add Remaining Environment Variables:**
   - Go to **Variables** tab
   - Add these 9 more variables (see STEP3_ENV_VARIABLES.md):
     - `DB_NAME=quantumsprout_production`
     - `JIRA_CLIENT_ID=RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg`
     - `JIRA_CLIENT_SECRET=ATOAwGM94of8TKIFcKndcob-3QOoYjuOaBu7b9RYLGyz02fHDdYlhjt29gg1vTtjJJ8988AF6550`
     - `JIRA_ENC_KEY=GGDbQ4i49uRqSyo2YIfTNUIs5WOlUlQXGFY6ods7JuQ=`
     - `JIRA_REDIRECT_URI=https://easygoing-kindness-production-cd75.up.railway.app/api/auth/jira/callback`
     - `FRONTEND_URL=https://quantumsprout.com`
     - `CORS_ORIGINS=https://quantumsprout.com,http://localhost:3000`
     - `JWT_SECRET_KEY=FF4im6Q67g8jOEm8cotgL1nftjNQ2mYzvs8bQI6WT00`
     - `LOG_LEVEL=INFO`

4. **Deploy:**
   - Click **"Deploy"** button at top
   - Watch deployment logs

---

### Step 4: Update OAuth Callback (After Deployment)

Once Railway deployment is complete:

1. Go to: https://developer.atlassian.com/console/myapps/
2. Find app: **RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg**
3. Update **Authorization Callback URL** to:
   ```
   https://easygoing-kindness-production-cd75.up.railway.app/api/auth/jira/callback
   ```
4. Save changes

---

### Step 5: Test Deployment

After Railway deploys:

```bash
# Test backend health
curl https://easygoing-kindness-production-cd75.up.railway.app/api/health

# Should return: {"status":"ok"}
```

---

## 🎯 Priority Order

**Do these NOW (in order):**

1. ✅ **MongoDB Network Access** → Allow 0.0.0.0/0 (5 minutes)
2. ✅ **Railway Variables** → Add MONGO_URL (2 minutes)
3. ✅ **Railway Settings** → Root Directory + Start Command (2 minutes)
4. ✅ **Railway Variables** → Add remaining 9 variables (5 minutes)
5. ✅ **Railway Deploy** → Click Deploy button (5-10 minutes)
6. ⚠️ **OAuth Update** → Update callback URL (2 minutes)
7. ✅ **Test** → Verify deployment works

---

## 📊 Current Status Summary

| Task | Status |
|------|--------|
| MongoDB Cluster | ✅ Created |
| Database User | ✅ Created |
| Connection String | ✅ Obtained |
| Network Access | ⚠️ **DO THIS NOW** |
| Railway MONGO_URL | ⚠️ **DO THIS NOW** |
| Railway Root Directory | ⚠️ Pending |
| Railway Start Command | ⚠️ Pending |
| Railway Other Variables | ⚠️ Pending |
| Railway Deployment | ⚠️ Pending |
| OAuth Callback | ⚠️ Pending |

---

**Next immediate action: Configure MongoDB Network Access!**

