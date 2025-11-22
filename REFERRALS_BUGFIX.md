# Referrals Create Form - Student Loading Fix

## Issue
The Create Referral form was not loading students properly.

## Root Causes

### 1. Backend Pagination Limit Exceeded
- **Problem**: The form was requesting `per_page=1000`
- **Backend Limit**: Maximum 100 items per page (enforced in `/api/v1/organizations/{org_id}/students`)
- **Result**: The API was likely rejecting the request or returning only 100 students

### 2. Incorrect Response Structure
- **Problem**: Code expected `{ students: [...] }` in the response
- **Actual Response**: Backend returns `{ profiles: [...] }` (ProfileListResponse schema)

## Solution

### Updated Student Fetching Logic
```typescript
// Before:
const response = await apiClient<{
  students: StudentOption[]
}>(`/api/v1/organizations/${orgId}/students?per_page=1000`)
setStudents(response.students || [])

// After:
let allStudents: StudentOption[] = []
let page = 1
let hasMore = true
const perPage = 100 // Backend max limit

while (hasMore) {
  const response = await apiClient<{
    profiles: StudentOption[]
    total_pages: number
  }>(`/api/v1/organizations/${orgId}/students?page=${page}&per_page=${perPage}`)
  
  const profiles = response.profiles || []
  allStudents = [...allStudents, ...profiles]
  
  hasMore = page < (response.total_pages || 1)
  page++
}

setStudents(allStudents)
```

### Additional Improvements
1. **Pagination Handling**: Loops through all pages to fetch all students
2. **Null Safety**: Added graceful handling for null `grade_level` and `student_id` values
3. **Empty State**: Shows "No students found" message when list is empty
4. **Error Logging**: Added console.error for debugging

## Testing
To verify the fix works:

1. **Navigate** to `/dashboard/referrals/create`
2. **Check** that the Student dropdown is populated
3. **Verify** that all students appear (not just the first 100)
4. **Confirm** student information displays correctly (name, ID, grade)

## Backend Endpoint Details
- **Endpoint**: `GET /api/v1/organizations/{org_id}/students`
- **Auth Required**: Admin role
- **Response**: `ProfileListResponse` with pagination
- **Max per_page**: 100 (enforced)

## Files Modified
- `/home/ericho/edgybe/frontend/components/ui/CreateReferralForm.tsx`

