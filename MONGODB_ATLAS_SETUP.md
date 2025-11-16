# 🗄️ MongoDB Atlas Connection String Setup

## How to Get Your MongoDB Atlas Connection String

### Step 1: Create MongoDB Atlas Account (if not done)
1. Go to https://cloud.mongodb.com
2. Sign up for free account
3. Create M0 Free cluster (free tier)

### Step 2: Create Database User
1. Go to "Database Access" → "Add New Database User"
2. Username: `quantumsprout_admin` (or your choice)
3. Password: Generate secure password (SAVE THIS!)
4. Database User Privileges: "Read and write to any database"
5. Click "Add User"

### Step 3: Configure Network Access
1. Go to "Network Access" → "Add IP Address"
2. Click "Allow Access from Anywhere" (0.0.0.0/0)
   - Or add specific IPs if you prefer
3. Click "Confirm"

### Step 4: Get Connection String
1. Go to "Database" → Click "Connect"
2. Choose "Connect your application"
3. Copy the connection string
4. It will look like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace:
   - `<username>` with your database user (e.g., `quantumsprout_admin`)
   - `<password>` with your database user password
   - Add database name: `/quantumsprout_production` before `?`

### Final Connection String Format:
```
mongodb+srv://quantumsprout_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```

**Example:**
```
mongodb+srv://quantumsprout_admin:MySecurePass123@cluster0.abc123.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```

⚠️ **IMPORTANT:** 
- Replace `YOUR_PASSWORD` with your actual database user password
- Replace `cluster0.xxxxx.mongodb.net` with your actual cluster address
- Make sure to include `/quantumsprout_production` before the `?`

## Quick Checklist
- [ ] MongoDB Atlas account created
- [ ] M0 Free cluster created
- [ ] Database user created (username + password saved)
- [ ] Network access configured (0.0.0.0/0)
- [ ] Connection string copied
- [ ] Username replaced in connection string
- [ ] Password replaced in connection string
- [ ] Database name added: `/quantumsprout_production`

