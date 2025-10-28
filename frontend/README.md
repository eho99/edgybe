# Frontend Setup Guide

## Quick Start

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your Supabase credentials
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**: Navigate to `http://localhost:3000`

## Environment Variables

Create a `.env.local` file with the following variables:

```env
# Supabase project URL and keys (public, safe for browser)
NEXT_PUBLIC_SUPABASE_URL="https://your-project-id.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-supabase-anon-key"

# URL for your FastAPI backend
NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── (app)/             # Protected routes (requires auth)
│   │   ├── dashboard/      # Dashboard page
│   │   └── layout.tsx     # Auth guard layout
│   ├── (auth)/            # Public auth routes
│   │   ├── login/         # Login page
│   │   └── layout.tsx     # Auth layout
│   ├── globals.css         # Global styles
│   └── layout.tsx         # Root layout
├── lib/                   # Utilities
│   ├── supabaseClient.ts  # Supabase client
│   └── apiClient.ts       # FastAPI client wrapper
└── components/            # React components
    └── ui/               # shadcn/ui components
```

## Authentication Flow

### Login Process
1. User enters credentials on `/login`
2. `supabaseClient.auth.signInWithPassword()` authenticates with Supabase
3. Supabase returns JWT token
4. User is redirected to `/dashboard`

### API Calls
1. `apiClient` automatically gets JWT from Supabase session
2. JWT is sent as `Authorization: Bearer <token>` header
3. FastAPI backend validates JWT with Supabase
4. Response is returned to frontend

### Route Protection
- Routes in `(app)/` are automatically protected
- `layout.tsx` checks for valid session
- Unauthenticated users are redirected to `/login`

## Adding New Pages

### Protected Pages
Add to `app/(app)/` directory:
```typescript
// app/(app)/new-page/page.tsx
'use client'

import apiClient from '@/lib/apiClient'

export default function NewPage() {
  // This page is automatically protected
  // Use apiClient for backend calls
}
```

### Public Pages
Add to `app/(auth)/` directory:
```typescript
// app/(auth)/signup/page.tsx
'use client'

import { createClient } from '@/lib/supabaseClient'

export default function SignupPage() {
  // This page is public
  // Use supabaseClient for auth operations
}
```

## API Integration

### Using apiClient
```typescript
import apiClient from '@/lib/apiClient'

// GET request
const response = await apiClient('/api/v1/organizations/123/data')
const data = await response.json()

// POST request
const response = await apiClient('/api/v1/organizations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'New Org' })
})
```

### Error Handling
```typescript
try {
  const response = await apiClient('/api/v1/protected-endpoint')
  const data = await response.json()
} catch (error) {
  // Handle authentication errors
  if (error.message.includes('No authenticated session')) {
    // Redirect to login
    router.push('/login')
  }
}
```

## UI Components

This project uses shadcn/ui components. To add new components:

```bash
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
```

## Styling

- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Pre-built component library
- **CSS Variables**: Customizable theme system

### Custom Styling
```typescript
// Use Tailwind classes
<div className="bg-white shadow rounded-lg p-6">

// Use CSS variables for theming
<div className="bg-background text-foreground">
```

## Development

### Available Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### TypeScript
- Strict mode enabled
- Path aliases configured (`@/` points to root)
- Type definitions for Supabase and API responses

## Troubleshooting

### Common Issues

1. **Authentication not working**: Check environment variables
2. **API calls failing**: Verify backend is running on correct port
3. **Build errors**: Check TypeScript types and imports

### Debug Mode
```bash
# Run with debug logging
NEXT_PUBLIC_DEBUG=true npm run dev
```

## Production Deployment

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Start production server**:
   ```bash
   npm run start
   ```

3. **Environment variables**: Ensure all `NEXT_PUBLIC_*` variables are set in production