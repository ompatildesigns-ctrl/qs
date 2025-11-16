# 📋 MongoDB Connection String - Format Template

## Your Connection String Template

Once you get your MongoDB Atlas connection string, format it like this:

```
mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@cluster0.XXXXX.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```

## Replace These Parts:

1. **YOUR_USERNAME** → Replace with your MongoDB username
   - Example: `quantumsprout_admin`

2. **YOUR_PASSWORD** → Replace with your MongoDB password
   - Example: `MySecurePass123`

3. **cluster0.XXXXX.mongodb.net** → Replace with your actual cluster address
   - Example: `cluster0.abc123.mongodb.net`
   - This comes from MongoDB Atlas "Connect" screen

4. **/quantumsprout_production** → This is your database name (keep as-is)

## Complete Example:

**If your details are:**
- Username: `quantumsprout_admin`
- Password: `SecurePass2024!`
- Cluster: `cluster0.abc123.mongodb.net`

**Your connection string would be:**
```
mongodb+srv://quantumsprout_admin:SecurePass2024!@cluster0.abc123.mongodb.net/quantumsprout_production?retryWrites=true&w=majority
```

## Quick Checklist:

- [ ] Username replaced (no `<username>` placeholder)
- [ ] Password replaced (no `<password>` placeholder)
- [ ] Cluster address replaced (from MongoDB Atlas)
- [ ] `/quantumsprout_production` added before the `?`
- [ ] No spaces in the connection string
- [ ] Special characters in password are URL-encoded if needed

## Special Characters in Password:

If your password contains special characters, they may need URL encoding:
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`
- `%` → `%25`
- `&` → `%26`
- `+` → `%2B`
- `/` → `%2F`
- `?` → `%3F`

**Example:** If password is `Pass@123`, use `Pass%40123` in connection string.

## Test Your Connection String:

After adding to Railway, test with:
```bash
curl https://easygoing-kindness-production-cd75.up.railway.app/api/health
```

If backend connects successfully, you'll see `{"status":"ok"}` or similar.

