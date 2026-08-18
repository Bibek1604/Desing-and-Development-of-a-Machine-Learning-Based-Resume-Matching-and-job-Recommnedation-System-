# Exercise the LIVE inference path end-to-end and inspect the score distribution.
import os, time, django, numpy as np
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
django.setup()
from accounts.models import CandidateProfile
from matching.services import recommend_jobs_for_candidate
from matching.ranking_model import CandidateJobRanker, _get_model
print("model artifact loaded:", _get_model() is not None)
profs=list(CandidateProfile.objects.select_related("user")[:12])
allsc=[]
for p in profs[:6]:
    t=time.time(); recs=recommend_jobs_for_candidate(p.user, limit=10); dt=time.time()-t
    sc=[r["score"] for r in recs]; allsc+=sc
    ordered = sc==sorted(sc,reverse=True)
    print(f"user {p.user_id:<6} n={len(recs):<3} {dt*1000:7.0f} ms  scores={sc}  desc_sorted={ordered}")
a=np.array(allsc)
print(f"\nlive score distribution: min={a.min()} max={a.max()} mean={a.mean():.1f} median={np.median(a):.0f}")
print(f"fraction >= 70 (frontend 'Recommended' threshold): {(a>=70).mean():.3f}")
# score() vs explain() consistency
u=profs[0].user
from jobs.models import Job
j=Job.objects.filter(is_active=True).prefetch_related("required_skills").first()
r=CandidateJobRanker()
print(f"\nSAME (user,job):  score()={r.score(u,j)}   explain()['score']={r.explain(u,j)['score']}")
