from django.contrib import admin
# from import_export.admin import ImportExportActionModelAdmin
# from import_export import resources
# from import_export import fields
# from import_export.widgets import ForeignKeyWidget


# from backend.models import UserProfile
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import SpectrumMeasurement, Spectrum, Post, Tag, SpectrumTag, Library, Metadata, CustomUser


# admin.site.register(UserProfile)


class SpectrumFieldAdmin(admin.ModelAdmin):
    pass


class SpectrumMeasurementAdmin(admin.ModelAdmin):
    pass


class SpectrumPeakAdmin(admin.ModelAdmin):
    pass


# class ProfileInline(admin.TabularInline):
#     model = Profile
#
#
# class UserAdmin(admin.ModelAdmin):
#     inlines = [ProfileInline]


class MetadataInline(admin.TabularInline):
    model = Metadata


class SpectrumMeasurementInline(admin.TabularInline):
    model = SpectrumMeasurement


# class SpectrumPeakInline(admin.TabularInline):
#     model = SpectrumPeak


class SpectrumAdmin(admin.ModelAdmin):
    # inlines = [
    #     SpectrumPeakInline, SpectrumMeasurementInline, SpectrumFieldInline,
    # ]
    inlines = [SpectrumMeasurementInline, MetadataInline]


class PostAdmin(admin.ModelAdmin):
    model = Post


class TagAdmin(admin.ModelAdmin):
    model = Post


class SpectrumTagAdmin(admin.ModelAdmin):
    model = SpectrumTag


class LibraryAdmin(admin.ModelAdmin):
    model = Library


class MetadataAdmin(admin.ModelAdmin):
    model = Metadata


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("username", "is_staff", "is_active",)
    list_filter = ("username", "is_staff", "is_active",)
    fieldsets = (
        (None, {"fields": ("username", "password", 'email', 'first_name', 'last_name', 'organization', 'position', 'work_experience')}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", 'email', 'first_name', 'last_name', 'organization', 'position', 'work_experience'
            )}
         ),
    )
    search_fields = ("username",)
    ordering = ("username",)


admin.site.register(CustomUser, CustomUserAdmin)

# admin.site.register(SpectrumField, SpectrumFieldAdmin)
admin.site.register(SpectrumMeasurement, SpectrumMeasurementAdmin)

# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)

admin.site.register(Spectrum, SpectrumAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(SpectrumTag, SpectrumTagAdmin)
admin.site.register(Library, LibraryAdmin)
admin.site.register(Metadata, MetadataAdmin)
