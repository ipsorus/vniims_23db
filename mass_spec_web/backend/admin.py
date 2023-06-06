from django.contrib import admin

from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import SpectrumMeasurement, Spectrum, Post, Tag, SpectrumTag, Library, Metadata, CustomUser, Support


class SpectrumFieldAdmin(admin.ModelAdmin):
    pass


class SpectrumMeasurementAdmin(admin.ModelAdmin):
    pass


class SpectrumPeakAdmin(admin.ModelAdmin):
    pass


class MetadataInline(admin.TabularInline):
    model = Metadata


class SpectrumMeasurementInline(admin.TabularInline):
    model = SpectrumMeasurement


class SpectrumAdmin(admin.ModelAdmin):
    inlines = [SpectrumMeasurementInline, MetadataInline]


class PostAdmin(admin.ModelAdmin):
    model = Post


class SupportAdmin(admin.ModelAdmin):
    model = Support


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
        (None, {"fields": ("username", "password", 'email', 'first_name', 'last_name', 'patronymic', 'organization', 'position', 'work_experience')}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", 'email', 'first_name', 'last_name', 'patronymic', 'organization', 'position', 'work_experience'
            )}
         ),
    )
    search_fields = ("username",)
    ordering = ("username",)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(SpectrumMeasurement, SpectrumMeasurementAdmin)
admin.site.register(Spectrum, SpectrumAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Support, SupportAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(SpectrumTag, SpectrumTagAdmin)
admin.site.register(Library, LibraryAdmin)
admin.site.register(Metadata, MetadataAdmin)
