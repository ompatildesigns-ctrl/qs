# 🗄️ MongoDB Atlas - Complete Setup Guide

## Current Step: Creating Free Cluster ✅

You're on the MongoDB Atlas cluster creation page. Here's what to do:

## ✅ Step 1: Complete Cluster Creation

**On the current page you see:**

1. **Cluster Selection:** ✅ Free tier is selected (good choice!)

2. **Configuration:**
   - **Name:** Keep "Cluster0" (default) or change to "quantumsprout-cluster"
   - **Provider:** AWS is selected (good)
   - **Region:** Select closest region to your Railway deployment
     - If Railway is US-based: "N. Virginia (us-east-1)" is fine
     - Or choose any AWS region

3. **Quick Setup:**
   - ✅ **Automate security setup:** Leave checked (this will create a database user automatically)
   - ✅ **Preload sample dataset:** You can uncheck this (we don't need sample data)

4. **Click:** "Create Deployment" button (green button, bottom right)

5. **Wait:** Cluster creation takes 3-5 minutes

---

## ✅ Step 2: Create Database User (After Cluster is Created)

### Option A: If "Automate security setup" was checked:

MongoDB will create a user automatically. You'll need to:
1. Set a **Username** (e.g., `quantumsprout_admin`)
2. Set a **Password** (generate a strong one - SAVE THIS!)
3. Click "Create Database User"

### Option B: Manual User Creation:

1. Go to **"Database Access"** in left sidebar
2. Click **"Add New Database User"**
3. Select **"Password"** authentication method
4. **Username:** `quantumsprout_admin` (or your choice)
5. **Password:** 
   - Click "Autogenerate Secure Password" (SAVE THIS!)
   - Or create your own strong password
6. **Database User Privileges:** Select **"Read and write to any database"**
7. Click **"Add User"**

⚠️ **CRITICAL:** Save the username and password - you'll need them for the connection string!

---

## ✅ Step 3: Configure Network Access

1. Go to **"Network Access"** in left sidebar
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** button
   - This adds `0.0.0.0/0` (allows all IPs)
   - Perfect for Railway deployments
4. Click **"Confirm"**

**Why:** Railway uses dynamic IPs, so we need to allow all IPs.

**Alternative (more secure):** If you want to be more restrictive later, you can add specific Railway IP ranges, but `0.0.0.0/0` works fine for now.

---

## ✅ Step 4: Get Connection String

1. Go to **"Database"** in left sidebar
2. Click **"Connect"** button on your cluster
3. Choose **"Connect your application"**
4. **Driver:** Select "Python" (version 3.6 or later)
5. **Connection String** will be shown, something like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

6. **Copy this connection string**

---

## ✅ Step 5: Format Connection String for Railway

Take your connection string and modify it:

**Original:**
```
mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

**Modified (for Railway):**
```
mongodb+srv://quantumsprout_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```

**Changes made:**
1. Replace `<username>` with your actual username (e.g., `quantumsprout_admin`)
2. Replace `<password>` with your actual password
3. Add `/quantumsprout_production` before the `?` (this is your database name)

**Example (with real values):**
```
mongodb+srv://quantumsprout_admin:MySecurePass123@cluster0.abc123.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```

---

## ✅ Step 6: Add to Railway Variables

Copy your formatted connection string and add it to Railway:

1. Go to Railway Dashboard → **Variables** tab
2. Click **"New Variable"**
3. **Variable Name:** `MONGO_URL`
4. **Variable Value:** Paste your formatted connection string
5. Click **"Add"**

---

## 📋 Quick Checklist

After cluster is created:

- [ ] Database user created (username + password saved)
- [ ] Network access configured (0.0.0.0/0)
- [ ] Connection string obtained from "Connect" → "Connect your application"
- [ ] Connection string formatted with:
  - [ ] Username replaced
  - [ ] Password replaced
  - [ ] Database name added: `/quantumsprout_production`
- [ ] Connection string added to Railway as `MONGO_URL` variable

---

## 🔐 Security Notes

- ⚠️ **Never commit passwords to Git**
- ✅ **Save passwords in password manager**
- ✅ **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
- ✅ **Connection string is a secret** - treat it like a password

---

## 🎯 What to Do Right Now

1. **On current page:** Click "Create Deployment" (green button)
2. **Wait 3-5 minutes** for cluster to create
3. **Follow steps above** to set up user and get connection string
4. **Add to Railway** as MONGO_URL variable

---

## ❓ Troubleshooting

**Q: What if I forgot my password?**
- Go to "Database Access" → Edit user → Reset password

**Q: Connection string doesn't work?**
- Check username/password are correct
- Verify network access is 0.0.0.0/0
- Ensure database name is added: `/quantumsprout_production`

**Q: How do I test the connection?**
- Use MongoDB Compass (desktop app) to test
- Or test after Railway deployment with health check

---

**After MongoDB setup is complete, your backend will be able to connect!**

