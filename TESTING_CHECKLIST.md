# 🧪 Quantum Sprout Production Testing Checklist

Use this checklist to verify your deployment is working correctly.

---

## ✅ Pre-Deployment Checks

- [ ] All environment variables set in platform
- [ ] MongoDB Atlas cluster created and accessible
- [ ] Database user created with correct permissions
- [ ] Network access configured (IP whitelist)
- [ ] Secrets generated (JWT_SECRET_KEY)
- [ ] Code pushed to Git repository
- [ ] Repository connected to deployment platform

---

## 🌐 DNS & Domain Tests

### DNS Configuration
- [ ] DNS records added in Squarespace
- [ ] DNS propagated (check with `dig quantumsprout.com`)
- [ ] Frontend domain resolves correctly
- [ ] Backend domain resolves correctly (if using subdomain)
- [ ] No DNS errors in browser console

### SSL/HTTPS
- [ ] HTTPS certificate active (lock icon in browser)
- [ ] HTTP redirects to HTTPS
- [ ] Certificate valid (no warnings)
- [ ] Mixed content warnings resolved (if any)

---

## 🎨 Frontend Tests

### Landing Page
- [ ] Page loads at https://quantumsprout.com
- [ ] No 404 errors
- [ ] Page title shows "Quantum Sprout" (not "Emergent")
- [ ] Hero section displays correctly
- [ ] "Connect Jira" button visible and clickable
- [ ] Footer displays with correct email addresses
- [ ] No JavaScript errors in console (F12 → Console)
- [ ] Page is responsive (test mobile/tablet/desktop)

### Branding Verification
- [ ] No "Emergent" branding visible
- [ ] All email addresses use @quantumsprout.com
- [ ] Company name shows "Quantum Sprout Inc."
- [ ] Copyright shows "© 2025 Quantum Sprout"
- [ ] Legal pages reference Quantum Sprout

### Performance
- [ ] Page loads in < 3 seconds
- [ ] No slow network requests (check Network tab)
- [ ] Images optimized and loading
- [ ] No console warnings about performance

---

## 🔌 Backend API Tests

### Health Check
```bash
curl https://api.quantumsprout.com/api/health
```
- [ ] Returns `{"status":"ok"}` or similar
- [ ] Response time < 200ms
- [ ] No 404 or 500 errors

### CORS Configuration
```bash
curl -H "Origin: https://quantumsprout.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://api.quantumsprout.com/api/health
```
- [ ] CORS headers present
- [ ] `Access-Control-Allow-Origin` includes frontend URL
- [ ] `Access-Control-Allow-Credentials: true`

### API Endpoints
- [ ] `/api/health` - Health check works
- [ ] `/api/auth/jira/authorize` - OAuth authorization endpoint
- [ ] `/api/auth/jira/callback` - OAuth callback endpoint
- [ ] `/api/jira/sync` - Sync endpoint (requires auth)
- [ ] `/api/analytics/financial` - Financial analytics (requires auth)
- [ ] All endpoints return expected status codes

### Response Times
- [ ] Health check: < 100ms
- [ ] OAuth endpoints: < 500ms
- [ ] Analytics endpoints: < 1000ms
- [ ] Sync endpoint: < 5000ms (background job)

---

## 🔐 OAuth Flow Tests

### Complete OAuth Flow
1. [ ] Navigate to https://quantumsprout.com
2. [ ] Click "Connect Jira" button
3. [ ] Redirects to Atlassian login page
4. [ ] Atlassian authorization page displays correctly
5. [ ] Log in with Atlassian account
6. [ ] Grant permissions (check all required scopes)
7. [ ] Redirects back to quantumsprout.com
8. [ ] URL includes `?oauth_success=true`
9. [ ] URL includes `connection_id` parameter
10. [ ] URL includes `cloud_id` parameter
11. [ ] "Syncing your data..." progress bar appears
12. [ ] Sync completes successfully (30-60 seconds)
13. [ ] Dashboard loads after sync

### OAuth Error Handling
- [ ] Invalid callback URL shows appropriate error
- [ ] User denial shows appropriate message
- [ ] Network errors handled gracefully
- [ ] Backend logs show OAuth flow steps

### OAuth Configuration Verification
- [ ] `JIRA_REDIRECT_URI` matches Atlassian console exactly
- [ ] No trailing slashes in callback URL
- [ ] HTTPS used (not HTTP)
- [ ] `JIRA_CLIENT_ID` matches Atlassian app
- [ ] `JIRA_CLIENT_SECRET` is correct

---

