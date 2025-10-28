# Test Invitation Flow

## **Quick Test Script**

Use this step-by-step process to test the invitation flow:

### **1. Start Development Servers**

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### **2. Send Test Invitation**

1. **Open browser** → `http://localhost:3000`
2. **Login as admin** user
3. **Go to dashboard** → find invitation form
4. **Enter test email** (use a real email you can access)
5. **Click "Send Invitation"**
6. **Check console** for success message

### **3. Check Email**

1. **Open email client** (or Inbucket at `http://localhost:54324`)
2. **Find invitation email**
3. **Note the invitation link** format
4. **Click the invitation link**

### **4. Debug the Flow**

1. **Open debug page** → `http://localhost:3000/test-invite`
2. **Click invitation link** in email
3. **Watch debug logs** for:
   - URL parameters
   - Session creation
   - Auth state changes
   - Any errors

### **5. Test Profile Completion**

1. **After clicking invitation link**
2. **Should redirect** to profile completion page
3. **Enter full name**
4. **Submit form**
5. **Should redirect** to dashboard

## **Expected Results**

### **✅ Success Indicators**
- Invitation email sent successfully
- Invitation link redirects to Site URL
- Session created automatically
- Profile completion page loads
- User can complete profile
- Redirected to dashboard after completion

### **❌ Failure Indicators**
- No invitation email received
- "Redirect not allowed" error
- "No session found" error
- Stuck on login page
- Profile completion fails

## **Common Issues & Solutions**

### **Issue: "Redirect not allowed"**
**Solution**: Add redirect URL to Supabase dashboard
- Go to Authentication → Settings → Redirect URLs
- Add: `http://localhost:3000/invite-profile-completion`

### **Issue: "No session found"**
**Solution**: Check Site URL configuration
- Go to Authentication → Settings → Site URL
- Set to: `http://localhost:3000`

### **Issue: Email not received**
**Solution**: Check SMTP settings or use Inbucket
- Development: Check `http://localhost:54324`
- Production: Configure SMTP settings

### **Issue: Session timing problems**
**Solution**: Use improved invitation page with retry logic
- The updated page waits for session creation
- Retries multiple times with delays
- Handles timing issues automatically

## **Debug Information**

### **What to Look For**

1. **URL Structure**: 
   - Should redirect to Site URL first
   - Then to redirect URL
   - No invitation token in final URL

2. **Session Creation**:
   - Session should be created automatically
   - User should be authenticated
   - No manual login required

3. **Auth State Changes**:
   - Should see "SIGNED_IN" event
   - Session should contain user data
   - No auth errors in console

### **Console Logs to Check**

```javascript
// Look for these in browser console:
"Processing invitation..."
"Checking for session (attempt 1/5)..."
"Successfully found session for user: user@example.com"
"Auth state change: SIGNED_IN"
```

## **Production Testing**

### **Before Going Live**

1. **Update URLs** in Supabase dashboard:
   - Site URL: `https://your-domain.com`
   - Redirect URLs: `https://your-domain.com/invite-profile-completion`

2. **Configure SMTP** for email delivery

3. **Test with real email** addresses

4. **Monitor logs** for any issues

5. **Verify HTTPS** is working properly

## **Troubleshooting Commands**

### **Check Supabase Configuration**
```bash
# Verify environment variables
echo $NEXT_PUBLIC_SUPABASE_URL
echo $NEXT_PUBLIC_SUPABASE_ANON_KEY
```

### **Check Backend Logs**
```bash
# Look for invitation service logs
tail -f backend/logs/app.log
```

### **Check Frontend Console**
```bash
# Open browser dev tools
# Check Console tab for errors
# Check Network tab for failed requests
```

## **Success Criteria**

The invitation flow is working correctly when:

- ✅ Admin can send invitations
- ✅ Users receive invitation emails
- ✅ Clicking invitation link creates session
- ✅ Users can complete profiles
- ✅ Users are redirected to dashboard
- ✅ No manual login required
- ✅ No "redirect not allowed" errors
- ✅ No session timing issues
