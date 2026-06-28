# SkillMatch Nepal — Frontend

Static frontend UI for an ML-based resume-to-job matching platform for IT graduates in Nepal.
Built with **Next.js 14 (App Router) + TypeScript + Tailwind CSS**. This is **UI only** — no backend
or real ML yet; all content is mock data in `lib/data.ts`.

## Getting started

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Build for production

```bash
npm run build
npm run start
```

## Pages

| Route        | Description                                   |
|--------------|-----------------------------------------------|
| `/`          | Landing page (hero, features, how it works)   |
| `/jobs`      | Job listings with search & filter UI          |
| `/upload`    | Resume upload UI                              |
| `/dashboard` | Candidate dashboard (matches, skill analysis) |
| `/employer`  | Employer post-a-job + matched candidates      |
| `/login`     | Login form                                    |
| `/register`  | Registration form                            |

## Structure

```
app/            Routes (App Router)
components/      Reusable UI (Navbar, Footer, JobCard, MatchRing, ...)
lib/            Types and mock data
```

## Theme

Blue-on-white. The `brand` color scale lives in `tailwind.config.ts`; shared UI classes
(`.btn-primary`, `.card`, `.input`, `.chip`, ...) are defined in `app/globals.css`.

## Next steps

- Wire pages to a backend API (Django/FastAPI).
- Replace mock data in `lib/data.ts` with live data.
- Add auth and real resume upload + parsing.