## 📊 Dashboard Tests

### Overview Tab
- [ ] Tab loads without errors
- [ ] Key metrics display (if data available)
- [ ] No infinite loading spinners
- [ ] Data refreshes correctly

### Financial Impact Tab
- [ ] Cost of Delay breakdown displays
- [ ] $ amounts show correctly (not NaN or 0)
- [ ] Team ROI percentages display
- [ ] Time period filters work (30d, 60d, 90d, 180d)
- [ ] Data changes when filter selected
- [ ] Charts/graphs render correctly

### Team Comparison Tab
- [ ] Team data displays
- [ ] Comparison metrics show
- [ ] No errors loading team data

### Historical Trends Tab
- [ ] Charts display correctly
- [ ] Time series data loads
- [ ] Filters work as expected

### Accountability Tab
- [ ] Assignee data displays
- [ ] Issue assignments show
- [ ] No errors loading data

### Communication Tab
- [ ] Bottleneck data displays
- [ ] Communication metrics show
- [ ] No errors loading data

### Settings Tab
- [ ] Connection info displays
- [ ] Last sync time shows
- [ ] "Sync Now" button works (if available)
- [ ] "Disconnect" button works (if available)

### Navigation
- [ ] All tabs navigate correctly
- [ ] URL updates when switching tabs
- [ ] Browser back/forward buttons work
- [ ] No navigation errors

---

## 💰 Financial Features Tests

### Cost of Delay
- [ ] Total Cost of Delay displays
- [ ] Breakdown by category shows (stale, unassigned, etc.)
- [ ] $ amounts are realistic
- [ ] Currency formatting correct ($7.58M format)

### Team ROI
- [ ] ROI percentages display
- [ ] Team names show correctly
- [ ] Calculations appear accurate
- [ ] No division by zero errors

### Time Period Filters
- [ ] 30-day filter works
- [ ] 60-day filter works
- [ ] 90-day filter works
- [ ] 180-day filter works
- [ ] Data updates when filter changes
- [ ] Loading states show during filter change

---

## ⚡ One-Click Actions Tests

### Preview & Execute Modal
- [ ] "Preview & Execute" button visible on Financial Impact tab
- [ ] Click opens modal dialog
- [ ] Modal displays correctly (not cut off)
- [ ] ROI preview card shows $ recovery amount
- [ ] Assignment plan shows real issue keys (PDT-xxx format)
- [ ] Issue counts display correctly

### Dry Run
- [ ] "Dry Run" button works
- [ ] Success toast appears after dry run
- [ ] No errors in console
- [ ] Backend logs show dry run execution

