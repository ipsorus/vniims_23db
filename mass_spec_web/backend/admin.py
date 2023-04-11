from django.contrib import admin
# from import_export.admin import ImportExportActionModelAdmin
# from import_export import resources
# from import_export import fields
# from import_export.widgets import ForeignKeyWidget


# from backend.models import UserProfile

from .models import SpectrumField, SpectrumMeasurement, SpectrumPeak, Spectrum


# admin.site.register(UserProfile)


class SpectrumFieldAdmin(admin.ModelAdmin):
    pass


class SpectrumMeasurementAdmin(admin.ModelAdmin):
    pass


class SpectrumPeakAdmin(admin.ModelAdmin):
    pass



class SpectrumFieldInline(admin.TabularInline):
    model = SpectrumField


class SpectrumMeasurementInline(admin.TabularInline):
    model = SpectrumMeasurement


class SpectrumPeakInline(admin.TabularInline):
    model = SpectrumPeak


class SpectrumAdmin(admin.ModelAdmin):
    inlines = [
        SpectrumPeakInline, SpectrumMeasurementInline, SpectrumFieldInline,
    ]


admin.site.register(SpectrumField, SpectrumFieldAdmin)
admin.site.register(SpectrumMeasurement, SpectrumMeasurementAdmin)
admin.site.register(SpectrumPeak, SpectrumPeakAdmin)
admin.site.register(Spectrum, SpectrumAdmin)
