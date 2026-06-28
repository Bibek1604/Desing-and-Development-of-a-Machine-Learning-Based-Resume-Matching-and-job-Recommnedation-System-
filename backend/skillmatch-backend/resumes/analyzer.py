"""ATS Resume Analyzer — scores a resume 0-100 across five dimensions.

Dimensions
----------
completeness  (25 pts) — required sections present: contact, summary, education,
                          experience/internship, skills, projects
keywords      (25 pts) — skill density relative to a reference vocabulary
formatting    (20 pts) — text length, structure signals (bullet chars, sections)
experience    (15 pts) — detects internship / work experience mentions
social        (15 pts) — GitHub, LinkedIn, portfolio, certifications

Usage
-----
    from resumes.analyzer import ATSScorer
    result = ATSScorer().analyze(resume_text, known_skills)
    print(result["ats_score"])       # 0-100
    print(result["strengths"])       # list[str]
    print(result["recommendations"]) # list[str]
"""
from __future__ import annotations
import re
import math
from dataclasses import dataclass, field

from matching.nlp.extractor import detect_sections

# ── Reference ATS section weights ────────────────────────────────────────────
_SECTION_WEIGHTS = {
    "contact":        5,
    "summary":        3,
    "education":      5,
    "experience":     5,
    "skills":         4,
    "projects":       3,
}

_STRONG_KEYWORDS = [
    "developed","implemented","designed","built","optimised","optimized",
    "deployed","integrated","architected","led","managed","reduced","improved",
    "increased","automated","migrated","launched","shipped","delivered",
    "contributed","mentored","researched","published","presented",
]

_SOCIAL_RE = {
    "github":    re.compile(r"github\.com/\S+", re.I),
    "linkedin":  re.compile(r"linkedin\.com/in/\S+", re.I),
    "portfolio": re.compile(r"https?://\S+\.(?:netlify|vercel|github\.io|com)\S*", re.I),
}

_CERT_KEYWORDS = [
    "certified","certificate","certification","coursera","udemy","aws",
    "google","microsoft","oracle","cisco","comptia","scrum","pmp",
]

_INTERNSHIP_RE = re.compile(r"\b(intern|internship|trainee|apprentice)\b", re.I)
_WORK_EXP_RE   = re.compile(r"\b(\d+)\s+(year|month)s?\s+(of\s+)?(experience|work)\b", re.I)
_BULLET_RE     = re.compile(r"^[\s]*[•\-\*\>◦▪▸]+\s", re.M)
_EMAIL_RE      = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE      = re.compile(r"[0-9]{7,15}")


@dataclass
class ATSResult:
    ats_score:          int = 0
    completeness_score: int = 0
    formatting_score:   int = 0
    keyword_score:      int = 0
    experience_score:   int = 0
    social_score:       int = 0
    strengths:          list[str] = field(default_factory=list)
    weaknesses:         list[str] = field(default_factory=list)
    recommendations:    list[str] = field(default_factory=list)
    section_scores:     dict[str, int] = field(default_factory=dict)
    missing_sections:   list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ats_score":          self.ats_score,
            "completeness_score": self.completeness_score,
            "formatting_score":   self.formatting_score,
            "keyword_score":      self.keyword_score,
            "experience_score":   self.experience_score,
            "social_score":       self.social_score,
            "strengths":          self.strengths,
            "weaknesses":         self.weaknesses,
            "recommendations":    self.recommendations,
            "section_scores":     self.section_scores,
            "missing_sections":   self.missing_sections,
        }


