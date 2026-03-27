from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    SKILL_LEVEL_CHOICES = [
        ("BEGINNER", "Beginner"),
        ("INTERMEDIATE", "Intermediate"),
        ("PROFESSIONAL", "Professional"),
        ("VIRTUOSO", "Virtuoso"),
    ]

    # AbstractUser has 'username', 'email', 'first_name'.
    skill_level = models.CharField(
        choices=SKILL_LEVEL_CHOICES, max_length=20, default="BEGINNER"
    )

    bio = models.TextField(blank=True, help_text="Tell something about yourself")

    def __str__(self):
        return self.username

    class Meta:
        db_table = "users_user"
