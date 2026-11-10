from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, identify_hasher
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from apps.audit.models import AuditLog
from apps.accounts.models import User
from apps.employers.models import Company
from apps.accounts.permissions import require_role
from apps.accounts.services import (
    clear_login_failures,
    login_is_locked,
    record_login_failure,
)


class PasswordHashingTests(SimpleTestCase):
    @override_settings(
        PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
    )
    def test_password_is_stored_as_a_pbkdf2_hash(self):
        user = User(
            email="student@example.edu", full_name="Test Student", role="STUDENT"
        )
        user.set_password("InternTrack@123")
        self.assertNotEqual(user.password, "InternTrack@123")
        self.assertEqual(identify_hasher(user.password).algorithm, "pbkdf2_sha256")
        self.assertTrue(check_password("InternTrack@123", user.password))


class LoginLockoutTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_lockout_starts_after_five_failures_and_email_is_case_insensitive(self):
        for _ in range(4):
            self.assertFalse(record_login_failure("User@Example.edu"))
        self.assertFalse(login_is_locked("user@example.edu"))
        self.assertTrue(record_login_failure("user@example.edu"))
        self.assertTrue(login_is_locked("USER@example.edu"))

    def test_success_clears_lockout_counter(self):
        for _ in range(5):
            record_login_failure("user@example.edu")
        clear_login_failures("USER@example.edu")
        self.assertFalse(login_is_locked("user@example.edu"))


class RolePermissionTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_anonymous_role_page_redirects_to_login(self):
        @require_role(User.Role.STUDENT)
        def view(request):
            return HttpResponse("ok")

        request = self.factory.get("/student/")
        request.user = SimpleNamespace(is_authenticated=False)
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/login/?next=/student/")

    def test_wrong_role_is_denied(self):
        @require_role(User.Role.OFFICER)
        def view(request):
            return HttpResponse("ok")

        request = self.factory.get("/officer/")
        request.user = SimpleNamespace(
            is_authenticated=True, role=User.Role.STUDENT, pk=5
        )
        with patch("apps.accounts.permissions.record_event"):
            with self.assertRaises(PermissionDenied):
                view(request)

    def test_allowed_role_reaches_view(self):
        @require_role(User.Role.STUDENT)
        def view(request):
            return HttpResponse("ok")

        request = self.factory.get("/student/")
        request.user = SimpleNamespace(
            is_authenticated=True, role=User.Role.STUDENT, pk=5
        )
        self.assertEqual(view(request).content, b"ok")


class AccountFlowTests(TestCase):
    def test_inactive_account_cannot_log_in(self):
        User.objects.create_user(
            email="disabled@example.edu",
            password="InternTrack#2026",
            full_name="Disabled Member",
            role=User.Role.STUDENT,
            is_active=False,
        )
        response = self.client.post(
            "/login/",
            {"email": "disabled@example.edu", "password": "InternTrack#2026"},
        )
        self.assertContains(
            response, "This account is disabled. Contact the placement office."
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_student_registration_creates_account_and_student_id(self):
        response = self.client.post(
            "/register/student/",
            {
                "full_name": "Ayesha Khan",
                "email": "ayesha@example.edu",
                "student_id": "02-131232-045",
                "password1": "InternTrack#2026",
                "password2": "InternTrack#2026",
            },
        )
        self.assertRedirects(
            response, "/student/profile/", fetch_redirect_response=False
        )
        user = User.objects.get(email="ayesha@example.edu")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.check_password("InternTrack#2026"))
        self.assertEqual(user.studentprofile.student_id, "02-131232-045")

    def test_employer_registration_creates_pending_company(self):
        response = self.client.post(
            "/register/employer/",
            {
                "full_name": "Sara Ali",
                "email": "hr@techcorp.example",
                "password1": "InternTrack#2026",
                "password2": "InternTrack#2026",
                "company_name": "TechCorp",
                "industry": "Software",
                "website": "https://techcorp.example",
                "location": "Karachi",
                "contact_phone": "+922112345678",
                "description": "A software company hiring interns.",
            },
        )
        self.assertRedirects(
            response, "/employer/pending/", fetch_redirect_response=False
        )
        company = Company.objects.get(name="TechCorp")
        self.assertEqual(company.approval_status, Company.ApprovalStatus.PENDING)
        self.assertEqual(company.owner.role, User.Role.EMPLOYER)

    def test_login_is_throttled_after_five_bad_passwords(self):
        User.objects.create_user(
            email="member@example.edu",
            password="InternTrack#2026",
            full_name="Member",
            role=User.Role.STUDENT,
        )
        for _ in range(5):
            response = self.client.post(
                "/login/", {"email": "member@example.edu", "password": "wrong"}
            )
        self.assertContains(
            response, "Too many unsuccessful attempts. Try again later."
        )
        self.assertEqual(AuditLog.objects.filter(action="login_failed").count(), 5)

    @override_settings(DEBUG=False)
    def test_student_directly_opening_officer_page_is_forbidden_and_audited(self):
        user = User.objects.create_user(
            email="member@example.edu",
            password="InternTrack#2026",
            full_name="Member",
            role=User.Role.STUDENT,
        )
        self.client.force_login(user)
        response = self.client.get("/officer/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            AuditLog.objects.filter(
                actor=user, action="unauthorized_access_attempt"
            ).exists()
        )
