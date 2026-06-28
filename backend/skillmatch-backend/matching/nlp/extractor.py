"""NLP-based information extractor for resume text.

Pipeline:
  1. spaCy NER for named entities (ORG, DATE, PERSON, GPE)
  2. Rule-based section detection (education, experience, skills, certifications…)
  3. Dictionary + regex skill extraction (extends matching.skill_extraction)
  4. Education and experience block parsers

Falls back gracefully when spaCy / en_core_web_sm is not available.
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# ── Section header patterns ───────────────────────────────────────────────────
_SECTION_PATTERNS = {
    "contact":         re.compile(r"\b(contact|email|phone|mobile|address|linkedin|github)\b", re.I),
    "summary":         re.compile(r"\b(summary|profile|objective|about me)\b", re.I),
    "education":       re.compile(r"\b(education|academic|qualification|degree|university|college)\b", re.I),
    "experience":      re.compile(r"\b(experience|work history|employment|internship|professional)\b", re.I),
    "skills":          re.compile(r"\b(skills|technologies|technical|competencies|proficiencies)\b", re.I),
    "projects":        re.compile(r"\b(projects|portfolio|personal projects)\b", re.I),
    "certifications":  re.compile(r"\b(certifications?|certificate|credential|training)\b", re.I),
    "achievements":    re.compile(r"\b(achievements?|awards?|honours?|accomplishments?)\b", re.I),
    "languages":       re.compile(r"\b(languages?|spoken|fluency)\b", re.I),
    "volunteer":       re.compile(r"\b(volunteer|community|social)\b", re.I),
    "research":        re.compile(r"\b(research|publications?|papers?)\b", re.I),
}

# ── CGPA / GPA ───────────────────────────────────────────────────────────────
_CGPA_RE = re.compile(r"(?:cgpa|gpa|grade)[:\s]*([0-9]+\.[0-9]+)", re.I)
_YEAR_RE  = re.compile(r"\b(20[0-9]{2})\b")

# ── Degree keywords ───────────────────────────────────────────────────────────
DEGREE_KEYWORDS = [
    "BSc CSIT", "BE Computer", "BE Software", "BIT", "BCA", "BIM", "BICTE",
    "Bachelor of Science", "Bachelor of Engineering", "Bachelor of Technology",
    "B.Tech", "B.E.", "B.Sc", "MCA", "M.Sc", "M.Tech", "MBA",
    "Data Science", "Artificial Intelligence", "Cyber Security",
]

# ── Email / phone ─────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(?:\+977[-\s]?)?[0-9]{2,4}[-\s]?[0-9]{6,8}")
_GITHUB_RE  = re.compile(r"github\.com/[\w\-]+", re.I)
_LINKEDIN_RE= re.compile(r"linkedin\.com/in/[\w\-]+", re.I)


@dataclass
class ExtractedResume:
    name:          str = ""
    email:         str = ""
    phone:         str = ""
    github:        str = ""
    linkedin:      str = ""
    degree:        str = ""
    cgpa:          float | None = None
    graduation_year: int | None = None
    colleges:      list[str] = field(default_factory=list)
    skills:        list[str] = field(default_factory=list)
    soft_skills:   list[str] = field(default_factory=list)
    certifications:list[str] = field(default_factory=list)
    languages:     list[str] = field(default_factory=list)
    summary:       str = ""
    objective:     str = ""
    sections_found:list[str] = field(default_factory=list)
    entities:      dict = field(default_factory=dict)


def _try_spacy():
    """Load spaCy model or return None."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        try:
            import spacy
            return spacy.load("en_core_web_md")
        except Exception:
            return None


_NLP = None
_NLP_TRIED = False


def _get_nlp():
    global _NLP, _NLP_TRIED
    if not _NLP_TRIED:
        _NLP = _try_spacy()
        _NLP_TRIED = True
    return _NLP


# ── Main entry point ─────────────────────────────────────────────────────────

def extract_resume_info(text: str, known_skills: list[str] | None = None) -> ExtractedResume:
    """Extract structured information from raw resume text."""
    result = ExtractedResume()
    if not text:
        return result

    # 1. Contact info
    emails = _EMAIL_RE.findall(text)
    result.email = emails[0] if emails else ""

    phones = _PHONE_RE.findall(text)
    result.phone = phones[0] if phones else ""

    gh = _GITHUB_RE.search(text)
    result.github = gh.group(0) if gh else ""

    li = _LINKEDIN_RE.search(text)
    result.linkedin = li.group(0) if li else ""

    # 2. Education
    for deg in DEGREE_KEYWORDS:
        if re.search(re.escape(deg), text, re.I):
            result.degree = deg
            break

    cgpa_m = _CGPA_RE.search(text)
    if cgpa_m:
        try:
            result.cgpa = float(cgpa_m.group(1))
        except ValueError:
            pass

    years = [int(y) for y in _YEAR_RE.findall(text) if 2000 <= int(y) <= 2030]
    if years:
        result.graduation_year = max(years)

    # 3. Sections present
    for section, pat in _SECTION_PATTERNS.items():
        if pat.search(text):
            result.sections_found.append(section)

    # 4. Skills (dictionary + spaCy)
    if known_skills:
        from matching.skill_extraction import extract_skills
        result.skills = extract_skills(text, known_skills)

    # 5. spaCy entities
    nlp = _get_nlp()
    if nlp:
        doc = nlp(text[:50000])  # limit for speed
        orgs, persons, gpe = [], [], []
        for ent in doc.ents:
            if ent.label_ == "ORG":
                orgs.append(ent.text)
            elif ent.label_ == "PERSON":
                persons.append(ent.text)
            elif ent.label_ == "GPE":
                gpe.append(ent.text)
        result.entities = {"organizations": orgs[:10], "persons": persons[:5], "locations": gpe[:5]}
        result.colleges = orgs[:5]
        if persons:
            result.name = persons[0]

    # 6. Summary / objective snippets (first matching sentence).
    #    Enumerate so we have the real index — never call lines.index() on a
    #    stripped copy (the stripped value may not exist in the original list).
    lines = text.split("\n")
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not result.summary and re.search(r"\b(summary|profile)\b", line, re.I) and len(line) < 80:
            # take the next non-empty line as the summary
            for nxt in lines[idx + 1:idx + 5]:
                if nxt.strip():
                    result.summary = nxt.strip()
                    break
        if not result.objective and re.search(r"\bobjective\b", line, re.I) and len(line) < 80:
            for nxt in lines[idx + 1:idx + 5]:
                if nxt.strip():
                    result.objective = nxt.strip()
                    break

    return result


def detect_sections(text: str) -> dict[str, bool]:
    """Return a dict of {section_name: present} for completeness scoring."""
    return {k: bool(pat.search(text)) for k, pat in _SECTION_PATTERNS.items()}


def extract_entities_spacy(text: str) -> dict:
    """Raw spaCy entity dict for downstream use."""
    nlp = _get_nlp()
    if not nlp:
        return {}
    doc = nlp(text[:50000])
    entities: dict[str, list[str]] = {}
    for ent in doc.ents:
        entities.setdefault(ent.label_, []).append(ent.text)
    return entities
