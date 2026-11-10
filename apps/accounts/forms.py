import re

from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.employers.models import Company
from apps.students.models import StudentProfile


class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Full name")
    email = forms.EmailField(label="University email")
    password1 = forms.CharField(
        label="Password", strip=False, widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirm password", strip=False, widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control", "autocomplete": "on"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        domain = getattr(settings, "ALLOWED_STUDENT_EMAIL_DOMAIN", "")
        if (
            self.role == User.Role.STUDENT
            and domain
            and email.rsplit("@", 1)[-1] != domain
        ):
            raise ValidationError(f"Use your university email ending in {domain}.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password1")
        if password:
            try:
                password_validation.validate_password(password)
            except ValidationError as exc:
                self.add_error("password1", exc)
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "The passwords do not match.")
        return cleaned

    @transaction.atomic
    def save_user(self):
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            full_name=self.cleaned_data["full_name"].strip(),
            role=self.role,
        )


class StudentRegistrationForm(RegistrationForm):
    role = User.Role.STUDENT
    student_id = forms.CharField(max_length=20, label="Student ID")

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()
        if not re.fullmatch(settings.STUDENT_ID_REGEX, student_id):
            raise ValidationError("Enter a student ID in the format 02-131232-045.")
        if StudentProfile.objects.filter(student_id__iexact=student_id).exists():
            raise ValidationError("An account with this student ID already exists.")
        return student_id

    @transaction.atomic
    def save_user(self):
        user = super().save_user()
        StudentProfile.objects.create(
            user=user, student_id=self.cleaned_data["student_id"]
        )
        return user


class EmployerRegistrationForm(RegistrationForm):
    role = User.Role.EMPLOYER
    company_name = forms.CharField(max_length=180, label="Company name")
    industry = forms.CharField(max_length=100)
    website = forms.URLField(required=False)
    location = forms.CharField(max_length=160)
    contact_phone = forms.CharField(max_length=20, label="Company phone")
    description = forms.CharField(
        max_length=2000, widget=forms.Textarea(attrs={"rows": 4})
    )

    def clean_company_name(self):
        name = self.cleaned_data["company_name"].strip()
        if Company.objects.filter(name__iexact=name).exists():
            raise ValidationError("A company with this name is already registered.")
        return name

    @transaction.atomic
    def save_user(self):
        user = super().save_user()
        Company.objects.create(
            owner=user,
            name=self.cleaned_data["company_name"],
            industry=self.cleaned_data["industry"].strip(),
            website=self.cleaned_data["website"],
            description=self.cleaned_data["description"].strip(),
            location=self.cleaned_data["location"].strip(),
            contact_person=user.full_name,
            contact_phone=self.cleaned_data["contact_phone"].strip(),
        )
        return user


class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(
        label="Password", strip=False, widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "current-password"}
        )


class AccountPasswordChangeForm(PasswordChangeForm):
    pass
