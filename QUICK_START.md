# Quick Start Guide - Referrals System Testing

## 🚀 5-Minute Setup

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migration
alembic upgrade head

# Add RESEND_API_KEY to .env (optional for email testing)
echo "RESEND_API_KEY=your_key_here" >> .env
```

### 2. Run Unit Tests

```bash
cd backend

# Run all referral tests
pytest tests/test_referral_endpoints.py tests/test_referral_services.py -v

# Quick smoke test (just config and create endpoints)
pytest tests/test_referral_endpoints.py::TestReferralConfig::test_get_config_success -v
pytest tests/test_referral_endpoints.py::TestReferralCreate::test_create_referral_success -v
```

### 3. Add Referral Config to Organization

```sql
-- Run this SQL to add config to your test organization
UPDATE organizations 
SET preset_config = jsonb_set(
  COALESCE(preset_config, '{}'::jsonb),
  '{referral_config}',
  '{
    "types": ["Behavior", "Support"],
    "locations": {"options": ["Classroom", "Hallway", "Other"]},
    "time_of_day": {"options": ["Morning", "Afternoon", "Other"]},
    "behaviors": {"options": ["Disruption", "Tardy", "Defiance"]},
    "common_interventions": ["Parent Contact", "Counseling", "Detention"]
  }'::jsonb
)
WHERE id = 'your-org-id-here';
```

### 4. Test Frontend

```bash
cd frontend

# Start dev server (if not already running)
npm run dev

# Navigate to:
# http://localhost:3000/dashboard/organizations/YOUR_ORG_ID/referrals
```

---

## ✅ Quick Verification Checklist

### Backend Tests
- [ ] All tests pass: `pytest tests/test_referral_endpoints.py tests/test_referral_services.py`
- [ ] No import errors
- [ ] Migration applied successfully

### Frontend Testing
- [ ] Referrals page loads without errors
- [ ] Can click "Create Referral" button
- [ ] Student dropdown populates
- [ ] Form shows config-driven options
- [ ] Can submit referral
- [ ] Referral appears in list
- [ ] Can click "View" to see details
- [ ] Can add intervention
- [ ] PDF download works (or shows appropriate error if WeasyPrint not installed)

---

## 🎯 Minimal Test Flow

### 1. Create a Referral (via UI)

1. Go to: `/dashboard/organizations/{your-org-id}/referrals`
2. Click "Create Referral"
3. Select student: Any student from dropdown
4. Type: "Behavior"
5. Location: "Classroom"
6. Behaviors: Check "Disruption"
7. Description: "Test referral"
8. Click "Create Referral"

**Expected**: Success toast, form closes, referral appears in list

### 2. View Details

1. Click "View" on the created referral
2. Verify all information displays correctly
3. Click "PDF" button
4. Check if PDF downloads (may fail if WeasyPrint not installed - that's OK for now)

**Expected**: Detailed view loads, shows student info, incident details

### 3. Add Intervention

1. On referral detail page, click "Add Intervention"
2. Select "Parent Contact"
3. Description: "Called parent"
4. Status: "PLANNED"
5. Click "Add Intervention"

**Expected**: Success toast, intervention appears in list below

---

## 🐛 Quick Troubleshooting

### Tests Failing?

**Check migration:**
```bash
cd backend
alembic current  # Should show: e7a1b2c3d4f5
```

**If migration not applied:**
```bash
alembic upgrade head
```

### Frontend Errors?

**Check browser console** (F12)

**Common issues:**
- `useReferralConfig` returns null → Config not added to organization
- Students dropdown empty → No students in organization
- 403 errors → User not member of organization

### PDF Errors Expected?

If you see "PDF generation service is not available", that's normal if WeasyPrint isn't installed. The endpoint structure is correct, just missing the library.

**To install WeasyPrint (optional):**
```bash
# Ubuntu/Debian
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0

# Then reinstall
pip install weasyprint
```

---

## 📊 Expected Test Results

### Passing Tests (35+ total)

```
tests/test_referral_endpoints.py::TestReferralConfig::test_get_config_success PASSED
tests/test_referral_endpoints.py::TestReferralConfig::test_get_config_missing PASSED
tests/test_referral_endpoints.py::TestReferralCreate::test_create_referral_success PASSED
tests/test_referral_endpoints.py::TestReferralCreate::test_create_referral_with_other_location PASSED
tests/test_referral_endpoints.py::TestReferralCreate::test_create_referral_invalid_student PASSED
...
tests/test_referral_services.py::TestPDFService::test_generate_pdf_success PASSED
tests/test_referral_services.py::TestEmailService::test_send_email_success PASSED
...

=============================== XX passed in X.XXs ===============================
```

### Tests That May Show Warnings (OK)

- PDF/Email tests may show import warnings if libraries not installed
- Some tests mock external services (expected behavior)

---

## 🎉 Success Criteria

You're ready to move forward if:

1. ✅ All unit tests pass (or only fail on optional dependencies like WeasyPrint)
2. ✅ Frontend loads without console errors
3. ✅ Can create a referral via UI
4. ✅ Can view referral details
5. ✅ Can add interventions

---

## 📝 Next Steps After Verification

1. Add more test data (students, referrals)
2. Test edge cases (Other values, multiple interventions)
3. Test role-based access (staff vs admin)
4. Install WeasyPrint for PDF testing
5. Configure Resend for email testing
6. Add custom email templates (optional)

---

**Total Time**: ~10 minutes for basic verification  
**Required**: Backend dependencies, migration  
**Optional**: WeasyPrint, Resend API key