class ATSScorer:
    """Analyse a resume text and return a structured ATS score."""

    def analyze(self, text: str, known_skills: list[str] | None = None) -> dict:
        result = ATSResult()
        if not text:
            result.weaknesses.append("Empty resume — no content detected")
            result.recommendations.append("Upload a valid PDF or DOCX file")
            return result.to_dict()

        lower = text.lower()

        # ── 1. Completeness (25 pts) ──────────────────────────────────────
        sections = detect_sections(text)
        comp_pts = 0
        for sec, pts in _SECTION_WEIGHTS.items():
            if sections.get(sec):
                comp_pts += pts
                result.section_scores[sec] = pts
            else:
                result.missing_sections.append(sec)
                result.section_scores[sec] = 0
        result.completeness_score = min(100, int(comp_pts / sum(_SECTION_WEIGHTS.values()) * 100))

        if sections.get("contact") and _EMAIL_RE.search(text):
            result.strengths.append("Contact information with email is present")
        elif not sections.get("contact"):
            result.weaknesses.append("No contact section detected")
            result.recommendations.append("Add a Contact section with email and phone")

        # ── 2. Keywords (25 pts) ──────────────────────────────────────────
        if known_skills:
            from matching.skill_extraction import extract_skills
            found = extract_skills(text, known_skills)
            skill_density = len(found) / max(len(known_skills), 1)
            # sigmoid-style: ~10 skills → 60 pts, ~20 skills → 90 pts
            kw_pts = min(100, int(100 * (1 - math.exp(-skill_density * 4))))
        else:
            # fallback: count action verbs
            action_hits = sum(1 for kw in _STRONG_KEYWORDS if kw in lower)
            kw_pts = min(100, action_hits * 5)
        result.keyword_score = kw_pts

        if kw_pts >= 80:
            result.strengths.append("Strong technical keyword density")
        elif kw_pts < 50:
            result.weaknesses.append("Low keyword density — ATS may filter this resume")
            result.recommendations.append("Add more specific technical skills and tools used")

        # ── 3. Formatting (20 pts) ────────────────────────────────────────
        char_count = len(text)
        word_count = len(text.split())
        bullet_count = len(_BULLET_RE.findall(text))

        length_score  = min(40, int(char_count / 3000 * 40))   # ideal ~3 000 chars
        bullet_score  = min(30, bullet_count * 3)              # bullet points are ATS-friendly
        section_score = min(30, len([s for s in sections.values() if s]) * 3)
        result.formatting_score = min(100, length_score + bullet_score + section_score)

        if word_count < 200:
            result.weaknesses.append("Resume is too short (< 200 words)")
            result.recommendations.append("Expand project descriptions and work experience")
        elif word_count > 700:
            result.strengths.append("Resume has substantial content")

        if bullet_count >= 5:
            result.strengths.append("Good use of bullet points — ATS-friendly formatting")
        else:
            result.recommendations.append("Use bullet points for experience and project descriptions")

        # ── 4. Experience (15 pts) ────────────────────────────────────────
        has_internship = bool(_INTERNSHIP_RE.search(text))
        has_work_years = bool(_WORK_EXP_RE.search(text))
        has_projects   = bool(sections.get("projects"))

        exp_pts = 0
        if has_internship:
            exp_pts += 40
            result.strengths.append("Internship experience found")
        if has_work_years:
            exp_pts += 40
        if has_projects:
            exp_pts += 20
            result.strengths.append("Projects section present — shows practical ability")
        result.experience_score = min(100, exp_pts)

        if not has_internship and not has_work_years:
            result.weaknesses.append("No internship or work experience detected")
            result.recommendations.append("Add an Internship/Experience section even for part-time roles")

        # ── 5. Social (15 pts) ────────────────────────────────────────────
        soc_pts = 0
        for platform, rx in _SOCIAL_RE.items():
            if rx.search(text):
                soc_pts += 25
                result.strengths.append(f"{platform.capitalize()} profile link found")
        has_cert = any(kw in lower for kw in _CERT_KEYWORDS)
        if has_cert:
            soc_pts += 25
            result.strengths.append("Certifications mentioned")
        else:
            result.weaknesses.append("No certifications detected")
            result.recommendations.append("Add relevant online certifications (AWS, Google, Coursera…)")
        result.social_score = min(100, soc_pts)

        if not _SOCIAL_RE["github"].search(text):
            result.recommendations.append("Include your GitHub profile link — recruiters actively check it")
        if not _SOCIAL_RE["linkedin"].search(text):
            result.recommendations.append("Add LinkedIn URL for professional visibility")

        # ── Composite ATS score ───────────────────────────────────────────
        result.ats_score = int(
            0.25 * result.completeness_score
            + 0.25 * result.keyword_score
            + 0.20 * result.formatting_score
            + 0.15 * result.experience_score
            + 0.15 * result.social_score
        )

        # Final recommendations cap
        if not result.recommendations:
            result.recommendations.append("Great resume! Tailor the summary for each job application.")

        return result.to_dict()
