# Referrals System Implementation Status

## ✅ Completed Backend Implementation

### 1. Database Schema & Models
**Status: Complete**

- ✅ Created Alembic migration (`e7a1b2c3d4f5_add_referrals_system_tables.py`)
  - `referrals` table with all required fields
  - `interventions` table linked to referrals
  - `communication_logs` table for email tracking
  - `email_templates` table for customizable email templates
  - Proper indexes for performance

- ✅ SQLAlchemy Models
  - `Referral` model with relationships to Organization, Profile (student, author)
  - `Intervention` model with relationship to Referral
  - `CommunicationLog` model for tracking communications
  - `EmailTemplate` model for organization-specific templates
  - All models properly integrated with existing Profile and Organization models

### 2. Pydantic Schemas
**Status: Complete**

- ✅ `backend/app/schemas/referral.py`
  - `ReferralConfigResponse` - Configuration from preset_config
  - `ReferralCreate`, `ReferralUpdate`, `ReferralResponse`
  - `InterventionCreate`, `InterventionUpdate`, `InterventionResponse`
  - `EmailRequest`, `EmailSendResponse`
  - Proper list responses with pagination

- ✅ `backend/app/schemas/email_template.py`
  - `EmailTemplateCreate`, `EmailTemplateUpdate`, `EmailTemplateResponse`
  - List responses with pagination

### 3. API Endpoints
**Status: Complete**

All endpoints in `backend/app/routers/referrals.py`:

#### Configuration
- ✅ `GET /api/v1/organizations/{org_id}/config/referrals`
  - Returns referral_config from organization.preset_config

#### Referral CRUD
- ✅ `POST /api/v1/organizations/{org_id}/referrals` - Create referral
- ✅ `GET /api/v1/organizations/{org_id}/referrals` - List referrals (with pagination & filters)
  - Role-based access: Admin/Secretary see all, Staff see only their own
- ✅ `GET /api/v1/organizations/{org_id}/referrals/{referral_id}` - Get single referral
- ✅ `PATCH /api/v1/organizations/{org_id}/referrals/{referral_id}` - Update referral

#### Interventions
- ✅ `POST /api/v1/organizations/{org_id}/referrals/{referral_id}/interventions` - Create intervention
- ✅ `GET /api/v1/organizations/{org_id}/referrals/{referral_id}/interventions` - List interventions
- ✅ `PATCH /api/v1/organizations/{org_id}/referrals/{referral_id}/interventions/{intervention_id}` - Update intervention

#### PDF & Email
- ✅ `GET /api/v1/organizations/{org_id}/referrals/{referral_id}/pdf` - Download PDF
- ✅ `POST /api/v1/organizations/{org_id}/referrals/{referral_id}/email` - Send email with PDF

### 4. Services
**Status: Complete**

- ✅ `backend/app/services/pdf_service.py`
  - `generate_referral_pdf()` - Generate PDF using WeasyPrint & Jinja2
  - Beautiful HTML template at `backend/app/templates/referral_report.html`
  - Includes organization branding, student info, incident details, interventions

- ✅ `backend/app/services/email_service.py`
  - `send_referral_email()` - Send email via Resend with PDF attachment
  - `render_email_template()` - Jinja2 template rendering for emails
  - `get_email_context_for_referral()` - Prepare template context
  - Communication logging for sent/failed emails

### 5. Dependencies & Configuration
**Status: Complete**

- ✅ Updated `backend/requirements.txt` with:
  - `resend` - Email service
  - `weasyprint` - PDF generation
  - `jinja2` - Template rendering

- ✅ Router registered in `backend/app/main.py`

### 6. Key Features Implemented

✅ **Role-Based Access Control**
- Admin/Secretary: Full access to all referrals
- Staff: Can only view/edit their own referrals

✅ **Soft Validation**
- Accepts any string values for location, time_of_day
- Supports "Other" custom values
- Behaviors stored as JSONB array

✅ **PDF Generation**
- Professional report template
- Organization branding
- Student information
- Incident details
- Interventions list

