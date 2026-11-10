from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=settings.STUDENT_ID_REGEX,
                message="Enter a student ID in the format 02-131232-045.",
            )
        ],
    )

    def __str__(self):
        return f"{self.user.full_name} ({self.student_id})"
