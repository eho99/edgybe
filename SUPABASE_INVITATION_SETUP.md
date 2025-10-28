# Supabase Invitation Flow Setup Guide

## **Critical Configuration Steps**

### **1. Supabase Dashboard Configuration**

#### **Site URL Setup**
- Go to **Authentication → Settings → Site URL**
- **Development**: Set to `http://localhost:3000`
- **Production**: Set to your frontend domain (e.g., `https://my-app.com`)

#### **Redirect URLs**
- Go to **Authentication → Settings → Redirect URLs**
- Add the following URLs:
  - `http://localhost:3000/invite-profile-completion` (development)
  - `https://your-domain.com/invite-profile-completion` (production)
  - `http://localhost:3000/test-invite` (for debugging)

### **2. Email Templates**
- Go to **Authentication → Templates**
- Customize the **"Invite"** email template
- The template should include a link that redirects to your Site URL
- Supabase will automatically append the invitation token

### **3. SMTP Configuration (Production)**
- Go to **Authentication → Settings → SMTP Settings**
- Configure with your email service provider
- For development, Supabase uses Inbucket at `http://localhost:54324`

## **How Supabase Invitation Flow Works**

### **Step-by-Step Process**

1. **Admin sends invitation** via your backend API
2. **Supabase sends email** with invitation link
3. **User clicks link** → redirected to Site URL
4. **Supabase processes invitation** → creates user account
5. **Supabase redirects** to your specified redirect URL
6. **Your frontend detects session** → shows profile completion

### **Key Points**

- **Site URL** is where Supabase redirects users after processing invitation
- **Redirect URLs** are additional allowed destinations
- **Invitation token** is consumed by Supabase, not passed to your app
- **Session is created automatically** when invitation is accepted
- **Timing issues** may occur - session might not be immediately available

## **Troubleshooting**

### **Common Issues**

1. **"No session found"**
   - Check Site URL configuration
   - Verify redirect URLs are added
   - Wait for session to be created (can take 1-2 seconds)

2. **"Redirect not allowed"**
   - Add your redirect URL to allowed list
   - Check URL format (no trailing slash)

3. **"Session not detected"**
   - Use the improved invitation page with retry logic
   - Check browser console for errors
   - Verify Supabase client configuration

### **Debug Steps**

1. **Use test page**: Visit `/test-invite` to see detailed logs
2. **Check console**: Look for Supabase auth errors
3. **Verify configuration**: Ensure Site URL matches your frontend
4. **Test email**: Check invitation email format and links

## **Testing the Flow**

### **Manual Test Process**

1. **Start both servers**:
   ```bash
   # Backend
   cd backend && uvicorn app.main:app --reload
   
   # Frontend  
   cd frontend && npm run dev
   ```

2. **Send invitation** from admin dashboard

3. **Check email** for invitation link

4. **Click invitation link** and watch debug logs

5. **Verify session creation** and profile completion

### **Expected Behavior**

- User clicks invitation link
- Redirected to Site URL (localhost:3000)
- Supabase processes invitation
- Session is created automatically
- User sees profile completion page
- After completing profile, redirected to dashboard

## **Environment Variables**

### **Frontend (.env.local)**
```env
NEXT_PUBLIC_SUPABASE_URL="https://your-project-id.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-supabase-anon-key"
NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
```

### **Backend (.env)**
```env
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_SERVICE_KEY="your-supabase-service-role-key"
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.your-project-id.supabase.co:5432/postgres"
SUPABASE_JWT_SECRET="your-supabase-jwt-secret"
```

## **Next Steps After Setup**

1. **Test invitation flow** with debug page
2. **Verify session creation** works consistently
3. **Test profile completion** end-to-end
4. **Deploy to production** with proper URLs
5. **Monitor logs** for any issues

## **Production Considerations**

- **Use HTTPS** for all URLs
- **Set proper Site URL** for your domain
- **Configure SMTP** for email delivery
- **Monitor invitation success rates**
- **Set up error tracking** for failed invitations
