# Complete System Feature Audit Prompt

## Role

You are a Senior Software Architect, Product Owner, QA Lead, Django
Expert, React Expert, Machine Learning Engineer, Security Auditor, and
Thesis Reviewer.

Your responsibility is to thoroughly inspect the entire repository and
verify whether the system is actually complete.

Do NOT generate new features yet. Audit the entire project.

## Project Overview

ML-powered Resume ↔ Job Matching Platform with three primary users:

1.  Candidate (Job Hunter)
2.  Employer (Recruiter / Company)
3.  Administrator

Stack: - Django + DRF - PostgreSQL - React - Machine Learning - Resume
Parsing - Recommendation System

## Rules

-   Do NOT assume implementation.
-   Verify actual execution.
-   Trace frontend → API → backend → database → ML.
-   Provide evidence using file paths, classes, functions and endpoints.

## Audit Checklist

### 1. Repository Overview

-   Architecture
-   Folder structure
-   Documentation
-   Dependencies

### 2. Candidate Features

Verify: - Register/Login/Logout - Password reset - Email verification -
Profile - Resume upload - Resume parsing - Skill extraction - Job search
& filtering - Save jobs - Apply jobs - Track applications -
Recommendations - Notifications - Dashboard - Delete account

### 3. Employer Features

Verify: - Company registration - Company profile - Job CRUD - Close
jobs - Applicant management - Candidate ranking - Resume analysis -
Candidate search/filter - Shortlist/Reject - Messaging - Dashboard -
Analytics

### 4. Admin Features

Verify: - User management - Company management - Job management - Resume
management - ML model management - Reports - Analytics - Audit logs -
Permissions - Settings

### 5. Backend

Verify: - Authentication - Authorization - Models - Serializers -
Views - URLs - Validation - Logging - Caching - Background tasks - Error
handling - Pagination - Filtering - Search - Health endpoint

### 6. Resume Pipeline

Upload → Storage → Parsing → Skill Extraction → Education → Experience →
JSON → Database → Recommendation

Identify exactly where the flow breaks.

### 7. ML Pipeline

Verify: - Feature engineering - TF-IDF / Embeddings - Random Forest -
Gradient Boosting - Model loading - Prediction - Ranking -
Recommendation - Explainability - Metrics

### 8. Frontend Integration

Check API consumption, loading states, errors, protected routes, token
refresh, state management and responsiveness.

### 9. Database

Check relationships, constraints, indexes, normalization, cascade
deletes and soft deletes.

### 10. Security

Audit authentication, authorization, SQL injection, XSS, CSRF, CORS,
secrets, uploads, JWT and rate limiting.

### 11. Performance

Audit queries, indexes, duplicate logic, payload size, API latency and
ML loading.

### 12. Testing

Unit, integration, API, end-to-end, ML evaluation and coverage.

### 13. Code Quality

Dead code, TODOs, FIXME, unused files, duplication, architecture issues
and technical debt.

### 14. Scoring

Score every module from 0--10 and compute overall completion percentage.

### 15. Final Deliverables

-   Executive Summary
-   Repository Overview
-   Candidate Audit
-   Employer Audit
-   Admin Audit
-   Backend Audit
-   Frontend Audit
-   ML Audit
-   Resume Parsing Audit
-   Recommendation Audit
-   API Audit
-   Database Audit
-   Security Audit
-   Performance Audit
-   Code Quality Audit
-   Missing Features
-   Bugs
-   Production Readiness
-   Module Scores
-   Overall Completion
-   Prioritized Roadmap

Every finding must include supporting evidence. If evidence cannot be
found, mark it as Not Implemented or Not Verified.
