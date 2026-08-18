"""Reusable ranking-model training, shared by the CLI command and the admin
'Retrain' endpoint.

Trains a RandomForest over (candidate, job) pairs. Features use the SAME
ordering the live ranker consumes (``ranking_model.FEATURE_ORDER``) so the
saved artifact lines up exactly with inference.

Label source (in priority order):
  1. Real signals -- Application.status (SHORTLISTED=1, REJECTED=0) plus
     RecommendationFeedback.signal (UP=1, DOWN=0). These are the ground-truth
     labels the Phase-7 retraining loop is meant to consume.
  2. Synthetic fallback -- pairs against canonical JOB_SPECS labelled by
     ``preferred_role`` vs. job title match (a signal that is *not* also a
     ranker feature, so the model can't memorise its own input). Used when
     there aren't enough real signals to train on alone.

Both paths compute REAL SBERT semantic similarity (with graceful fallback
to TF-IDF) so training-time features match inference-time features -- the
old ``semantic_sim=0.0`` at train time was a train/serve skew bug.
"""
from __future__ import annotations

import logging
import random
import re

from matching.ranking_model import FEATURE_ORDER, MODEL_PATH, reload_model

log = logging.getLogger(__name__)

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

# Minimum real (positive, negative) counts to use the real-label path alone.
MIN_REAL_LABELS = 40


def _profile_meta(profile, resume_text):
    skills = {s.lower() for s in profile.skills.values_list("name", flat=True)}
    certs = [c for c in (profile.certifications or "").split(",")
             if c.strip() and c.strip() != "None"]
    yrs = [int(x) for x in re.findall(r"(\d+)\s*year", resume_text or "")]
    return {
        "sk": skills,
        "cg": float(profile.cgpa or 0) / 4.0,
        "int": 1 if "intern" in (resume_text or "") else 0,
        "gh": 1 if profile.github_url else 0,
        "cert": min(len(certs), 5) / 5.0,
        "skn": min(len(skills), 20) / 20.0,
        "exp": min((max(yrs) if yrs else 0) / 10.0, 1.0),
        "pref": (profile.preferred_role or "").lower(),
    }


def _build_feature_row(meta, job_skills, job_title, tfidf_sim, semantic_sim):
    overlap = len(meta["sk"] & job_skills) / len(job_skills) if job_skills else 0.0
    pref_match = 1 if meta["pref"] and meta["pref"].split()[0] in job_title.lower() else 0
    feats = {
        "skill_overlap":   overlap,
        "semantic_sim":    float(semantic_sim),
        "tfidf_sim":       float(tfidf_sim),
        "cgpa_norm":       meta["cg"],
        "has_internship":  meta["int"],
        "has_github":      meta["gh"],
        "cert_count":      meta["cert"],
        "skill_count":     meta["skn"],
        "exp_years":       meta["exp"],
        "preferred_match": pref_match,
    }
    return [feats[k] for k in FEATURE_ORDER]


def _pairs_from_real_signals():
    """Yield (user, job, label) tuples from persisted user signals."""
    try:
        from applications.models import Application, RecommendationFeedback
    except Exception:
        return
    shortlisted = Application.objects.filter(
        status=Application.Status.SHORTLISTED
    ).select_related("candidate", "job").prefetch_related("job__required_skills")
    for a in shortlisted:
        yield a.candidate, a.job, 1
    rejected = Application.objects.filter(
        status=Application.Status.REJECTED
    ).select_related("candidate", "job").prefetch_related("job__required_skills")
    for a in rejected:
        yield a.candidate, a.job, 0
    up = RecommendationFeedback.objects.filter(
        signal=RecommendationFeedback.Signal.UP
    ).select_related("user", "job").prefetch_related("job__required_skills")
    for fb in up:
        yield fb.user, fb.job, 1
    down = RecommendationFeedback.objects.filter(
        signal=RecommendationFeedback.Signal.DOWN
    ).select_related("user", "job").prefetch_related("job__required_skills")
    for fb in down:
        yield fb.user, fb.job, 0


def _semantic_matrix(cand_texts, job_texts):
    """Return (n_cand, n_job) SBERT cosine matrix, or None if unavailable."""
    try:
        from matching.engine.semantic import SentenceTransformerMatcher
        import numpy as np
        matcher = SentenceTransformerMatcher()
        if matcher._get_model() is None:
            return None
        cand_vecs = np.asarray(matcher.embed_batch(cand_texts))
        job_vecs = np.asarray(matcher.embed_batch(job_texts))
        if cand_vecs.size == 0 or job_vecs.size == 0:
            return None
        return cand_vecs @ job_vecs.T
    except Exception as exc:
        log.warning("SBERT unavailable during training (%s); using TF-IDF for semantic_sim.", exc)
        return None


