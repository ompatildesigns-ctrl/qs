# 🔧 IMMEDIATE FIX: Deployment Error

## ⚠️ Problem

Railway error: **"There was an error deploying from source"**

## 🎯 Most Likely Causes (in order)

### 1. **Root Directory Not Set** (MOST COMMON)
Railway doesn't know your code is in the `backend/` folder.

**Fix in Railway Dashboard:**
1. Go to **Settings** tab
2. Scroll to **"Source"** section
3. Find **"Root Directory"** field
4. Enter: `backend`
5. **Save**

### 2. **Start Command Missing/Incorrect**
Railway doesn't know how to start your app.

**Fix in Railway Dashboard:**
1. Go to **Settings** tab
2. Scroll to **"Deploy"** or **"Start Command"** section
3. Find **"Custom Start Command"** field
4. Enter: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. **Save**

### 3. **Code Not Pushed to GitHub**
If Railway is connected to a repo but code isn't there.

**Fix:**
```bash
cd /Users/ompatil/Desktop/QuantumSprout
git add .
git commit -m "Initial commit - backend ready for deployment"
git push origin main
```

### 4. **Check Deployment Logs**
See the exact error message.

**In Railway Dashboard:**
1. Click **"Logs"** tab (top navigation)
2. Look for red error messages
3. Common errors:
   - "No such file or directory" → Root Directory issue
   - "Module not found" → Dependencies issue
   - "Command not found" → Start Command issue
   - "Build failed" → Build process issue

---

## ✅ QUICK CHECKLIST

In Railway Dashboard → Settings:

- [ ] **Root Directory**: `backend` (MUST BE SET!)
- [ ] **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
- [ ] **Build Command**: Leave empty OR `pip install -r requirements.txt`
- [ ] **Branch**: Connected to `main` (or your branch)
- [ ] **Logs**: Check for specific error messages

---

## 🚀 IMMEDIATE ACTION STEPS

### Step 1: Set Root Directory (CRITICAL)

**In Railway Dashboard:**

1. Click **"Settings"** tab
2. Scroll to **"Source"** section
3. Look for **"Root Directory"** or **"Service Root"**
4. If empty, click **"+ Add Root Directory"** or enter in field
5. Enter: `backend`
6. **Save**

### Step 2: Verify Start Command

**In Railway Dashboard → Settings:**

1. Scroll to **"Deploy"** or **"Start Command"** section
2. Look for **"Custom Start Command"** or **"Start Command"**
3. Should be: `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. If missing or wrong, fix it
5. **Save**

### Step 3: Check Logs for Exact Error

**In Railway Dashboard:**

1. Click **"Logs"** tab
2. Look for error messages
3. Note the exact error
4. Fix based on error message

### Step 4: Redeploy

After fixing settings:

1. Go to **"Deployments"** tab
2. Click **"New Deployment"** or **"Redeploy"**
3. Watch logs for success/error

---

## 🔍 What to Look For in Logs

### Error: "No such file or directory: server.py"
**Fix:** Root Directory not set to `backend`

### Error: "ModuleNotFoundError: No module named 'fastapi'"
**Fix:** Build failed - check `requirements.txt` is in `backend/` folder

### Error: "command not found: uvicorn"
**Fix:** Start Command wrong or dependencies not installed

### Error: "port already in use" or "address already in use"
**Fix:** Use `$PORT` in start command (already correct)

### Error: "Build failed" or "Installation failed"
**Fix:** Check `requirements.txt` syntax, all packages valid

---

## 📋 Verify These Files Exist

These must be in your GitHub repo (in `backend/` folder):

- ✅ `server.py`
- ✅ `requirements.txt`
- ✅ `models.py`
- ✅ `auth.py`
- ✅ `jira_client.py`
- ✅ `crypto_utils.py`
- ✅ All other Python files backend needs

**Check in Railway → Settings → Source → Verify connected repo has these files**

---

## ⚡ FASTEST FIX (Most Common Issue)

**90% of deployment errors are Root Directory not set!**

1. Railway Dashboard → Settings
2. **Root Directory**: Set to `backend`
3. **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. **Save**
5. Deployments tab → New Deployment

---

**Check the Logs tab first to see the exact error, then fix based on that!**

