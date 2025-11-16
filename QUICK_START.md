# 🚀 Quantum Sprout - Quick Start Deployment

**Get your app live in under 30 minutes!**

---

## ⚡ Quick Deployment Steps

### 1. Generate Secrets (2 minutes)

```bash
# Run the secret generation script
cd /Users/ompatil/Desktop/QuantumSprout
python3 scripts/generate-secrets.py

# Or use the shell script
bash scripts/generate-secrets.sh
```

**Save the output** - you'll need `JWT_SECRET_KEY` for backend.

### 2. Set Up MongoDB Atlas (5 minutes)

1. Go to https://cloud.mongodb.com
2. Create free account
3. Create M0 Free cluster
4. Create database user (save username/password!)
5. Add IP whitelist: `0.0.0.0/0` (allow all)
6. Get connection string:
   ```
   mongodb+srv://<username>:<password>@cluster.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
   ```

### 3. Deploy Backend to Railway (10 minutes)

1. **Sign up:** https://railway.app (use GitHub)
2. **Create project:** New Project → Deploy from GitHub
3. **Select repo:** Choose QuantumSprout repository
4. **Set root:** `backend` folder
5. **Add environment variables:**

   ```env
   MONGO_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
   DB_NAME=quantumsprout_production
   JIRA_CLIENT_ID=RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg
   JIRA_CLIENT_SECRET=ATOAwGM94of8TKIFcKndcob-3QOoYjuOaBu7b9RYLGyz02fHDdYlhjt29gg1vTtjJJ8988AF6550
   JIRA_ENC_KEY=GGDbQ4i49uRqSyo2YIfTNUIs5WOlUlQXGFY6ods7JuQ=
   JIRA_REDIRECT_URI=https://<YOUR_RAILWAY_URL>/api/auth/jira/callback
   FRONTEND_URL=https://quantumsprout.com
   CORS_ORIGINS=https://quantumsprout.com,http://localhost:3000
   JWT_SECRET_KEY=<PASTE_GENERATED_SECRET>
   ```

6. **Deploy:** Railway auto-detects Python and deploys
7. **Copy URL:** Railway provides URL like `https://quantumsprout-production.up.railway.app`
8. **Update JIRA_REDIRECT_URI:** Replace `<YOUR_RAILWAY_URL>` with actual URL

### 4. Deploy Frontend to Vercel (5 minutes)

1. **Sign up:** https://vercel.com (use GitHub)
2. **Import project:** Add New Project → Import GitHub repo
3. **Configure:**
   - Framework: Create React App
   - Root Directory: `frontend`
   - Build Command: `yarn build` (or `npm run build`)
   - Output Directory: `build`
4. **Add environment variable:**
   ```
   REACT_APP_BACKEND_URL=https://<YOUR_RAILWAY_URL>
   ```
   (Use the Railway URL from step 3)
5. **Deploy:** Click Deploy
6. **Copy URL:** Vercel provides URL like `https://quantumsprout.vercel.app`

### 5. Configure DNS (5 minutes)

**In Squarespace DNS:**

1. Add CNAME record:
   ```
   Type: CNAME
   Host: www
   Value: cname.vercel-dns.com
   ```

2. Add A record (Vercel will provide IPs):
   ```
   Type: A
   Host: @
   Value: 76.76.21.21
   ```

3. Wait 5-60 minutes for DNS propagation

### 6. Update OAuth Callback (2 minutes)

1. Go to https://developer.atlassian.com/console/myapps/
2. Find app with Client ID: `RNFKijJKbUERvmQoyjrwKcjtmwtPj5Gg`
3. Update Authorization Callback URL:
   ```
   https://<YOUR_RAILWAY_URL>/api/auth/jira/callback
   ```
4. Save changes

### 7. Test! (5 minutes)

1. Visit https://quantumsprout.com
2. Click "Connect Jira"
3. Authorize connection
4. Verify dashboard loads

**Done! 🎉**

---

## 🔧 Troubleshooting

**OAuth not working?**
- Check `JIRA_REDIRECT_URI` matches Atlassian console exactly
- Verify backend URL is correct
- Check backend logs for errors

**Frontend can't connect to backend?**
- Verify `REACT_APP_BACKEND_URL` is set correctly
- Check CORS configuration
- Test backend health: `curl https://<backend-url>/api/health`

**Database connection fails?**
- Verify MongoDB IP whitelist includes `0.0.0.0/0`
- Check connection string format
- Verify username/password are correct

---

## 📚 Full Documentation

For detailed instructions, see:
- **DEPLOYMENT_GUIDE.md** - Complete deployment guide
- **TESTING_CHECKLIST.md** - Comprehensive testing checklist

---

## 💰 Cost Estimate

- **Frontend (Vercel):** FREE
- **Backend (Railway):** $5/month
- **Database (MongoDB Atlas):** FREE
- **Total:** ~$5/month

---

**Need help? Check DEPLOYMENT_GUIDE.md for detailed instructions!**

