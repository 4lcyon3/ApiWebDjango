from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth import authenticate
from .models import Teacher, Report, Student

# ==========================
# FORMULARIO: CREAR PROFESOR
# ==========================
class TeacherCreationForm(UserCreationForm):
    """
    Formulario para registrar nuevos profesores (usado en admin y vistas).
    Hereda de UserCreationForm, pero usa el modelo Teacher personalizado.
    """
    class Meta:
        model = Teacher
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'school',
            'password1',
            'password2',
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Teacher.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un profesor con este correo electrónico.")
        return email

class TeacherChangeForm(UserChangeForm):
    """
    Formulario para editar profesores existentes (usado en admin).
    """
    class Meta:
        model = Teacher
        fields = ['username', 'first_name', 'last_name', 'email', 'school', 'is_active', 'is_staff', 'is_superuser']

# ==========================
# FORMULARIO: LOGIN PROFESOR
# ==========================
class TeacherAuthenticationForm(AuthenticationForm):
    """
    Formulario de autenticación adaptado para el modelo Teacher.
    Valida username, password y school.
    """
    school = forms.CharField(required=True, label="Colegio")

    class Meta:
        model = Teacher
        fields = ['username', 'password', 'school']

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        school_name = cleaned_data.get('school')

        if username and password and school_name:
            try:
                teacher = Teacher.objects.select_related('school').get(
                    username=username,
                    school__fullname=school_name
                )
            except Teacher.DoesNotExist:
                raise forms.ValidationError("No existe un usuario asociado a ese colegio.")

            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Contraseña incorrecta.")
        return cleaned_data


# ==========================
# FORMULARIO: SUBIR REPORTE CSV
# ==========================
class ReportUploadForm(forms.Form):
    file = forms.FileField(required=True, help_text="Selecciona un archivo CSV con los datos semanales.")


# ==========================
# FORMULARIO: REGISTRAR ESTUDIANTE
# ==========================
class StudentForm(forms.ModelForm):
    """
    Formulario para registrar o actualizar estudiantes.
    """
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'school', 'teacher', 'puntaje', 'promedio', 'cant_evaluaciones']


# ==========================
# FORMULARIO: BUSCAR ESTUDIANTE
# ==========================
class StudentSearchForm(forms.Form):
    """
    Formulario para buscar estudiantes por nombre o colegio.
    """
    query = forms.CharField(label="Buscar estudiante", max_length=100, required=False)
    school = forms.CharField(label="Colegio", max_length=100, required=False)