✅ **Email Integration**
- Resend API integration
- PDF attachments
- Email template support with Jinja2 variables
- Communication logging

## ✅ Completed Frontend Implementation

### 1. Hooks & API Client
**Status: Complete**

- ✅ `frontend/hooks/useReferrals.ts`
  - `useReferralConfig()` - Fetch configuration
  - `useReferrals()` - List referrals with filters & pagination
  - `useReferral()` - Get single referral
  - `createReferral()` - Create referral
  - `updateReferral()` - Update referral
  - `createIntervention()` - Create intervention
  - `updateIntervention()` - Update intervention
  - `downloadReferralPDF()` - Download PDF
  - `sendReferralEmail()` - Send email

## 🔄 Remaining Frontend Components

### 2. Forms & Components
**Status: Not Started - Ready for Implementation**

The following components need to be created following the patterns in existing components like `CreateStudentGuardianForm.tsx`:

#### CreateReferralForm Component
**File:** `frontend/components/ui/CreateReferralForm.tsx`

**Requirements:**
- Multi-step form with student selector
- Fetch config using `useReferralConfig()`
- Fields:
  - Student selector (dropdown from students in organization)
  - Type dropdown (from config.types)
  - Location dropdown (from config.locations.options) with "Other" → text input
  - Time of day dropdown (from config.time_of_day.options) with "Other" → text input
  - Behaviors multi-select (from config.behaviors.options)
  - Description textarea
  - Date/time pickers for incident
- Handle "Other" logic: show text input when "Other" selected
- Submit to `createReferral()`

#### InterventionForm Component
**File:** `frontend/components/ui/InterventionForm.tsx`

**Requirements:**
- Modal or inline form
- Fields:
  - Title dropdown (from config.common_interventions) or custom text input
  - Description textarea
  - Status select (PLANNED, IN_PROGRESS, COMPLETED)
  - Date pickers (planned_date, completion_date)
- Submit to `createIntervention()` or `updateIntervention()`

#### ReferralList Component
**File:** `frontend/components/ui/ReferralList.tsx`

**Requirements:**
- Table view of referrals using `useReferrals()`
- Columns: Student, Type, Status, Location, Date, Actions
- Filters: Status, Type, Student, Date range
- Pagination controls
- Click row to navigate to detail page
- Status badges with colors

#### ReferralDetail Component
**File:** `frontend/components/ui/ReferralDetail.tsx`

**Requirements:**
- Display full referral using `useReferral()`
- Sections:
  - Student information
  - Incident details
  - Interventions list
  - Actions (Edit, Download PDF, Email, Add Intervention)
- Edit referral button → open edit form
- Add intervention button → open InterventionForm
- Download PDF button → call `downloadReferralPDF()`
- Email button → open EmailReferralModal

#### EmailReferralModal Component
**File:** `frontend/components/ui/EmailReferralModal.tsx`

**Requirements:**
- Modal dialog
- Fetch student's guardians from organization
- Multi-select for guardian emails
- Subject input (optional, defaults to template)
- Message textarea (optional)
- Template selector (if email_templates implemented)
- Send button → call `sendReferralEmail()`
- Success/error toast notifications

### 3. Pages
**Status: Not Started - Ready for Implementation**

#### Referrals Dashboard Page
**File:** `frontend/app/(app)/dashboard/organizations/[orgId]/referrals/page.tsx`

**Requirements:**
- Page layout with header "Referrals"
- "Create Referral" button → open CreateReferralForm
- Embed `<ReferralList orgId={orgId} />`
- Filter controls
- Export to CSV option (future enhancement)

#### Referral Detail Page
**File:** `frontend/app/(app)/dashboard/organizations/[orgId]/referrals/[referralId]/page.tsx`

**Requirements:**
- Page layout with breadcrumbs
- Embed `<ReferralDetail orgId={orgId} referralId={referralId} />`
- Back button to referrals list

## 📋 Implementation Guide for Frontend

### Step 1: Create CreateReferralForm

