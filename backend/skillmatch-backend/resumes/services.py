"""Post-upload processing: parse text, extract skills, run ATS + embedding."""
import logging
from skills.models import Skill
from matching.skill_extraction import extract_skills

log = logging.getLogger(__name__)


def process_resume(resume) -> None:
    """Full pipeline on resume upload:
    1. Extract raw text
    2. NLP skill extraction → update CandidateProfile
    3. ATS analysis → persist ATSAnalysis row
    4. Sentence-BERT embedding → persist CandidateEmbedding row
    """
    # 1. Text extraction
    resume.raw_text = ""
    if resume.file:
        try:
            from .parsing import extract_text
            resume.raw_text = extract_text(resume.file.path)
        except Exception as exc:
            log.warning("Text extraction failed for resume %s: %s", resume.pk, exc)
    resume.save(update_fields=["raw_text"])

    # 2. Skill extraction
    known = list(Skill.objects.values_list("name", flat=True))
    found_names = extract_skills(resume.raw_text, known)
    found_skills = Skill.objects.filter(name__in=found_names)
    resume.extracted_skills.set(found_skills)

    # 3. Update profile — skills, score, and parsed details (education, links,
    #    contact, bio). Parsed values only fill BLANK fields so we never clobber
    #    anything the candidate has manually edited on their profile.
    profile = getattr(resume.candidate, "candidate_profile", None)
    if profile is not None:
        profile.skills.add(*found_skills)
        profile.resume_score = _resume_score(resume.raw_text, found_skills.count())
        try:
            _populate_profile_from_resume(profile, resume.raw_text, known)
        except Exception as exc:  # noqa: BLE001
            log.warning("Profile auto-fill failed for resume %s: %s", resume.pk, exc)
        profile.save()

    # 4. ATS analysis
    try:
        _run_ats_analysis(resume, known)
    except Exception as exc:
        log.warning("ATS analysis failed for resume %s: %s", resume.pk, exc)

    # 5. Embedding
    try:
        _update_embedding(resume.candidate, resume.raw_text)
    except Exception as exc:
        log.debug("Embedding update skipped for resume %s: %s", resume.pk, exc)


def _populate_profile_from_resume(profile, text: str, known_skills: list) -> None:
    """Fill blank CandidateProfile fields with details parsed from the resume.

    Education, contact, social links and a short bio are extracted by the
    rule-based NLP parser. Existing (non-blank) fields are left untouched so a
    re-upload never overwrites the candidate's own edits.
    """
    from matching.nlp.extractor import extract_resume_info

    info = extract_resume_info(text, known_skills)

    def fill_text(field: str, value: str) -> None:
        if value and not (getattr(profile, field, "") or "").strip():
            setattr(profile, field, value.strip())

    def as_url(handle: str) -> str:
        return handle if handle.startswith("http") else f"https://{handle}"

    # Contact + education
    fill_text("phone", info.phone)
    fill_text("degree", info.degree)
    if info.graduation_year and not profile.graduation_year:
        profile.graduation_year = info.graduation_year
    if info.cgpa and not profile.cgpa:
        profile.cgpa = info.cgpa

    # Colleges / universities (spaCy ORG entities, best-effort)
    if info.colleges:
        fill_text("college", info.colleges[0])
        if len(info.colleges) > 1:
            fill_text("university", info.colleges[1])

    # Social / portfolio links
    if info.github and not profile.github_url:
        profile.github_url = as_url(info.github)
    if info.linkedin and not profile.linkedin_url:
        profile.linkedin_url = as_url(info.linkedin)

    # Bio / summary
    fill_text("resume_summary", info.summary or info.objective)


def _run_ats_analysis(resume, known_skills: list) -> None:
    from resumes.analyzer import ATSScorer
    from accounts.models import ATSAnalysis

    result = ATSScorer().analyze(resume.raw_text, known_skills)
    ATSAnalysis.objects.update_or_create(
        resume=resume,
        defaults={
            "ats_score":          result["ats_score"],
            "completeness_score": result["completeness_score"],
            "formatting_score":   result["formatting_score"],
            "keyword_score":      result["keyword_score"],
            "experience_score":   result["experience_score"],
            "strengths":          result["strengths"],
            "weaknesses":         result["weaknesses"],
            "recommendations":    result["recommendations"],
            "section_scores":     result["section_scores"],
            "missing_sections":   result["missing_sections"],
        },
    )
    profile = getattr(resume.candidate, "candidate_profile", None)
    if profile:
        profile.ats_score = result["ats_score"]
        profile.save(update_fields=["ats_score"])


def _update_embedding(user, text: str) -> None:
    import json
    from matching.engine.semantic import SentenceTransformerMatcher
    from accounts.models import CandidateEmbedding

    matcher = SentenceTransformerMatcher()
    vec = matcher.embed(text)
    if not vec:
        return
    CandidateEmbedding.objects.update_or_create(
        user=user,
        defaults={
            "vector":     json.dumps(vec),
            "model_name": SentenceTransformerMatcher.model_name(),
        },
    )


def _resume_score(text: str, skill_count: int) -> int:
    length_score = min(len(text) / 2000.0, 1.0) * 50
    skill_score  = min(skill_count / 10.0,  1.0) * 50
    return int(round(length_score + skill_score))


def analyze_resume_text(text: str) -> dict:
    """Standalone ATS analysis without DB write — for preview endpoint."""
    from resumes.analyzer import ATSScorer
    known = list(Skill.objects.values_list("name", flat=True))
    return ATSScorer().analyze(text, known)
