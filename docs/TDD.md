# TDD (EN) - Project Solo Levelling (PSL)

## Technical Description Document (TDD)

### Real-Life RPG Self-Improvement App

Based on the Product Requirements Document (PRD)

---

## 1. Requirements

### 1.1 Functional Requirements

#### Authentication

- User registration.
- User login/logout.
- JWT authentication.
- Role-based access control.

#### User Dashboard

- Display username.
- Display global level.
- Display stat levels.
- Display XP progress bars.
- Display recent activity logs.
- Animated XP updates.

#### Logging System

- User can submit predefined activities.
- Activities can be positive or negative.
- Activities can affect multiple stats.
- Activities support binary and quantified inputs.

#### XP and Level System

- Each stat has XP and level.
- User has a global level.
- XP recalculates after logging.
- Levels update dynamically.
- XP values configurable through admin panel.

#### Admin Panel

- Create activity templates.
- Edit activity templates.
- Configure XP effects.
- Enable/disable templates.
- Configure affected stats.

---

### 1.2 Non-Functional Requirements

#### Performance

- Dashboard load under 2 seconds.
- Activity logging under 500ms.
- Optimistic frontend updates.

#### Scalability

- Modular architecture.
- Future support for achievements, AI, multiplayer, and leaderboards.
- Horizontal scalability.

#### Security

- Secure password hashing.
- JWT authentication.
- HTTPS-only communication.
- Protected admin routes.
- Input validation and rate limiting.

#### Usability

- Logging flow under 30 seconds.
- Mobile-first responsive design.
- PWA support.

---

## 2. Core Entities

### User

```tsx
User {
  id: UUID
  username: string
  email: string
  passwordHash: string
  role: USER | ADMIN
  globalXp: number
  globalLevel: number
  createdAt: datetime
}
```

---

### Stat

```tsx
Stat {
  id: UUID
  key: string
  displayName: string
  icon: string
}
```

Default stats:

- Strength
- Health
- Intelligence
- Mental State
- Endurance
- Finance
- Social Skills

---

### UserStat

```tsx
UserStat {
  id: UUID
  userId: UUID
  statId: UUID
  xp: number
  level: number
}
```

---

### ActivityTemplate

```tsx
ActivityTemplate {
  id: UUID
  title: string
  description: string
  inputType: BINARY | QUANTITY
  isEnabled: boolean
  effects: ActivityEffect[]
}
```

One `ActivityTemplate` can have multiple `ActivityEffect` records because one activity can affect several stats.

---

### ActivityEffect

```tsx
ActivityEffect {
  id: UUID
  activityTemplateId: UUID
  statId: UUID
  xpChange: number
}
```

`xpChange` can be both positive and negative.

This allows a single activity to have mixed effects.

Example:

```
Alcohol:
+10 Social Skills
-15 Health
-5 Mental State
```

---

### ActivityLog

```tsx
ActivityLog {
  id: UUID
  userId: UUID
  activityTemplateId: UUID
  quantity: number
  totalXpApplied: number
  createdAt: datetime
}
```

---

## 3. API

### Authentication

#### POST /auth/register

```json
{
  "username": "danylo",
  "email": "user@example.com",
  "password": "password123"
}
```

---

#### POST /auth/login

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

---

### User

#### GET /users/me

Returns current user profile.

---

#### GET /users/me/stats

Returns user stats.

---

#### GET /users/me/activity-history

Returns recent activity logs.

---

### Activities

#### GET /activities

Returns available activity templates.

---

#### POST /activities/log

```json
{
  "activityTemplateId": "uuid",
  "quantity": 60
}
```

---

### Admin

#### POST /admin/activity-templates

Creates activity template.

---

#### PATCH /admin/activity-templates/:id

Updates activity template.

---

#### DELETE /admin/activity-templates/:id

Disables activity template.

---

## 4. High-Level Design

### Frontend

#### Stack

- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Feature-Sliced Design (FSD)

#### Architecture

Frontend uses Feature-Sliced Design for clear separation of product layers.

Recommended layers:

```
app/
pages/
assets/
components/
features/
hooks/
lib/
testing/
types/
utils/
config/
```

#### Modules

- Authentication
- Dashboard
- Logging
- Shared UI

---

### Backend

#### Stack

- FastAPI
- PostgreSQL
- Redis
- JWT
- SQLAdmin or similar admin tooling

#### Architecture

Backend uses Service-Oriented Architecture (SOA). Business logic is separated into independent services that can evolve separately.

#### Services

- Auth Service
- User Service
- Stats Service
- Activity Service
- Admin Service

#### Admin Panel

Admin functionality is implemented on FastAPI using SQLAdmin or a similar library.

Admin responsibilities:

- Manage activity templates.
- Manage activity effects.
- Enable or disable activities.
- Balance XP values without code changes.

---

### Database Relationships

```
User -> UserStat
User -> ActivityLog
Stat -> UserStat
ActivityTemplate -> ActivityEffect
ActivityTemplate -> ActivityLog
Stat -> ActivityEffect
```

---

### Infrastructure

#### Frontend Hosting

- Vercel

#### Backend Hosting

- Render

#### Database

- Supabase PostgreSQL

#### Cache

- Redis on Render

---

### Environments

```
local
preview
production
```

---

## 5. Deep Dives

### 5.1 Activity Processing Flow

```
1. User selects activity
2. Frontend validates input
3. Request sent to backend
4. Backend validates activity template
5. XP effects calculated
6. User stats updated
7. Global XP recalculated
8. Activity log stored
9. Updated progression returned
10. Frontend animates updates
```

---

### 5.2 XP Formula

```
Final XP = Base XP × Quantity Multiplier
```

Example:

```
Workout XP = 10
Quantity = 2
Final XP = 20
```

---

### 5.3 Level Formula

Recommended MVP formula:

genui{"math_block_widget_always_prefetch_v2":{"content":"XP=100\cdot Level^{1.5}"}}

Goals:

- Fast early progression.
- Slower late progression.
- Rewarding long-term growth.

---

### 5.4 Global Level Logic

```
Global XP = Sum of all stat XP
```

Global level uses the same progression formula.

---

### 5.5 Testing Strategy

Tests are required for both backend and frontend.

#### Backend Tests

- XP calculations.
- Level calculations.
- Activity effect processing.
- API endpoints.
- Authentication.
- Database interactions.

#### Frontend Tests

- Dashboard rendering.
- Activity logging form.
- Stat card rendering.
- User interaction flows.
- API integration states.

#### E2E Tests

- Registration.
- Login.
- Activity logging.
- Admin workflows.

Recommended tools:

- Pytest for backend.
- Vitest / React Testing Library for frontend.
- Playwright for E2E.

---

### 5.6 Observability

#### Monitoring

- API latency.
- Error rate.
- Active users.
- Log submissions.

#### Tools

- Sentry
