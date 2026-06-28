from django.contrib.auth import get_user_model
from django.test import TestCase

from skills.models import Skill
from jobs.models import Job
from matching.services import recommend_jobs_for_candidate
from matching.skill_extraction import extract_skills

User = get_user_model()


class SkillExtractionTests(TestCase):
    def test_extracts_known_skills_with_variants(self):
        known = ["Python", "React", "TensorFlow"]
        text = "Built a project in python and reactjs using tensor flow."
        found = set(extract_skills(text, known))
        self.assertEqual(found, {"Python", "React", "TensorFlow"})


class MatchingTests(TestCase):
    def setUp(self):
        self.py = Skill.objects.create(name="Python")
        self.tf = Skill.objects.create(name="TensorFlow")
        self.react = Skill.objects.create(name="React")

        self.employer = User.objects.create_user(
            email="emp@demo.np", password="x", role=User.Role.EMPLOYER
        )
        self.ml_job = Job.objects.create(
            employer=self.employer, title="ML Engineer",
            description="Machine learning with TensorFlow and Python.",
        )
        self.ml_job.required_skills.set([self.py, self.tf])

        self.fe_job = Job.objects.create(
            employer=self.employer, title="Frontend Developer",
            description="Build UIs with React.",
        )
        self.fe_job.required_skills.set([self.react])

        self.candidate = User.objects.create_user(
            email="cand@demo.np", password="x", role=User.Role.CANDIDATE
        )
        self.candidate.candidate_profile.skills.set([self.py, self.tf])

    def test_ml_candidate_ranks_ml_job_first(self):
        results = recommend_jobs_for_candidate(self.candidate)
        self.assertTrue(results)
        self.assertEqual(results[0]["job"].id, self.ml_job.id)
        # ML job should clearly outscore the frontend job for this candidate.
        scores = {r["job"].id: r["score"] for r in results}
        self.assertGreater(scores[self.ml_job.id], scores[self.fe_job.id])
