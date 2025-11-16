# ⚠️ OAuth Callback URL - NEEDS FIX!

## 🔴 Current Issue

Your OAuth callback URL is **WRONG**:

**Current (INCORRECT):**
```
https://easygoing-kindness-production-cd75.up.railway.app/api/health
```

**Should be:**
```
https://easygoing-kindness-production-cd75.up.railway.app/api/auth/jira/callback
```

---

## ✅ Fix It Now

### In Atlassian Developer Console (where you are):

1. **Find the "Callback URL *" field** (you can see it on the page)

2. **Replace the current URL:**
   - **Delete:** `https://easygoing-kindness-production-cd75.up.railway.app/api/health`
   - **Enter:** `https://easygoing-kindness-production-cd75.up.railway.app/api/auth/jira/callback`

3. **Click "Save changes"** button

4. **Verify:**
   - The authorization URL generator should update
   - The `redirect_uri` in the authorization URL should show `/api/auth/jira/callback`

---

## 📋 Correct Callback URL

**Copy this exactly:**
```
https://easygoing-kindness-production-cd75.up.railway.app/api/auth/jira/callback
```

**Important:**
- ✅ Must end with `/api/auth/jira/callback`
- ❌ NOT `/api/health`
- ❌ NO trailing slash

---

## ✅ After Fixing

Once you update and save:

1. The callback URL will be correct
2. OAuth flow will work properly
3. Users can connect their Jira accounts

---

## 🔍 Why This Matters

The callback URL must match exactly:
- ✅ Your backend route: `/api/auth/jira/callback` (defined in server.py)
- ✅ Atlassian Developer Console: Authorization callback URL
- ✅ Railway environment variable: `JIRA_REDIRECT_URI`

All three must be **identical**!

---

## ⚡ Action Required NOW

**In Atlassian Developer Console:**

1. Click in the "Callback URL *" field
2. Replace `/api/health` with `/api/auth/jira/callback`
3. Click "Save changes"
4. Verify it's saved correctly

---

**Fix this now - OAuth won't work until callback URL is correct!**

