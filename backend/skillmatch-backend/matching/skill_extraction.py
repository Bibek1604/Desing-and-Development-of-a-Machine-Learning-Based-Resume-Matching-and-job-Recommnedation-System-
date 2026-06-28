"""Dictionary-based skill extraction.

A hybrid baseline: match a curated skill vocabulary against resume text using
word-boundary regex (handles common spelling variants). This is the recall-safe
half of the hybrid NER approach described in the thesis; a learned NER model can
be layered on top later.
"""
import re

# Common variant spellings normalised to a canonical skill name.
SKILL_ALIASES = {
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "nextjs": "Next.js",
    "next js": "Next.js",
    "node js": "Node.js",
    "nodejs": "Node.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "tensor flow": "TensorFlow",
    "js": "JavaScript",
    "ts": "TypeScript",
}


def _variants(skill_name: str) -> list[str]:
    base = skill_name.lower()
    variants = {base}
    # add alias spellings that map to this canonical skill
    for alias, canonical in SKILL_ALIASES.items():
        if canonical.lower() == base:
            variants.add(alias)
    return list(variants)


def extract_skills(text: str, known_skills) -> list:
    """Return the subset of `known_skills` whose name appears in `text`.

    `known_skills` is an iterable of skill names (str). Matching is
    case-insensitive and respects word boundaries.
    """
    if not text:
        return []
    haystack = text.lower()
    found = []
    for name in known_skills:
        for variant in _variants(name):
            pattern = r"(?<![a-z0-9])" + re.escape(variant) + r"(?![a-z0-9])"
            if re.search(pattern, haystack):
                found.append(name)
                break
    return found