### Execute Action
- [ ] "Execute Now" button visible (don't click in testing)
- [ ] Button disabled if no actions available
- [ ] Confirmation dialog appears (if implemented)
- [ ] Modal closes after action

### Error Handling
- [ ] Network errors handled gracefully
- [ ] Backend errors show user-friendly message
- [ ] No JavaScript errors in console

---

## 🔒 Security Tests

### Secrets Protection
- [ ] View page source - no secrets exposed
- [ ] Check browser DevTools - no secrets in localStorage (except JWT token)
- [ ] Network tab - no secrets in request headers (except Authorization)
- [ ] Backend logs - no secrets logged

### Authentication
- [ ] JWT tokens stored securely (localStorage)
- [ ] Tokens not visible in URLs
- [ ] Tokens expire correctly (after 7 days)
- [ ] Invalid tokens rejected

### CORS Protection
- [ ] Unauthorized domains blocked
- [ ] Only frontend domain can access API
- [ ] CORS errors show in console for blocked domains

### HTTPS Enforcement
- [ ] HTTP redirects to HTTPS
- [ ] No mixed content warnings
- [ ] SSL certificate valid
- [ ] Certificate chain complete

### MongoDB Security
- [ ] Connection string not exposed
- [ ] Database credentials not in logs
- [ ] IP whitelist configured correctly
- [ ] Database user has minimal required permissions

---

## 📈 Performance Tests

### Frontend Performance
- [ ] Initial page load < 3 seconds
- [ ] Dashboard loads < 2 seconds
- [ ] Tab switching < 500ms
- [ ] No memory leaks (check over time)
- [ ] No excessive API calls

### Backend Performance
- [ ] Health check < 100ms
- [ ] OAuth endpoints < 500ms
- [ ] Analytics endpoints < 1000ms
- [ ] Sync job completes in reasonable time
- [ ] No database connection timeouts

### Database Performance
- [ ] Queries execute quickly
- [ ] Indexes used (check MongoDB logs)
- [ ] No slow queries (> 1 second)
- [ ] Connection pool working correctly

---

## 🗄️ Database Tests

### Connection
- [ ] MongoDB connection successful
- [ ] No connection errors in logs
- [ ] Connection pool working
- [ ] Reconnection works after timeout

### Data Sync
- [ ] Issues sync correctly
- [ ] Users sync correctly
- [ ] Projects sync correctly
- [ ] Statuses sync correctly
- [ ] Data persists after sync

### Data Integrity
- [ ] No duplicate records
- [ ] Foreign key relationships maintained
- [ ] Data types correct
- [ ] Timestamps updated correctly

---

## 📱 Responsive Design Tests

### Mobile (< 768px)
- [ ] Layout adapts correctly
- [ ] Navigation works (hamburger menu if applicable)
- [ ] Text readable without zooming
- [ ] Buttons/touch targets adequate size
- [ ] No horizontal scrolling

### Tablet (768px - 1024px)
- [ ] Layout adapts correctly
- [ ] Navigation works
- [ ] Content readable
- [ ] Forms usable

### Desktop (> 1024px)
- [ ] Full layout displays
- [ ] All features accessible
- [ ] No wasted space
- [ ] Multi-column layouts work

---

## 🔍 Browser Compatibility Tests

Test in multiple browsers:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

For each browser:
- [ ] Page loads correctly
- [ ] OAuth flow works
- [ ] Dashboard displays
- [ ] No console errors
- [ ] Features work as expected

---

## 📝 Logging & Monitoring Tests

### Backend Logs
- [ ] Logs accessible in platform dashboard
- [ ] Logs show request/response details
- [ ] Errors logged with stack traces
- [ ] No sensitive data in logs
- [ ] Log rotation working (if configured)

### Frontend Logs
- [ ] Console logs helpful for debugging
- [ ] No excessive logging in production
- [ ] Error boundaries catch React errors
- [ ] Network errors logged

### Error Tracking (if Sentry configured)
- [ ] Errors sent to Sentry
- [ ] Error context included
- [ ] User information included (if applicable)
- [ ] No duplicate errors

---

## 🚨 Error Handling Tests

### Network Errors
- [ ] Offline mode handled gracefully
- [ ] Slow network handled (timeouts)
- [ ] Connection errors show user-friendly message
- [ ] Retry logic works (if implemented)

### API Errors
- [ ] 400 errors handled
- [ ] 401 errors handled (redirect to login)
- [ ] 403 errors handled
- [ ] 404 errors handled
- [ ] 500 errors handled gracefully
- [ ] Rate limit errors handled

### User Errors
- [ ] Invalid input validated
- [ ] Error messages clear and helpful
- [ ] Forms prevent invalid submissions
- [ ] Confirmation dialogs for destructive actions

---

## 🔄 Sync Tests

### Manual Sync
- [ ] "Sync Now" button works (if available)
- [ ] Progress indicator shows
- [ ] Sync completes successfully
- [ ] Data updates after sync
- [ ] Last sync time updates

### Background Sync (if configured)
- [ ] Scheduled sync runs (check logs)
- [ ] Sync completes successfully
- [ ] No errors in scheduled sync
- [ ] Data stays fresh

### Sync Error Handling
- [ ] Rate limit errors handled
- [ ] Network errors handled
- [ ] Invalid token errors handled
- [ ] User notified of sync failures

---

## ✅ Final Verification

### End-to-End User Flow
1. [ ] User visits quantumsprout.com
2. [ ] User clicks "Connect Jira"
3. [ ] User authorizes Jira connection
4. [ ] User returns to app
5. [ ] Data syncs automatically
6. [ ] Dashboard displays with data
7. [ ] User navigates through tabs
8. [ ] User views financial metrics
9. [ ] User previews actions
10. [ ] User can disconnect Jira (if needed)

### Production Readiness
- [ ] All critical tests passed
- [ ] No blocking errors
- [ ] Performance acceptable
- [ ] Security verified
- [ ] Monitoring configured
- [ ] Documentation complete
- [ ] Team trained (if applicable)

---

## 📊 Test Results Summary

**Date:** _______________

**Tester:** _______________

**Environment:** Production

**Overall Status:** ☐ Pass  ☐ Fail  ☐ Partial

**Critical Issues Found:** _______________

**Non-Critical Issues Found:** _______________

**Notes:** _______________

---

**✅ If all tests pass, your deployment is production-ready!**

**❌ If any critical tests fail, refer to DEPLOYMENT_GUIDE.md troubleshooting section.**

