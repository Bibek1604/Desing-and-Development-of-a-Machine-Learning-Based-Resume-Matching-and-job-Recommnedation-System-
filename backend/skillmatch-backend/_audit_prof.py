import os, django, cProfile, pstats, io
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
django.setup()
from accounts.models import CandidateProfile
from matching.services import recommend_jobs_for_candidate
from matching.index import get_job_index
get_job_index()  # warm
u=CandidateProfile.objects.select_related("user")[4].user
recommend_jobs_for_candidate(u, limit=10)  # warm
pr=cProfile.Profile(); pr.enable()
recommend_jobs_for_candidate(u, limit=10)
pr.disable()
s=io.StringIO(); pstats.Stats(pr,stream=s).sort_stats("cumulative").print_stats(18)
print("\n".join(s.getvalue().split("\n")[:34]))
