from django.contrib import admin
# from import_export.admin import ImportExportActionModelAdmin
# from import_export import resources
# from import_export import fields
# from import_export.widgets import ForeignKeyWidget


# from backend.models import UserProfile

from .models import SpectrumField, SpectrumMeasurement, SpectrumPeak

# admin.site.register(UserProfile)


class SpectrumFieldAdmin(admin.ModelAdmin):
    pass


class SpectrumMeasurementAdmin(admin.ModelAdmin):
    pass


class SpectrumPeakAdmin(admin.ModelAdmin):
    pass


admin.site.register(SpectrumField, SpectrumFieldAdmin)
admin.site.register(SpectrumMeasurement, SpectrumMeasurementAdmin)
admin.site.register(SpectrumPeak, SpectrumPeakAdmin)