def train_ranking_model(samples=800):
    """Train, persist, and version the ranking model. Returns a metrics dict."""
    from accounts.models import CandidateProfile
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        accuracy_score, roc_auc_score, precision_score,
        recall_score, f1_score, confusion_matrix,
    )
    from sklearn.metrics.pairwise import cosine_similarity
    from matching.engine.tfidf import build_vectorizer
    import numpy as np
    import joblib

    profiles = list(
        CandidateProfile.objects.select_related("user")
        .prefetch_related("user__resumes", "skills")[:samples]
    )
    if len(profiles) < 30:
        raise ValueError("Not enough candidates to train. Seed data first (seed_dataset_v3).")

    cand_meta = []
    cand_texts = []
    profile_by_user = {}
    for p in profiles:
        resume = p.user.resumes.first()
        rt = ((resume.raw_text if resume else "") or "")
        m = _profile_meta(p, rt)
        cand_meta.append(m)
        cand_texts.append((rt[:4000].lower() + " " + " ".join(m["sk"])).strip())
        profile_by_user[p.user_id] = (p, m, len(cand_meta) - 1)

    spec_texts = [t + " " + " ".join(s) for t, s in JOB_SPECS]
    spec_skill_sets = [s for _, s in JOB_SPECS]
    spec_titles = [t for t, _ in JOB_SPECS]

    # Same vectorizer config the serving path uses (engine/tfidf.py), so
    # tfidf_sim means the same thing at train time and at inference. Differing
    # max_features / token_pattern was a sixth train/serve skew.
    vec = build_vectorizer()
    matrix = vec.fit_transform(cand_texts + spec_texts)
    tfidf_c_x_spec = cosine_similarity(matrix[: len(cand_texts)],
                                       matrix[len(cand_texts):])

    sem_c_x_spec = _semantic_matrix(cand_texts, spec_texts)
    used_semantic = sem_c_x_spec is not None
    if not used_semantic:
        sem_c_x_spec = tfidf_c_x_spec

    # --- 1. Real-signal pairs ------------------------------------------------
    real_X, real_y = [], []
    real_used = 0
    for user, job, label in _pairs_from_real_signals():
        entry = profile_by_user.get(user.pk)
        if not entry:
            continue
        _profile, meta, idx = entry
        job_text = f"{job.title} {job.description or ''} " + " ".join(
            job.required_skills.values_list("name", flat=True)
        )
        job_skills = {s.lower() for s in job.required_skills.values_list("name", flat=True)}
        try:
            cand_vec = vec.transform([cand_texts[idx]])
            job_vec = vec.transform([job_text.lower()])
            tf = float(cosine_similarity(cand_vec, job_vec)[0, 0])
        except Exception:
            tf = 0.0
        if used_semantic:
            try:
                from matching.engine.semantic import SentenceTransformerMatcher
                sm = SentenceTransformerMatcher()
                sem = float(sm.similarity(cand_texts[idx], [job_text])[0])
            except Exception:
                sem = tf
        else:
            sem = tf
        real_X.append(_build_feature_row(meta, job_skills, job.title, tf, sem))
        real_y.append(label)
        real_used += 1

    pos_real = sum(real_y)
    neg_real = len(real_y) - pos_real
    have_enough_real = (pos_real >= MIN_REAL_LABELS and neg_real >= MIN_REAL_LABELS)

    # --- 2. Synthetic pairs (fallback only, when real signals are scarce) ----
    # Positive: preferred_role prefix matches spec title AND text sim in top 33%.
    # Negative: no preferred_role match AND text sim in bottom 33%.
    #
    # KNOWN LIMITATION -- READ BEFORE QUOTING ANY NUMBER FROM THIS PATH.
    # The label is a deterministic function of ``tf`` (feature ``tfidf_sim``)
    # and ``pref_match_title`` (feature ``preferred_match``). That is target
    # leakage: the classifier can recover the labelling rule from its own
    # inputs and scores ~99% accuracy / ~1.0 AUC, which measures nothing.
    #
    # A previous revision "solved" this by randomly inverting 33% of labels
    # after the split (LABEL_FLIP = 0.33) so that held-out accuracy landed in
    # the 60-70% band. That is accuracy manipulation, not a fix, and it has
    # been removed. Metrics from this path are NOT reportable; use the
    # real-signal path, or evaluate ranking quality with
    # ``manage.py evaluate_matcher`` instead.
    all_sims = tfidf_c_x_spec.flatten()
    hi_thr = float(np.quantile(all_sims, 0.66))
    lo_thr = float(np.quantile(all_sims, 0.33))

    syn_X, syn_y = [], []
    for i, meta in enumerate(cand_meta):
        for j, title in enumerate(spec_titles):
            tf = float(tfidf_c_x_spec[i, j])
            sem = float(sem_c_x_spec[i, j])
            pref = meta["pref"]
            pref_match_title = bool(
                pref and pref.split() and pref.split()[0] in title.lower()
            )
            if pref_match_title and tf >= hi_thr:
                label = 1
            elif (not pref_match_title) and tf <= lo_thr:
                label = 0
            else:
                continue
            syn_X.append(_build_feature_row(meta, spec_skill_sets[j], title, tf, sem))
            syn_y.append(label)

    # --- 3. Combine ---------------------------------------------------------
    if have_enough_real:
        X, y = real_X, real_y
        label_source = "real"
    else:
        X = real_X + syn_X
        y = real_y + syn_y
        label_source = "synthetic" if not real_used else "real+synthetic"

    pos, neg = sum(y), len(y) - sum(y)
    if pos < 10 or neg < 10:
        raise ValueError(f"Too few labelled samples (pos={pos}, neg={neg}).")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    # Hyperparameters selected by 5-fold CV on the TRAINING split only; the
    # test split is scored once, at the end. Two changes over the previous
    # configuration, both measured on the real-signal labels:
    #   * class_weight="balanced" removed  -- it cost ~1.5pp accuracy by
    #     over-predicting the minority class on a genuinely noisy label.
    #   * max_depth 12 -> 6, min_samples_leaf 4 -> 20 -- the deep forest was
    #     memorising noise (train 0.76 vs test 0.65); the shallow one closes
    #     that gap almost entirely.
    model = RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=20,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    acc = float(accuracy_score(y_te, y_pred))
    try:
        auc = float(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))
    except ValueError:
        auc = 0.0
    prec = float(precision_score(y_te, y_pred, zero_division=0))
    rec = float(recall_score(y_te, y_pred, zero_division=0))
    f1 = float(f1_score(y_te, y_pred, zero_division=0))
    tn, fp, fn, tp = (int(v) for v in confusion_matrix(y_te, y_pred).ravel())
    importances = {k: round(float(v), 4)
                   for k, v in zip(FEATURE_ORDER, model.feature_importances_)}

    # Majority-class accuracy on the same test split. Accuracy on an imbalanced
    # label is meaningless without it -- report both or neither.
    baseline = float(max(sum(y_te) / len(y_te), 1 - sum(y_te) / len(y_te)))
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    cv_scores = cross_val_score(
        RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=20,
                               random_state=42, n_jobs=-1),
        X_tr, y_tr, cv=StratifiedKFold(5, shuffle=True, random_state=42),
        scoring="accuracy",
    )
    train_acc = float(accuracy_score(y_tr, model.predict(X_tr)))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    metrics = {
        "accuracy":     round(acc, 4),
        "train_accuracy":    round(train_acc, 4),
        "baseline_accuracy": round(baseline, 4),
        "lift_over_baseline": round(acc - baseline, 4),
        "cv_accuracy_mean":  round(float(cv_scores.mean()), 4),
        "cv_accuracy_std":   round(float(cv_scores.std()), 4),
        "auc":          round(auc, 4),
        "precision":    round(prec, 4),
        "recall":       round(rec, 4),
        "f1":           round(f1, 4),
        "confusion":    {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "n_samples":    len(y),
        "n_candidates": len(profiles),
        "positives":    pos,
        "negatives":    neg,
        "feature_importances": importances,
        "label_source":    label_source,
        "real_pairs_used": real_used,
        "used_semantic":   used_semantic,
    }

    version = None
    try:
        from matching.models import ModelVersion
        last = ModelVersion.objects.order_by("-version").first()
        version = (last.version + 1) if last else 1
    except Exception:
        version = None

    joblib.dump(model, MODEL_PATH)
    if version is not None:
        joblib.dump(model, MODEL_PATH.parent / f"ranker_v{version}.joblib")
    reload_model()

    if version is not None:
        try:
            from matching.models import ModelVersion
            ModelVersion.objects.update(is_active=False)
            ModelVersion.objects.create(version=version, is_active=True, **{
                k: v for k, v in metrics.items()
                if k in {
                    "accuracy", "auc", "n_samples", "n_candidates",
                    "positives", "negatives", "feature_importances",
                }
            })
        except Exception:
            version = None
    metrics["version"] = version
    return metrics


def rollback_to_version(version):
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
