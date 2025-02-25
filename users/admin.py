from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


admin.site.site_header = "SARN SGBV Management Admin"
admin.site.site_title = "SARN SGBV Management"
admin.site.index_title = "Welcome to the SARN SGBV Management System"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("email", "phone", "address")}),
        ("Roles & Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )
