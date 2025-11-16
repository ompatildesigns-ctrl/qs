# 🔐 Your MongoDB Atlas Credentials

## Save These Credentials NOW!

**⚠️ CRITICAL: Copy these before proceeding!**

### Username:
```
ompatildesigns_db_user
```

### Password:
```
oMIGENOBJ90KfPOh
```

### Cluster Name:
```
quantumsprout-cluster
```

---

## What to Do Next:

### 1. In MongoDB Atlas Modal (Right Now):
- ✅ Click "Copy" button next to password (or manually copy: `oMIGENOBJ90KfPOh`)
- ✅ Click "Create Database User"
- ✅ Click "Choose a connection method" → Select "Connect your application"
- ✅ Select "Python" driver → Copy connection string

### 2. Format Your Connection String:

**You'll get something like:**
```
mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

**Replace with your credentials:**
```
mongodb+srv://ompatildesigns_db_user:oMIGENOBJ90KfPOh@<your-cluster>.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```

**Replace `<your-cluster>` with your actual cluster address from MongoDB Atlas**

**Example (with real cluster address):**
```
mongodb+srv://ompatildesigns_db_user:oMIGENOBJ90KfPOh@cluster0.abc123.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```

### 3. Configure Network Access (IMPORTANT for Railway):

After getting connection string:
1. In MongoDB Atlas, go to "Network Access" (left sidebar)
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" button
4. This adds `0.0.0.0/0` (allows all IPs - needed for Railway)
5. Click "Confirm"

### 4. Add to Railway:

1. Go to Railway Dashboard → Variables tab
2. Click "New Variable"
3. **Name:** `MONGO_URL`
4. **Value:** Paste your formatted connection string
5. Click "Add"

---

## Connection String Template:

Once you have your cluster address, your connection string will be:

```
mongodb+srv://ompatildesigns_db_user:oMIGENOBJ90KfPOh@<CLUSTER_ADDRESS>/quantumsprout_production?retryWrites=true&w=majority
```

**Just replace `<CLUSTER_ADDRESS>` with your actual cluster from MongoDB Atlas!**

---

⚠️ **REMEMBER:** 
- Save this password in a password manager
- Never commit passwords to Git
- Connection string will be added to Railway as MONGO_URL

