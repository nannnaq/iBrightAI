from django.contrib import admin
from .models import Patient, CornealTopography, ACCustomization, ReviewResult, BasicParams
from django.contrib.admin.sites import AdminSite


admin.site.site_header = '后台管理系统'
admin.site.site_title = '后台管理系统'
admin.site.index_title = '后台管理系统'


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    model_icon = "fa fa-user"
    list_display = ("name", "age", "gender", "phone")
    search_fields = ("name", "phone")


@admin.register(BasicParams)
class BasicParamsAdmin(admin.ModelAdmin):
    list_display = ("patient", "lens_type", "overall_diameter", "optical_zone_diameter", "ac_arc_width")
    search_fields = ("eye", )


@admin.register(CornealTopography)
class CornealTopographyAdmin(admin.ModelAdmin):
    list_display = ("patient", "eye", "flat_k", "steep_k", "plane_angle")
    list_filter = ("patient", "eye")


@admin.register(ACCustomization)
class ACCustomizationAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "eye",
        "ac_arc_k1",
        "ac_arc_k2",
        "ac_arc_k3",
        "ac_arc_k4",
        "axis",
    )
    list_filter = ("patient", "eye")


@admin.register(ReviewResult)
class ReviewResultAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "eye",
        "adaptation_status",
        "post_adjustment",
        "satisfaction_level",
        "review_date",
    )
    list_filter = ("patient", "eye", "review_date")


