from django.contrib.auth.views import PasswordChangeDoneView
from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.AccountLogoutView.as_view(), name="logout"),
    path("register/", views.registration_options, name="register"),
    path("register/student/", views.register_student, name="register_student"),
    path("register/employer/", views.register_employer, name="register_employer"),
    path(
        "account/password/",
        views.AccountPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "account/password/done/",
        PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path("student/", views.student_home, name="student_dashboard"),
    path("student/profile/", views.student_profile_placeholder, name="student_profile"),
    path("employer/", views.employer_home, name="employer_dashboard"),
    path("employer/pending/", views.employer_pending, name="employer_pending"),
    path("officer/", views.officer_home, name="officer_dashboard"),
]
