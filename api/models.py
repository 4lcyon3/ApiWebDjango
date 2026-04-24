from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# =====================
# MODELO: DISTRITO
# =====================
class District(models.Model):
    description = models.CharField(max_length=50)

    def __str__(self):
        return self.description


# =====================
# MODELO: COLEGIO
# =====================
class School(models.Model):
    fullname = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='schools')

    def __str__(self):
        return self.fullname

# =====================
# MODELO: SECCIÓN
# =====================
class Section(models.Model):
    name = models.CharField(max_length=50, help_text="Ej: 1ro A, 2do B, 5to Ciencias")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='sections')
    grade_level = models.CharField(max_length=50, blank=True, null=True, help_text="Nivel educativo (Opcional)")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school', 'name') # Evita secciones duplicadas en el mismo colegio
        ordering = ['name']

    def __str__(self):
        return f"{self.school.fullname} - {self.name}"

# =====================
# MODELO: PROFESOR
# =====================
class Teacher(AbstractUser):
    """
    Usuario personalizado para profesores, con vínculo a School.
    Usa AbstractUser para compatibilidad con el sistema de autenticación de Django.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teachers', null=True)

    def __str__(self):
        return f"{self.username} ({self.school.fullname if self.school else 'Sin colegio'})"


# =====================
# MODELO: ESTUDIANTE
# =====================
class Student(models.Model):
    first_name = models.CharField(max_length=50, default="SinNombre")
    last_name = models.CharField(max_length=50, default="SinApellido")
    puntaje = models.IntegerField(default=0, null=True, blank=True)
    promedio = models.DecimalField(max_digits=5, decimal_places=2, default=0.00) # type: ignore
    persistente_total = models.IntegerField(default=0)
    competente_total = models.IntegerField(default=0)
    observador_total = models.IntegerField(default=0)
    cant_evaluaciones = models.IntegerField(default=0, null=True, blank=True)
    score_total = models.IntegerField(default=0, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='students')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.school.fullname})"


# =====================
# MODELO: REPORTE (CSV)
# =====================
class Report(models.Model):
    teacher = models.ForeignKey('api.Teacher', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    student = models.ForeignKey('api.Student', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)

    persistente = models.IntegerField(default=0)
    competente = models.IntegerField(default=0)
    observador = models.IntegerField(default=0)
    score_total = models.IntegerField(default=0)

    upload_date = models.DateField(default=timezone.now)
    week_number = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.week_number:
            self.week_number = self.upload_date.isocalendar()[1]
        self.score_total = self.persistente + self.competente + self.observador
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reporte de {self.student} (Semana {self.week_number})"


# =====================
# MODELO: VERSIÓN DE MODELO ML
# =====================
class MLModelVersion(models.Model):
    version_name = models.CharField(max_length=50)
    training_date = models.DateField(default=timezone.now)
    performance_metric = models.FloatField(default=0.0)

    def __str__(self):
        return self.version_name


# =====================
# MODELO: PREDICCIÓN
# =====================
class Prediction(models.Model):
    value = models.CharField(max_length=20)
    timestamp = models.DateTimeField(default=timezone.now)
    model_version = models.ForeignKey(MLModelVersion, on_delete=models.CASCADE, related_name='predictions', null=True, blank=True)

    def __str__(self):
        return f"Predicción {self.value} ({self.model_version.version_name})" # type: ignore


# =====================
# RELACIÓN: PROFESOR x ALUMNO x REPORTE x PREDICCIÓN
# =====================
class TeacherStudentPrediction(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, null=True, blank=True)
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.teacher.username} -> {self.student.first_name} ({self.prediction.value})"
