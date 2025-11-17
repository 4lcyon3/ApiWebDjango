from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    District,
    School,
    Teacher,
    Student,
    Report,
    MLModelVersion,
    Prediction,
    TeacherStudentPrediction,
)

# =====================
# ADMIN: DISTRITO
# =====================
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('description',)


# =====================
# ADMIN: COLEGIO
# =====================
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'fullname', 'district')
    list_filter = ('district',)
    search_fields = ('fullname',)


# =====================
# ADMIN: PROFESOR
# =====================
@admin.register(Teacher)
class TeacherAdmin(UserAdmin):

    list_display = (
        'id', 'username', 'first_name', 'last_name',
        'email', 'school', 'is_active', 'is_staff'
    )

    list_filter = ('school', 'is_active', 'is_staff')

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {
            "fields": ("first_name", "last_name", "email")
        }),
        ("School Info", {
            "fields": ("school",)
        }),
        ("Permissions", {
            "fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions"
            )
        }),
        ("Important dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "first_name",
                "last_name",
                "email",
                "school",
                "password1",
                "password2",
                "is_staff",
                "is_active",
                "is_superuser",
                "groups"
            ),
        }),
    )


# =====================
# ADMIN: ESTUDIANTE
# =====================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'first_name',
        'last_name',
        'puntaje',
        'promedio',
        'cant_evaluaciones',
        'score_total',
        'teacher',
        'school',
    )
    list_filter = ('school', 'teacher')
    search_fields = ('first_name', 'last_name')


# =====================
# ADMIN: REPORTE
# =====================
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'teacher',
        'student',
        'persistente',
        'competente',
        'observador',
        'score_total',
        'upload_date',
        'week_number',
    )
    list_filter = ('upload_date', 'week_number', 'teacher__school')
    search_fields = ('student__first_name', 'student__last_name', 'teacher__username')
    ordering = ('-upload_date',)


# =====================
# ADMIN: MODELO ML
# =====================
@admin.register(MLModelVersion)
class MLModelVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'version_name', 'training_date', 'performance_metric')
    search_fields = ('version_name',)
    ordering = ('-training_date',)


# =====================
# ADMIN: PREDICCIÓN
# =====================
@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'value', 'timestamp', 'model_version')
    list_filter = ('model_version',)
    search_fields = ('value',)


# =====================
# ADMIN: RELACIÓN PROFESOR - ALUMNO - REPORTE - PREDICCIÓN
# =====================
@admin.register(TeacherStudentPrediction)
class TeacherStudentPredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'teacher', 'student', 'report', 'prediction')
    list_filter = ('teacher__school', 'prediction__model_version')
    search_fields = ('teacher__username', 'student__first_name', 'student__last_name')
