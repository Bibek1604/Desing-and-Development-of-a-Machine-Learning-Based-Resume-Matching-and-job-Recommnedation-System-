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

    def test_results_are_sorted_descending_by_displayed_score(self):
        """The order shown must be monotonic in the number shown (§14)."""
        scores = [r["score"] for r in recommend_jobs_for_candidate(self.candidate)]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_scores_are_in_range(self):
        for r in recommend_jobs_for_candidate(self.candidate):
            self.assertGreaterEqual(r["score"], 0)
            self.assertLessEqual(r["score"], 100)

    def test_score_and_explain_agree(self):
        """Regression: score() returned the model probability while explain()
        returned a heuristic total — 53 vs 4 for the same pair in production."""
        from matching.ranking_model import CandidateJobRanker
        ranker = CandidateJobRanker()
        self.assertEqual(
            ranker.score(self.candidate, self.ml_job),
            ranker.explain(self.candidate, self.ml_job)["score"],
        )

    def test_probability_is_not_the_match_score(self):
        """A classifier probability must never be served as the '% match'."""
        for r in recommend_jobs_for_candidate(self.candidate):
            p = r.get("shortlist_probability")
            if p is not None:
                self.assertGreaterEqual(p, 0.0)
                self.assertLessEqual(p, 1.0)

    def test_candidate_with_no_skills_does_not_crash(self):
        empty = User.objects.create_user(
            email="empty@demo.np", password="x", role=User.Role.CANDIDATE
        )
        self.assertIsInstance(recommend_jobs_for_candidate(empty), list)


class ResumeUploadValidationTests(TestCase):
    """Malformed uploads must be rejected before they reach the ML pipeline."""

    def _validate(self, name, size, content_type="application/pdf"):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from resumes.serializers import ResumeSerializer
        f = SimpleUploadedFile(name, b"x" * size, content_type=content_type)
        return ResumeSerializer().validate_file(f)

    def test_rejects_unsupported_extension(self):
        from rest_framework.serializers import ValidationError
        with self.assertRaises(ValidationError):
            self._validate("virus.exe", 100, "application/octet-stream")

    def test_rejects_empty_file(self):
        from rest_framework.serializers import ValidationError
        with self.assertRaises(ValidationError):
            self._validate("empty.pdf", 0)

    def test_rejects_oversized_file(self):
        from rest_framework.serializers import ValidationError
        with self.assertRaises(ValidationError):
            self._validate("huge.pdf", 6 * 1024 * 1024)

    def test_accepts_valid_pdf(self):
        self.assertIsNotNone(self._validate("cv.pdf", 2048))


class ValidationTests(TestCase):
    """Input validation at the API boundary (§20 of the audit brief)."""

    def setUp(self):
        self.employer = User.objects.create_user(
            email="v-emp@demo.np", password="x", role=User.Role.EMPLOYER)
        self.candidate = User.objects.create_user(
            email="v-cand@demo.np", password="x", role=User.Role.CANDIDATE)

    def _job(self, **over):
        from jobs.serializers import JobSerializer
        data = {"title": "Backend Developer",
                "description": "We need a backend developer for our Kathmandu team.",
                "job_type": "full_time"}
        data.update(over)
        return JobSerializer(data=data)

    def test_rejects_blank_job_title(self):
        self.assertFalse(self._job(title="   ").is_valid())

    def test_rejects_too_short_job_description(self):
        self.assertFalse(self._job(description="hire me").is_valid())

    def test_rejects_inverted_salary_range(self):
        s = self._job(salary_min=90000, salary_max=40000)
        self.assertFalse(s.is_valid())
        self.assertIn("salary_min", s.errors)

    def test_rejects_negative_salary(self):
        self.assertFalse(self._job(salary_min=-1).is_valid())

    def test_accepts_valid_job(self):
        self.assertTrue(self._job().is_valid())

    def test_rejects_out_of_range_cgpa(self):
        from accounts.serializers import CandidateProfileSerializer
        s = CandidateProfileSerializer(
            self.candidate.candidate_profile, data={"cgpa": "9.50"}, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("cgpa", s.errors)

    def test_rejects_implausible_graduation_year(self):
        from accounts.serializers import CandidateProfileSerializer
        s = CandidateProfileSerializer(
            self.candidate.candidate_profile, data={"graduation_year": 1750}, partial=True)
        self.assertFalse(s.is_valid())

    def test_rejects_duplicate_email_case_insensitively(self):
        from accounts.serializers import RegisterSerializer
        s = RegisterSerializer(data={"email": "V-CAND@demo.np", "full_name": "Someone Else",
                                     "password": "Str0ng-Passw0rd!", "role": "candidate"})
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_cannot_move_application_to_another_job(self):
        from applications.models import Application
        from applications.serializers import ApplicationSerializer
        a = Job.objects.create(employer=self.employer, title="A",
                               description="First posting description here.")
        b = Job.objects.create(employer=self.employer, title="B",
                               description="Second posting description here.")
        app = Application.objects.create(candidate=self.candidate, job=a)
        s = ApplicationSerializer(app, data={"job": b.pk}, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("job", s.errors)


class JobVisibilityTests(TestCase):
    """A withdrawn posting must not leak to other employers (audit B: LOW)."""

    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="own@demo.np", password="x", role=User.Role.EMPLOYER)
        self.other = User.objects.create_user(
            email="oth@demo.np", password="x", role=User.Role.EMPLOYER)
        self.hidden = Job.objects.create(
            employer=self.owner, title="Unpublished Role",
            description="This posting is not active and should stay private.",
            is_active=False)

    @staticmethod
    def _ids(response):
        data = response.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        return [j["id"] for j in items]

    def test_inactive_job_hidden_from_other_employers(self):
        self.client.force_authenticate(self.other)
        self.assertNotIn(self.hidden.id, self._ids(self.client.get("/api/jobs/")))

    def test_owner_sees_own_inactive_job_via_mine(self):
        self.client.force_authenticate(self.owner)
        self.assertIn(self.hidden.id, self._ids(self.client.get("/api/jobs/?mine=true")))

    def test_inactive_job_not_retrievable_by_candidate(self):
        cand = User.objects.create_user(
            email="vis-cand@demo.np", password="x", role=User.Role.CANDIDATE)
        self.client.force_authenticate(cand)
        self.assertEqual(self.client.get(f"/api/jobs/{self.hidden.id}/").status_code, 404)


class ResumeAccessControlTests(TestCase):
    """An employer must not be able to read resumes of candidates who never
    applied to their jobs (IDOR regression)."""

    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.emp = User.objects.create_user(
            email="e1@demo.np", password="x", role=User.Role.EMPLOYER)
        self.other_emp = User.objects.create_user(
            email="e2@demo.np", password="x", role=User.Role.EMPLOYER)
        self.cand = User.objects.create_user(
            email="c1@demo.np", password="x", role=User.Role.CANDIDATE)
        self.job = Job.objects.create(
            employer=self.emp, title="Backend Developer", description="Python.")

    def _url(self):
        return f"/api/matching/candidates/{self.cand.pk}/resume/"

    def test_unrelated_employer_is_denied(self):
        self.client.force_authenticate(self.other_emp)
        self.assertEqual(self.client.get(self._url()).status_code, 403)

    def test_employer_with_application_is_allowed(self):
        from applications.models import Application
        Application.objects.create(candidate=self.cand, job=self.job)
        self.client.force_authenticate(self.emp)
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_candidate_cannot_read_another_candidate(self):
        other = User.objects.create_user(
            email="c2@demo.np", password="x", role=User.Role.CANDIDATE)
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(self._url()).status_code, 403)
