# Frontend - Human-in-the-Loop AI Supervisor

A modern Next.js web application that provides a dashboard interface for managing AI receptionist help requests and knowledge base entries. This system allows human supervisors to respond to customer inquiries, update the AI's knowledge base, and monitor system performance.

## 🌟 Features

### Core Functionality
- **Help Request Management**: View and respond to pending customer inquiries
- **Knowledge Base Viewer**: Browse AI's learned responses and capabilities
- **Real-time Status Monitoring**: Track system health and active calls
- **Responsive Design**: Works on desktop and mobile devices

### User Interface
- Modern, clean interface built with Tailwind CSS
- Component-based architecture with React 19
- Real-time updates with polling mechanism
- Type-safe development with TypeScript

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Backend API running (see backend README)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd frontend

# Install dependencies
npm install
# or
yarn install
```

### Configuration
Create a `.env.local` file with the following variables:
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### Development
```bash
# Start development server
npm run dev
# or
yarn dev
```

### Build & Production
```bash
# Create production build
npm run build

# Start production server
npm start
```

## 🏗️ Architecture

### Tech Stack
- **Framework**: Next.js 15.3.2 (App Router)
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4.1.6
- **Language**: TypeScript 5
- **HTTP Client**: Native Fetch API
- **Icons**: Heroicons

### Key Components

#### Pages
- **Home Page** (`/`): Dashboard with navigation cards
- **Help Requests** (`/pages/requests`): Manage pending inquiries
- **Knowledge Base** (`/pages/knowledge`): View learned answers

#### Components
- `HelpRequestCard`: Display and manage individual help requests
- `KnowledgeBaseEntry`: Show knowledge base items

#### API Integration
- Custom API utility in `utils/api.ts`
- Next.js API routes for proxying backend requests
- Type definitions for data structures

### Project Structure
```
frontend/
├── src/
│   └── app/
│       ├── api/                    # API route handlers
│       │   ├── help-requests/
│       │   │   ├── route.ts
│       │   │   └── [id]/
│       │   │       └── respond/
│       │   │           └── route.ts
│       │   └── knowledge/
│       │       └── route.ts
│       ├── components/             # Reusable UI components
│       │   ├── HelpRequestCard.tsx
│       │   └── KnowledgeBaseEntry.tsx
│       ├── pages/                  # Application pages
│       │   ├── knowledge/
│       │   │   └── page.tsx
│       │   └── requests/
│       │       └── page.tsx
│       ├── globals.css             # Global styles
│       ├── layout.tsx              # Root layout
│       └── page.tsx                # Home page
├── utils/
│   └── api.ts                      # API utilities and types
├── public/                         # Static assets
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── .gitignore                      # Git ignore file
├── next.config.ts                  # Next.js configuration
├── package.json                    # Project dependencies
├── package-lock.json               # Dependency lock file
├── postcss.config.mjs              # PostCSS configuration
├── README.md                       # Project documentation
├── tailwind.config.js              # Tailwind CSS configuration
└── tsconfig.json                   # TypeScript configuration
```

## 📡 API Integration

### API Routes
The frontend communicates with the backend through Next.js API routes:

```typescript
// Help Requests
GET  /api/help-requests              - List all help requests
POST /api/help-requests/:id/respond  - Submit answer

// Knowledge Base
GET  /api/knowledge                  - List all knowledge entries
```

### Backend Communication
- API routes proxy requests to the backend server
- Configured backend URL: `http://localhost:5000`
- JSON content type for all requests

## 🎯 Usage Examples

### Viewing Help Requests
```typescript
// Fetching help requests
const response = await fetch('/api/help-requests');
const requests = await response.json();
```

### Submitting Responses
```typescript
// Submitting a supervisor response
const response = await fetch(`/api/help-requests/${requestId}/respond`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ response: answer })
});
```


## 🚦 Testing & Deployment

### Local Testing
```bash
# Run development server
npm run dev

# Test production build
npm run build && npm start
```

### Deployment Options
- **Vercel**: Recommended for Next.js apps
- **Docker**: Use multi-stage builds
- **Traditional hosting**: Export as static site

### Environment Variables
Required for all environments:
- `NEXT_PUBLIC_API_URL`: Backend API endpoint

## 🔄 Real-time Updates

The application implements polling for real-time updates:
- Help requests refresh every 10 seconds
- Manual refresh available for immediate updates
- Future enhancement: WebSocket for instant updates

