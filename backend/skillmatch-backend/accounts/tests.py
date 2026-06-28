from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AuthFlowTests(APITestCase):
    def test_register_creates_candidate_with_profile(self):
        resp = self.client.post("/api/auth/register/", {
            "email": "new@demo.np", "full_name": "New Grad",
            "role": "candidate", "password": "StrongPass123",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        user = User.objects.get(email="new@demo.np")
        self.assertTrue(hasattr(user, "candidate_profile"))

    def test_cannot_register_as_admin(self):
        resp = self.client.post("/api/auth/register/", {
            "email": "hacker@demo.np", "full_name": "X",
            "role": "admin", "password": "StrongPass123",
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_login_and_me(self):
        User.objects.create_user(email="a@demo.np", password="StrongPass123", full_name="A")
        login = self.client.post("/api/auth/login/", {
            "email": "a@demo.np", "password": "StrongPass123",
        }, format="json")
        self.assertEqual(login.status_code, 200, login.content)
        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["email"], "a@demo.np")
