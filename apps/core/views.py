from django.shortcuts import render

from apps.accounts.models import User


def home(request):
    if request.user.is_authenticated:
        destinations = {
            User.Role.STUDENT: "student_profile",
            User.Role.EMPLOYER: "employer_pending",
            User.Role.OFFICER: "officer_dashboard",
        }
        from django.shortcuts import redirect

        return redirect(destinations.get(request.user.role, "home"))
    return render(request, "home.html")
