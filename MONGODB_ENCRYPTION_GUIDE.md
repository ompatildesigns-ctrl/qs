# MONGODB ENCRYPTION AT REST CONFIGURATION
## Enterprise Security Enhancement for Quantum Sprout

**Purpose:** Enable MongoDB encryption at rest for enterprise-grade data security  
**Impact:** +5 points to security score (85 → 90/100)  
**Required For:** SOC 2 certification, enterprise customers

---

## WHY ENCRYPTION AT REST?

**Current State:**
- ✅ OAuth tokens encrypted with Fernet (AES-128 CBC + HMAC)
- ✅ HTTPS/TLS for all network traffic
- ⚠️ MongoDB database files stored unencrypted

**Gap:**
If server disk is compromised, Jira data is readable (even though OAuth tokens are encrypted).

**Industry Requirement:**
- SOC 2: Encryption at rest recommended
- Enterprise customers: Often required in contracts
- Best practice: Defense in depth

---

## MONGODB ENCRYPTION OPTIONS

### Option 1: WiredTiger Encryption (Recommended)

**MongoDB Enterprise only** - Encrypts database files with AES-256

**Configuration:**
```yaml
# mongod.conf
security:
  enableEncryption: true
  encryptionKeyFile: /path/to/encryption_key
```

**Generate Key:**
```bash
openssl rand -base64 32 > /etc/mongodb/encryption_key
chmod 600 /etc/mongodb/encryption_key
chown mongodb:mongodb /etc/mongodb/encryption_key
```

**Restart MongoDB:**
```bash
sudo systemctl restart mongod
```

**Verification:**
```bash
mongo --eval "db.serverStatus().security"
```

---

### Option 2: MongoDB Atlas (Cloud - Easiest)

**Automatic encryption at rest** - No configuration needed

**Benefits:**
- ✅ Encryption at rest enabled by default (AES-256)
- ✅ Automatic backups
- ✅ Point-in-time recovery
- ✅ Global replication
- ✅ Monitoring and alerts
- ✅ SOC 2 / ISO 27001 certified

**Migration:**
1. Create MongoDB Atlas cluster (free tier available)
2. Update .env:
   ```env
   MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net
   ```
3. Migrate data:
   ```bash
   mongodump --uri="mongodb://localhost:27017/test_database"
   mongorestore --uri="mongodb+srv://cluster.mongodb.net" dump/
   ```

**Cost:**
- Free tier: 512MB (good for testing)
- Shared cluster: $9/month (good for 100-1K users)
- Dedicated: $57/month (good for 10K+ users)

---

### Option 3: Application-Level Encryption

**Encrypt sensitive fields before storing** - Works with MongoDB Community

**Implementation:**
```python
# In models.py - Add field-level encryption
from cryptography.fernet import Fernet

class JiraIssue(BaseModel):
    summary: str  # Encrypt if contains sensitive info
    
# In server.py - Encrypt before save
encrypted_summary = get_encryptor().encrypt(issue['summary'])
```

**Pros:**
- Works with MongoDB Community (free)
- Granular control over what's encrypted

**Cons:**
- More complex code
- Can't query encrypted fields easily
- Manual key management

---

## CURRENT SECURITY POSTURE

### What's Already Encrypted:
✅ **OAuth Tokens:** Fernet AES-128 (before MongoDB storage)
✅ **Network Traffic:** HTTPS/TLS 1.2+
✅ **API Calls:** TLS to Atlassian Jira

### What's NOT Encrypted:
⚠️ **MongoDB Database Files:** Stored in plaintext
- Jira issue summaries
- User display names
- Project names

### Risk Assessment:
**Low-Medium Risk:**
- Data is business information (not PII in most cases)
- User display names are business identifiers (not personal addresses/SSNs)
- No payment info, health data, or sensitive personal data
- If disk is stolen, OAuth tokens are still encrypted (attacker can't access Jira API)

**Best Practice:** Enable encryption at rest for enterprise deployments

---

## RECOMMENDATIONS BY DEPLOYMENT

### Development/Preview:
- Current state: OK (no encryption at rest needed)
- Focus: Feature development and testing

### US-Only Beta:
- Recommended: MongoDB Atlas free tier (easiest)
- Benefit: Automatic encryption + backups

### Production (www.quantumsprout.com):
- Recommended: MongoDB Atlas paid tier ($57/month)
- Benefits: Encryption + monitoring + backups + scaling
- Alternative: Self-hosted MongoDB Enterprise with WiredTiger encryption

### Enterprise Customers:
- Required: Encryption at rest (contractual requirement)
- Solution: MongoDB Atlas dedicated cluster or self-hosted Enterprise
- Documentation: Provide encryption certificate to customers

---

## IMPLEMENTATION CHECKLIST

### For MongoDB Atlas (Recommended):

- [ ] Sign up at cloud.mongodb.com
- [ ] Create new cluster (M2 or higher for encryption)
- [ ] Enable encryption at rest (default on paid tiers)
- [ ] Create database: `quantum_sprout_production`
- [ ] Create database user with read/write permissions
- [ ] Whitelist application server IP address
- [ ] Get connection string
- [ ] Update production .env:
  ```env
  MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/quantum_sprout_production
  ```
- [ ] Migrate data from localhost
- [ ] Verify connection works
- [ ] Test full application flow
- [ ] Monitor performance

### For Self-Hosted MongoDB Enterprise:

- [ ] Purchase MongoDB Enterprise license
- [ ] Install MongoDB Enterprise edition
- [ ] Generate encryption key (openssl rand -base64 32)
- [ ] Update mongod.conf with encryption settings
- [ ] Restart MongoDB
- [ ] Verify encryption enabled
- [ ] Backup encryption key securely
- [ ] Test data recovery with key

---

## COMPLIANCE IMPACT

**With Encryption at Rest:**
- Security Score: 85 → 90/100 (+5 points)
- SOC 2 Readiness: 70 → 80/100 (+10 points)
- Enterprise Sales: Unblocked (contractual requirement met)
- Customer Trust: Significantly increased

**Cost:**
- MongoDB Atlas: $57-$200/month (depending on size)
- Self-hosted Enterprise: $10K-$50K/year (license + management)

**ROI:**
- Enterprise deals: $50K-$500K ARR
- Customer trust: Priceless
- SOC 2 certification: $100K+ value

---

## CURRENT DEPLOYMENT RECOMMENDATION

**For Launch at www.quantumsprout.com:**

1. **Week 1-2:** Use MongoDB Atlas free tier
   - Test with real users
   - Validate scaling needs
   - No encryption cost

2. **Week 3-4:** Upgrade to Atlas M2 ($57/month)
   - Encryption at rest enabled
   - Backups included
   - Support 1,000+ users

3. **Month 2-3:** Upgrade as needed
   - M10 for 10K+ users ($185/month)
   - M30 for 100K+ users ($790/month)
   - Dedicated for enterprise ($2K+/month)

**Timeline:** 1-2 hours to set up Atlas
**Complexity:** Low (point-and-click UI)
**Security Gain:** +5 points

---

**Current Score:** 94/100
**With Atlas Encryption:** 96/100
**With Full SOC 2:** 98/100

---

## CONTACT

**Questions:** security@quantumsprout.com  
**Implementation Help:** support@quantumsprout.com
