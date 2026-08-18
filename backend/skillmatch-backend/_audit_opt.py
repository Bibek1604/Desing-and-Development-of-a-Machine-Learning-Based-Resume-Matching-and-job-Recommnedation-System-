# Legitimate optimisation: model selection by CV on TRAIN ONLY; test touched once.
import os, django, numpy as np
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
django.setup()
from matching.training import _profile_meta
from accounts.models import CandidateProfile
from applications.models import Application
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (accuracy_score, roc_auc_score, precision_score,
                             recall_score, f1_score, confusion_matrix)

N=int(os.environ.get("N","20000"))
profiles=list(CandidateProfile.objects.select_related("user").prefetch_related("user__resumes","skills")[:N])
meta={}; text={}
for p in profiles:
    r=p.user.resumes.first(); rt=(r.raw_text if r else "") or ""
    m=_profile_meta(p,rt); meta[p.user_id]=m
    text[p.user_id]=(rt[:4000].lower()+" "+" ".join(m["sk"])).strip()
apps=list(Application.objects.filter(candidate_id__in=list(meta),
    status__in=[Application.Status.SHORTLISTED,Application.Status.REJECTED])
    .select_related("job").prefetch_related("job__required_skills")[:80000])
print("pairs:",len(apps))
jt={}; jsk={}
for a in apps:
    j=a.job
    if j.pk in jt: continue
    sk={s.lower() for s in j.required_skills.values_list("name",flat=True)}
    jsk[j.pk]=sk; jt[j.pk]=(f"{j.title} {j.description or ''} "+" ".join(sk)).lower()

y=np.array([1 if a.status==Application.Status.SHORTLISTED else 0 for a in apps])
tr,te=train_test_split(np.arange(len(apps)),test_size=0.2,random_state=42,stratify=y)

vec=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,min_df=2,max_features=20000)
vec.fit(sorted({text[apps[i].candidate_id] for i in tr}|{jt[apps[i].job_id] for i in tr}))

def feats(ii):
    C=vec.transform([text[apps[i].candidate_id] for i in ii])
    J=vec.transform([jt[apps[i].job_id] for i in ii])
    sim=np.asarray(C.multiply(J).sum(axis=1)).ravel()
    rows=[]
    for k,i in enumerate(ii):
        a=apps[i]; m=meta[a.candidate_id]; js=jsk[a.job_id]
        inter=m["sk"]&js
        rows.append([
            len(inter)/len(js) if js else 0.0,            # 0 skill_overlap (frac) - existing
            float(sim[k]), float(sim[k]),                  # 1,2 semantic_sim, tfidf_sim - existing
            m["cg"], m["int"], m["gh"], m["cert"], m["skn"], m["exp"],  # 3..8 existing
            1 if m["pref"] and m["pref"].split() and m["pref"].split()[0] in a.job.title.lower() else 0, # 9
            float(len(inter)),                             # 10 NEW raw shared-skill count
            float(len(inter)>=1),                          # 11 NEW has-any-shared-skill
            len(inter)/max(1,len(m["sk"]|js)),             # 12 NEW jaccard
        ])
    return np.array(rows)

Xtr,Xte=feats(tr),feats(te)
ytr,yte=y[tr],y[te]
print(f"train={len(ytr)} test={len(yte)} pos_rate={ytr.mean():.4f}")
CUR=list(range(10)); NEW=list(range(13)); LEAN=[0,10,11,12,1]
cvk=StratifiedKFold(5,shuffle=True,random_state=42)

def cv(name,est,cols):
    s=cross_val_score(est,Xtr[:,cols],ytr,cv=cvk,scoring="accuracy",n_jobs=-1)
    print(f"  {name:<46} CV acc {s.mean():.4f} +/- {s.std():.4f}")
    return s.mean()

print("\n--- MODEL SELECTION (5-fold CV on TRAIN only) ---")
cv("Dummy majority", DummyClassifier(strategy="most_frequent"), CUR)
best=(None,-1)
cands={
 "RF current (10 feat, depth12, balanced)": (RandomForestClassifier(n_estimators=300,max_depth=12,min_samples_leaf=4,class_weight="balanced",random_state=42,n_jobs=-1),CUR),
 "RF current feats, NO class_weight":       (RandomForestClassifier(n_estimators=300,max_depth=12,min_samples_leaf=4,random_state=42,n_jobs=-1),CUR),
 "RF +count/jaccard feats":                 (RandomForestClassifier(n_estimators=300,max_depth=12,min_samples_leaf=4,random_state=42,n_jobs=-1),NEW),
 "RF LEAN feats (drop noise cols)":         (RandomForestClassifier(n_estimators=300,max_depth=6,min_samples_leaf=20,random_state=42,n_jobs=-1),LEAN),
 "LogisticRegression LEAN":                 (make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000)),LEAN),
 "LogisticRegression all-new":              (make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000)),NEW),
 "LinearSVC LEAN":                          (make_pipeline(StandardScaler(),LinearSVC(max_iter=5000)),LEAN),
 "GaussianNB LEAN":                         (make_pipeline(StandardScaler(),GaussianNB()),LEAN),
 "HistGradientBoosting LEAN":               (HistGradientBoostingClassifier(max_depth=4,random_state=42),LEAN),
 "HistGradientBoosting all-new":            (HistGradientBoostingClassifier(max_depth=4,random_state=42),NEW),
}
for n,(e,c) in cands.items():
    m=cv(n,e,c)
    if m>best[1]: best=((n,e,c),m)
print(f"\nBEST by CV: {best[0][0]}  ({best[1]:.4f})")

print("\n--- FINAL: fit best on full TRAIN, evaluate ONCE on untouched TEST ---")
(nm,est,cols)=best[0]
est.fit(Xtr[:,cols],ytr); yp=est.predict(Xte[:,cols])
try: pr=est.predict_proba(Xte[:,cols])[:,1]
except Exception: pr=est.decision_function(Xte[:,cols])
tn,fp,fn,tp=confusion_matrix(yte,yp).ravel()
print(f" model      {nm}")
print(f" TRAIN acc  {accuracy_score(ytr,est.predict(Xtr[:,cols])):.4f}")
print(f" TEST acc   {accuracy_score(yte,yp):.4f}")
print(f" precision  {precision_score(yte,yp,zero_division=0):.4f}")
print(f" recall     {recall_score(yte,yp,zero_division=0):.4f}")
print(f" f1         {f1_score(yte,yp,zero_division=0):.4f}")
print(f" roc_auc    {roc_auc_score(yte,pr):.4f}")
print(f" confusion  tn={tn} fp={fp} fn={fn} tp={tp}")
print(f" baseline   {max(yte.mean(),1-yte.mean()):.4f}  (majority class)")
print(f" CEILING    0.6728  (Bayes-optimal given seeded 33% label flip)")
