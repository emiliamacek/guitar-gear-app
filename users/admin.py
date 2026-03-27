from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Musician Profile", {"fields": ("skill_level", "bio")}),
    )
    list_display = ["username", "email", "skill_level", "is_staff"]


admin.site.register(User, CustomUserAdmin)
