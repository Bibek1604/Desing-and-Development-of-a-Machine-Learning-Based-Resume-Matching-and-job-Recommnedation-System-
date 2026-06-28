"""Reusable ranking-model training, shared by the CLI command and the admin
'Retrain' endpoint.

Trains a RandomForest over (candidate, job) pairs built from the seeded
candidates and a representative job per role family. Features use the SAME
ordering the live ranker consumes (``ranking_model.FEATURE_ORDER``) so the
saved artifact lines up exactly with inference. TF-IDF similarity is computed
in one batched fit (fast even for thousands of candidates).
"""
from __future__ import annotations

import re

from matching.ranking_model import FEATURE_ORDER, MODEL_PATH, reload_model

# One representative job per IT role family (title, required-skill set).
JOB_SPECS = [
    ("Backend Developer",        {"python", "django", "postgresql", "rest apis", "docker", "mysql"}),
    ("Frontend Developer",       {"javascript", "react", "typescript", "css", "tailwind", "next.js"}),
    ("Full-Stack Developer",     {"javascript", "react", "node.js", "mongodb", "express.js"}),
    ("Mobile App Developer",     {"kotlin", "flutter", "firebase", "java", "dart"}),
    ("DevOps Engineer",          {"docker", "kubernetes", "aws", "ci/cd", "terraform", "linux"}),
    ("Data Scientist",           {"python", "pandas", "scikit-learn", "sql", "machine learning"}),
    ("QA Automation Engineer",   {"selenium", "cypress", "jest", "postman", "python"}),
    ("UI/UX Designer",           {"figma", "adobe xd", "wireframing", "prototyping", "user research"}),
    ("Network Engineer",         {"ccna", "routing", "switching", "tcp/ip", "firewalls"}),
    ("System Administrator",     {"linux", "windows server", "bash", "vmware", "nginx"}),
    ("Cybersecurity Analyst",    {"penetration testing", "kali linux", "nmap", "owasp", "siem"}),
    ("Cloud Engineer",           {"aws", "azure", "terraform", "kubernetes", "docker"}),
]


def train_ranking_model(samples: int = 800) -> dict:
    """Train, persist, and version the ranking model. Returns a metrics dict."""
    from accounts.models import CandidateProfile
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import joblib

    profiles = list(
        CandidateProfile.objects.select_related("user")
        .prefetch_related("user__resumes", "skills")[:samples]
    )
    if len(profiles) < 30:
        raise ValueError("Not enough candidates to train. Seed data first (seed_dataset_v3).")

    job_texts = [t + " " + " ".join(s) for t, s in JOB_SPECS]

    texts, meta = [], []
    for p in profiles:
        resume = p.user.resumes.first()
        rt = ((resume.raw_text if resume else "") or "")[:4000].lower()
        skills = {s.lower() for s in p.skills.values_list("name", flat=True)}
        texts.append(rt + " " + " ".join(skills))
        certs = [c for c in (p.certifications or "").split(",") if c.strip() and c.strip() != "None"]
        yrs = [int(x) for x in re.findall(r"(\d+)\s*year", rt)]
        meta.append({
            "sk": skills,
            "cg": float(p.cgpa or 0) / 4.0,
            "int": 1 if "intern" in rt else 0,
            "gh": 1 if p.github_url else 0,
            "cert": min(len(certs), 5) / 5.0,
            "skn": min(len(skills), 20) / 20.0,
            "exp": min((max(yrs) if yrs else 0) / 10.0, 1.0),
            "pref": (p.preferred_role or "").lower(),
        })

    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2, max_features=20000)
    matrix = vec.fit_transform(texts + job_texts)
    sim = cosine_similarity(matrix[: len(texts)], matrix[len(texts):])

    X, y = [], []
    for i, m in enumerate(meta):
        for j, (title, js) in enumerate(JOB_SPECS):
            overlap = len(m["sk"] & js) / len(js) if js else 0.0
            if overlap >= 0.40:
                label = 1
            elif overlap <= 0.12:
                label = 0
            else:
                continue
            pref_match = 1 if m["pref"] and m["pref"].split()[0] in title.lower() else 0
            feats = {
                "skill_overlap": overlap, "semantic_sim": 0.0, "tfidf_sim": float(sim[i, j]),
                "cgpa_norm": m["cg"], "has_internship": m["int"], "has_github": m["gh"],
                "cert_count": m["cert"], "skill_count": m["skn"], "exp_years": m["exp"],
                "preferred_match": pref_match,
            }
            X.append([feats[k] for k in FEATURE_ORDER])
            y.append(label)

    pos, neg = sum(y), len(y) - sum(y)
    if pos < 10 or neg < 10:
        raise ValueError(f"Too few labelled samples (pos={pos}, neg={neg}).")

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=4,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    model.fit(X_tr, y_tr)
    acc = float(accuracy_score(y_te, model.predict(X_te)))
    try:
        auc = float(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))
    except ValueError:
        auc = 0.0
    importances = {k: round(float(v), 4) for k, v in zip(FEATURE_ORDER, model.feature_importances_)}

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    metrics = {
        "accuracy": round(acc, 4), "auc": round(auc, 4),
        "n_samples": len(y), "n_candidates": len(profiles),
        "positives": pos, "negatives": neg, "feature_importances": importances,
    }

    # Determine the next version number (best-effort; table may be unmigrated).
    version = None
    try:
        from matching.models import ModelVersion
        last = ModelVersion.objects.order_by("-version").first()
        version = (last.version + 1) if last else 1
    except Exception:  # noqa: BLE001
        version = None

    # Save the live artifact + a per-version copy so rollback can restore it.
    joblib.dump(model, MODEL_PATH)
    if version is not None:
        joblib.dump(model, MODEL_PATH.parent / f"ranker_v{version}.joblib")
    reload_model()

    if version is not None:
        try:
            from matching.models import ModelVersion
            ModelVersion.objects.update(is_active=False)
            ModelVersion.objects.create(version=version, is_active=True, **metrics)
        except Exception:  # noqa: BLE001
            version = None
    metrics["version"] = version
    return metrics


def rollback_to_version(version: int) -> dict:
    """Activate a previously-trained model version by restoring its artifact."""
    import shutil
    from matching.models import ModelVersion

    src = MODEL_PATH.parent / f"ranker_v{version}.joblib"
    if not src.exists():
        raise ValueError(f"No saved artifact for version {version} (it predates per-version saving).")
    shutil.copyfile(src, MODEL_PATH)
    reload_model()
    ModelVersion.objects.update(is_active=False)
    ModelVersion.objects.filter(version=version).update(is_active=True)
    return {"version": version, "is_active": True}
