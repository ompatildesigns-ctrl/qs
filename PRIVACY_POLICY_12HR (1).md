# Privacy Policy - Quantum Sprout

**Effective Date:** November 12, 2025  
**Last Updated:** November 12, 2025

---

## Privacy-First Data Policy

Quantum Sprout uses a **12-hour data lifecycle** model. We sync your Jira data when you login, display it in your dashboard, and delete it within 12 hours. Every login is a fresh sync.

**We do NOT store Jira personal data long-term.**

---

## 1. What We Collect

### Your Account Information (Permanent Storage)
- Email address (for login)
- Password (hashed with bcrypt)
- Full name (optional)
- Account creation date

### Jira Data (12-Hour Temporary Storage)
When you connect your Jira account, we temporarily sync:
- Issue summaries, keys, statuses, priorities
- Project names and keys
- User display names (assignees, reporters)
- Status definitions
- OAuth access tokens (encrypted)

**This data is deleted within 12 hours.**

### Technical Data
- IP address (for security)
- Browser type (for compatibility)
- Session data (for authentication)

---

## 2. How We Use Data

**During Your Session:**
- Display analytics dashboard
- Calculate Cost of Delay and Team ROI
- Show bottleneck insights
- Enable one-click actions

**After 12 Hours:**
- All Jira data deleted automatically
- OAuth tokens deleted
- Next login = fresh sync from Jira

**Permanent Storage:**
- Only your account credentials (email, password hash)
- No Jira business data stored permanently

---

## 3. Data Retention

**Account Data:** Retained until you delete your account
**Jira Data:** Maximum 12 hours, then auto-deleted
**OAuth Tokens:** Maximum 12 hours, then deleted
**Logs:** 24 hours for security

**We do NOT:**
- Store historical Jira data
- Keep archived analytics
- Build long-term profiles
- Aggregate data across users

**Privacy-First:** Fresh data on every login, nothing persists.

---

## 4. Third-Party Services

**Atlassian Jira:**
- We access your Jira via OAuth 2.0
- Read permissions only (read:jira-work)
- Write permissions for actions (write:jira-work)
- Subject to Atlassian Privacy Policy

**MongoDB:**
- Database hosting
- Temporary storage only (12 hours)
- Encrypted connections

**We Do NOT Share Data With:**
- Advertisers
- Data brokers
- Third-party analytics
- Marketing companies

---

## 5. Your Rights (GDPR & CCPA)

**Right to Access:**
Email privacy@quantumsprout.com - we'll provide your account data
(Note: Jira data auto-deletes within 12 hours, so export may be empty)

**Right to Delete:**
Settings → Delete Account - removes all data immediately

**Right to Disconnect:**
Settings → Disconnect Jira - removes Jira data immediately

**Data Portability:**
Minimal stored data makes export simple

---

## 6. Security

- HTTPS/TLS encryption for all traffic
- OAuth tokens encrypted with Fernet (AES-128)
- Passwords hashed with bcrypt
- JWT session tokens (7-day expiration)
- Multi-tenant data isolation

---

## 7. Children's Privacy

Not intended for users under 18.

---

## 8. Contact

**Privacy Officer:** privacy@quantumsprout.com  
**Security:** security@quantumsprout.com  
**GDPR:** gdpr@quantumsprout.com

---

## Summary

**Data Lifecycle:** 12 hours maximum  
**Storage:** Account credentials only (permanent), Jira data temporary  
**Philosophy:** Fresh sync on every login, no long-term storage  

© 2025 Quantum Sprout Inc.