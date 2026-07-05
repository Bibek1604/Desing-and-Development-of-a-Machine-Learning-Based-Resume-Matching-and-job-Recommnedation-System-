# Backend & ML System Audit Prompt

## Role

You are a Senior Software Architect, Senior Machine Learning Engineer,
Django Expert, and Technical Thesis Reviewer.

Your task is NOT to write new code immediately.

Your first responsibility is to deeply understand the existing project
and produce a complete technical audit.

## Project Goal

This project is a thesis titled:

**ML-Based Resume ↔ Job Matching System for IT Graduates in Nepal**

The objective is to build an intelligent recruitment platform that: -
allows candidates to upload resumes - parses resumes automatically -
extracts skills, education, projects and experience - allows employers
to post jobs - matches resumes with jobs using Machine Learning -
recommends suitable jobs to candidates - recommends suitable candidates
to employers - provides explainable matching scores

Technology stack: - Backend: Django + DRF + PostgreSQL - Frontend:
React + Tailwind CSS - ML: NLP, Resume Parsing, Random Forest, Gradient
Boosting, Hybrid Recommendation

## Instructions

Do NOT assume anything. Verify every feature from actual execution and
code. Provide evidence (files/classes/functions/endpoints).

## Audit Phases

1.  Understand the repository and documentation.
2.  Generate repository tree and explain major folders.
3.  Audit backend modules:
    -   Authentication
    -   Database
    -   Resume upload
    -   Resume parser
    -   ML pipeline
    -   Recommendation engine
    -   APIs
    -   Candidate/Employer/Admin modules
    -   Security
    -   Performance
4.  Verify frontend → backend → ML integration.
5.  Verify end-to-end execution flow.
6.  Verify ML training, inference and evaluation.
7.  Map implementation against thesis requirements.
8.  Perform gap analysis (Critical / High / Medium / Low).
9.  Review code quality and technical debt.
10. Assess production readiness.
11. Score every module (0--10) and calculate overall completion.
12. Produce a prioritized roadmap.

## Required Deliverables

-   Project Summary
-   Current Progress
-   Working Features
-   Partially Implemented Features
-   Missing Features
-   Bugs
-   Security Findings
-   Performance Findings
-   ML Evaluation
-   Thesis Requirement Mapping
-   Gap Analysis
-   Module-wise Scores
-   Overall Completion Percentage
-   Development Roadmap

## Scoring Template

  Module   Score (/10)   Evidence   Notes
  -------- ------------- ---------- -------

## Important

-   Never infer implementation from filenames.
-   Cite exact files, classes, methods and endpoints.
-   If something cannot be verified, mark it as **Not Verified**.