```tsx
// Pattern to follow from CreateStudentGuardianForm.tsx
'use client'

import { useState } from 'react'
import { useReferralConfig, createReferral } from '@/hooks/useReferrals'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { useToast } from '@/hooks/useToast'

export function CreateReferralForm({ orgId, onSuccess }: Props) {
  const { config, isLoading } = useReferralConfig(orgId)
  const [formData, setFormData] = useState({ /* fields */ })
  const { toast } = useToast()
  
  // Fetch students for selector
  // Handle "Other" logic for location/time_of_day
  // Submit form
  
  return (
    <Card>
      {/* Form fields */}
    </Card>
  )
}
```

### Step 2: Create Other Components

Follow similar patterns from existing UI components:
- Use existing UI primitives (Button, Input, Card, etc.)
- Use `useToast` for notifications
- Use `useErrorHandler` for error handling
- Follow the styling patterns from other components

### Step 3: Create Pages

```tsx
// frontend/app/(app)/dashboard/organizations/[orgId]/referrals/page.tsx
'use client'

import { ReferralList } from '@/components/ui/ReferralList'
import { CreateReferralForm } from '@/components/ui/CreateReferralForm'
import { useState } from 'react'

export default function ReferralsPage({ params }: { params: { orgId: string } }) {
  const [showCreate, setShowCreate] = useState(false)
  
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Referrals</h1>
        <Button onClick={() => setShowCreate(true)}>Create Referral</Button>
      </div>
      
      {showCreate && (
        <CreateReferralForm 
          orgId={params.orgId} 
          onSuccess={() => setShowCreate(false)} 
        />
      )}
      
      <ReferralList orgId={params.orgId} />
    </div>
  )
}
```

## 🗄️ Database Migration

To apply the schema changes:

```bash
cd backend
alembic upgrade head
```

## 🔧 Environment Variables

Add to `backend/.env`:

```env
RESEND_API_KEY=your_resend_api_key_here
```

## 📝 Configuration Example

Add to organization's `preset_config`:

```json
{
  "referral_config": {
    "types": ["Behavior", "Support", "Academic"],
    "locations": {
      "options": ["Classroom", "Hallway", "Playground", "Cafeteria", "Gym", "Other"]
    },
    "time_of_day": {
      "options": ["Morning", "Mid-Morning", "Lunch", "Afternoon", "After School", "Other"]
    },
    "behaviors": {
      "options": [
        "Disruption",
        "Tardy",
        "Physical Aggression",
        "Verbal Aggression",
        "Defiance",
        "Inappropriate Language",
        "Bullying",
        "Dress Code Violation",
        "Technology Misuse",
        "Other"
      ]
    },
    "common_interventions": [
      "Parent Contact",
      "Counseling Referral",
      "Detention",
      "In-School Suspension",
      "Behavior Contract",
      "Restorative Circle",
      "Check-in/Check-out",
      "Academic Support",
      "Peer Mediation"
    ]
  }
}
```

## ✅ Testing Checklist

Before deployment:

1. **Backend:**
   - [ ] Run migration: `alembic upgrade head`
   - [ ] Install dependencies: `pip install -r requirements.txt`
   - [ ] Set RESEND_API_KEY in environment
   - [ ] Test config endpoint with sample organization
   - [ ] Test creating referral
   - [ ] Test PDF generation
   - [ ] Test email sending

2. **Frontend:**
   - [ ] Implement remaining components
   - [ ] Test referral creation flow
   - [ ] Test PDF download
   - [ ] Test email sending
   - [ ] Test role-based access (staff vs admin)
   - [ ] Test "Other" value handling

## 🚀 Next Steps

1. Apply the database migration
2. Add referral_config to an organization's preset_config
3. Install backend dependencies
4. Set up Resend API key
5. Implement remaining frontend components following the patterns above
6. Test the complete flow
7. Add tests (optional but recommended)

## 📚 API Documentation

The API endpoints are self-documenting. Access Swagger docs at:
`http://localhost:8000/docs`

All endpoints are under:
`/api/v1/organizations/{org_id}/`

---

**Implementation Date:** 2025-01-22
**Status:** Backend Complete, Frontend 20% Complete
**Remaining Effort:** ~8-12 hours for frontend components

