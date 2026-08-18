# Honest evaluation of the shipped ranker artifact, leakage-safe split.
import os, django, numpy as np, joblib
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
os.environ["SQLITE_PATH"]="/tmp/db_audit.sqlite3"
django.setup()

from matching.ranking_model import FEATURE_ORDER, MODEL_PATH
from matching.training import _profile_meta, _build_feature_row
from accounts.models import CandidateProfile
from applications.models import Application
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import (accuracy_score, roc_auc_score, precision_score,
                             recall_score, f1_score, confusion_matrix, classification_report)
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
import sqlite3

N = int(os.environ.get("N","6000"))
profiles = list(CandidateProfile.objects.select_related("user").prefetch_related("user__resumes","skills")[:N])
print("profiles loaded:", len(profiles))
meta_by_user, text_by_user = {}, {}
for p in profiles:
    r = p.user.resumes.first()
    rt = (r.raw_text if r else "") or ""
    m = _profile_meta(p, rt)
    meta_by_user[p.user_id] = m
    text_by_user[p.user_id] = (rt[:4000].lower()+" "+" ".join(m["sk"])).strip()

uids = list(meta_by_user)
apps = list(Application.objects.filter(candidate_id__in=uids,
        status__in=[Application.Status.SHORTLISTED, Application.Status.REJECTED])
        .select_related("job").prefetch_related("job__required_skills")[:60000])
print("labelled pairs available:", len(apps))

job_text = {}; job_sk = {}
for a in apps:
    j=a.job
    if j.pk in job_text: continue
    sk={s.lower() for s in j.required_skills.values_list("name",flat=True)}
    job_sk[j.pk]=sk
    job_text[j.pk]=f"{j.title} {j.description or ''} "+" ".join(sk)

# --- LEAKAGE-SAFE: split pairs FIRST, fit TF-IDF on train docs only ---------
idx = np.arange(len(apps))
y = np.array([1 if a.status==Application.Status.SHORTLISTED else 0 for a in apps])
tr_i, te_i = train_test_split(idx, test_size=0.2, random_state=42, stratify=y)

tr_docs = sorted({text_by_user[apps[i].candidate_id] for i in tr_i} |
                 {job_text[apps[i].job_id].lower() for i in tr_i})
vec = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True, min_df=2, max_features=20000)
vec.fit(tr_docs)
print("tfidf vocab (train-only fit):", len(vec.vocabulary_))

def rows(ii):
    ct = vec.transform([text_by_user[apps[i].candidate_id] for i in ii])
    jt = vec.transform([job_text[apps[i].job_id].lower() for i in ii])
    sims = np.asarray(ct.multiply(jt).sum(axis=1)).ravel()  # both L2-normalised -> cosine
    X=[]
    for k,i in enumerate(ii):
        a=apps[i]
        X.append(_build_feature_row(meta_by_user[a.candidate_id], job_sk[a.job_id],
                                    a.job.title, sims[k], sims[k]))
    return np.array(X)

Xtr, Xte = rows(tr_i), rows(te_i)
ytr, yte = y[tr_i], y[te_i]
print(f"train={len(ytr)}  test={len(yte)}  pos_rate_train={ytr.mean():.4f} pos_rate_test={yte.mean():.4f}")

def report(name, yt, yp, proba=None):
    print(f"\n== {name} ==")
    print(f" accuracy  {accuracy_score(yt,yp):.4f}")
    print(f" precision {precision_score(yt,yp,zero_division=0):.4f}")
    print(f" recall    {recall_score(yt,yp,zero_division=0):.4f}")
    print(f" f1        {f1_score(yt,yp,zero_division=0):.4f}")
    if proba is not None:
        print(f" roc_auc   {roc_auc_score(yt,proba):.4f}")
    tn,fp,fn,tp = confusion_matrix(yt,yp).ravel()
    print(f" confusion tn={tn} fp={fp} fn={fn} tp={tp}")

# baseline
d = DummyClassifier(strategy="most_frequent").fit(Xtr,ytr)
report("BASELINE (majority class)", yte, d.predict(Xte))

# shipped artifact
shipped = joblib.load(MODEL_PATH)
report("SHIPPED ARTIFACT ranker.joblib (on this held-out split)",
       yte, shipped.predict(Xte), shipped.predict_proba(Xte)[:,1])

# retrained, same hyperparams
m = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=4,
                           class_weight="balanced", random_state=42, n_jobs=-1).fit(Xtr,ytr)
report("RETRAINED RF (leakage-safe, train-only TF-IDF fit)",
       yte, m.predict(Xte), m.predict_proba(Xte)[:,1])
print(" TRAIN accuracy:", round(accuracy_score(ytr,m.predict(Xtr)),4), "<- overfit check")

cv = cross_val_score(RandomForestClassifier(n_estimators=200,max_depth=12,min_samples_leaf=4,
        class_weight="balanced",random_state=42,n_jobs=-1),
        np.vstack([Xtr,Xte]), np.concatenate([ytr,yte]),
        cv=StratifiedKFold(5,shuffle=True,random_state=42), scoring="accuracy")
print(f"\n5-fold CV accuracy: mean={cv.mean():.4f} std={cv.std():.4f}  folds={np.round(cv,4)}")

print("\nfeature importances (retrained):")
for k,v in sorted(zip(FEATURE_ORDER, m.feature_importances_), key=lambda t:-t[1]):
    print(f"  {k:<16} {v:.4f}")
