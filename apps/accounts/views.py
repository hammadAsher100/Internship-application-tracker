import logging
import hashlib

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from apps.accounts.forms import (
    AccountPasswordChangeForm,
    EmailLoginForm,
    EmployerRegistrationForm,
    StudentRegistrationForm,
)
from apps.accounts.models import User
from apps.accounts.permissions import require_role
from apps.accounts.services import (
    clear_login_failures,
    login_is_locked,
    record_login_failure,
)
from apps.audit.services import record_event

logger = logging.getLogger(__name__)


def _email_fingerprint(email):
    return hashlib.sha256(email.casefold().encode()).hexdigest()


def _role_url(user):
    if user.role == User.Role.STUDENT:
        return "/student/profile/"
    if user.role == User.Role.EMPLOYER:
        return "/employer/pending/"
    return "/officer/"


def register_student(request):
    if request.user.is_authenticated:
        return redirect(_role_url(request.user))
    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save_user()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(
            request, "Complete your profile and upload a CV before applying."
        )
        return redirect("student_profile")
    return render(
        request, "accounts/register.html", {"form": form, "role_label": "Student"}
    )


def register_employer(request):
    if request.user.is_authenticated:
        return redirect(_role_url(request.user))
    form = EmployerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save_user()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(
            request,
            "Your employer account is registered. Complete company details next.",
        )
        return redirect("employer_pending")
    return render(
        request, "accounts/register.html", {"form": form, "role_label": "Employer"}
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_role_url(request.user))
    form = EmailLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        if login_is_locked(email):
            record_event(
                request,
                "login_locked",
                metadata={"email_hash": _email_fingerprint(email)},
            )
            messages.error(request, "Too many unsuccessful attempts. Try again later.")
        else:
            user_record = User.objects.filter(email__iexact=email).first()
            if user_record and not user_record.is_active:
                record_event(
                    request,
                    "login_failed",
                    target=user_record,
                    metadata={"reason": "inactive"},
                )
                messages.error(
                    request, "This account is disabled. Contact the placement office."
                )
            else:
                user = authenticate(
                    request, email=email, password=form.cleaned_data["password"]
                )
                if user is None:
                    email_hash = _email_fingerprint(email)
                    logger.warning("login_failed email_hash=%s", email_hash)
                    record_event(
                        request, "login_failed", metadata={"email_hash": email_hash}
                    )
                    if record_login_failure(email):
                        messages.error(
                            request, "Too many unsuccessful attempts. Try again later."
                        )
                    else:
                        messages.error(request, "Invalid email or password.")
                else:
                    clear_login_failures(email)
                    login(request, user)
                    record_event(request, "login_success", actor=user, target=user)
                    requested = request.POST.get("next") or request.GET.get("next")
                    if requested and url_has_allowed_host_and_scheme(
                        requested,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure(),
                    ):
                        return HttpResponseRedirect(requested)
                    return redirect(_role_url(user))
    return render(request, "accounts/login.html", {"form": form})


class AccountLogoutView(LogoutView):
    next_page = reverse_lazy("home")


class AccountPasswordChangeView(PasswordChangeView):
    form_class = AccountPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("password_change_done")


@login_required
def student_profile_placeholder(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    return render(
        request, "accounts/phase_placeholder.html", {"title": "Complete your profile"}
    )


@require_role(User.Role.EMPLOYER)
def employer_pending(request):
    return render(request, "accounts/employer_pending.html")


@require_role(User.Role.STUDENT)
def student_home(request):
    return render(
        request, "accounts/phase_placeholder.html", {"title": "Student dashboard"}
    )


@require_role(User.Role.EMPLOYER)
def employer_home(request):
    return render(
        request, "accounts/phase_placeholder.html", {"title": "Employer dashboard"}
    )


@require_role(User.Role.OFFICER)
def officer_home(request):
    return render(
        request,
        "accounts/phase_placeholder.html",
        {"title": "Placement office dashboard"},
    )


def registration_options(request):
    if request.user.is_authenticated:
        return redirect(_role_url(request.user))
    return render(request, "accounts/register_options.html")


def forbidden(request, exception=None):
    return render(request, "errors/403.html", status=403)
