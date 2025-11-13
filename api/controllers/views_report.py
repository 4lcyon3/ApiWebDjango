from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import csv, io

from api.models import Report, Student, Teacher
from api.serializers import ReportSerializer
from api.permissions import IsTeacher, IsOwnerTeacherOrAdmin


class ReportViewSet(viewsets.ModelViewSet):
    """
    Vista para gestionar los reportes semanales de los alumnos.
    - Los profesores pueden subir CSVs o registrar reportes manualmente.
    - Los administradores pueden ver todos los reportes.
    - Se filtra automáticamente por profesor y escuela.
    """
    queryset = Report.objects.all().select_related('teacher', 'student', 'school')
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher | IsOwnerTeacherOrAdmin]

    # ------------------------------------------------------------------
    # Control de Querysets según tipo de usuario
    # ------------------------------------------------------------------
    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Report.objects.all().select_related('teacher', 'student', 'school')

        teacher = Teacher.objects.filter(user=user).first()
        if not teacher:
            return Report.objects.none()

        return Report.objects.filter(teacher=teacher)

    # ------------------------------------------------------------------
    # Crear reportes individuales
    # ------------------------------------------------------------------
    def perform_create(self, serializer):
        """
        Asigna automáticamente el profesor autenticado y su escuela al crear un reporte manual.
        """
        user = self.request.user
        teacher = Teacher.objects.filter(user=user).first()

        if not teacher:
            raise ValueError("El usuario autenticado no está registrado como profesor.")

        serializer.save(
            teacher=teacher,
            school=teacher.school,
            upload_date=timezone.now().date(),
            week_number=timezone.now().isocalendar().week
        )

    # ------------------------------------------------------------------
    # Subida de CSV
    # ------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='upload', permission_classes=[permissions.IsAuthenticated, IsTeacher])
    def upload_csv(self, request):
        """
        Permite subir un CSV con los reportes semanales de los alumnos.
        Estructura esperada del CSV:
        Estudiante, Persistente (1), Competente (1), Observador (1), ...
        """
        file = request.FILES.get('file')
        if not file:
            return Response(
                {"error": "No se envió ningún archivo CSV."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        teacher = Teacher.objects.filter(user=user).first()
        if not teacher:
            return Response(
                {"error": "El usuario no está registrado como profesor."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            data = io.TextIOWrapper(file.file, encoding='utf-8')
            csv_reader = csv.DictReader(data)
        except Exception as e:
            return Response(
                {"error": f"Error al leer el archivo CSV: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_reports = []
        not_found_students = []

        with transaction.atomic():
            for row in csv_reader:
                student_name = (row.get("Estudiante") or row.get("Alumno") or "").strip()
                if not student_name:
                    continue

                student = Student.objects.filter(
                    name__iexact=student_name,
                    school=teacher.school
                ).first()

                if not student:
                    not_found_students.append(student_name)
                    continue

                # Parseo robusto de valores
                def safe_int(value):
                    try:
                        return int(value) if value else 0
                    except ValueError:
                        return 0

                persistente = safe_int(row.get("Persistente (1)"))
                competente = safe_int(row.get("Competente (1)"))
                observador = safe_int(row.get("Observador (1)"))
                score_total = persistente + competente + observador

                report = Report.objects.create(
                    student=student,
                    teacher=teacher,
                    school=teacher.school,
                    persistente=persistente,
                    competente=competente,
                    observador=observador,
                    score_total=score_total,
                    upload_date=timezone.now().date(),
                    week_number=timezone.now().isocalendar().week
                )
                created_reports.append(report.id) # type: ignore

        response_data = {
            "mensaje": f"{len(created_reports)} reportes subidos correctamente.",
            "reportes_creados": created_reports,
            "no_encontrados": not_found_students or "Todos los alumnos fueron encontrados."
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # Filtros por semana y escuela
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='filter', permission_classes=[permissions.IsAuthenticated])
    def filter_reports(self, request):
        """
        Permite filtrar reportes por semana o escuela.
        Ejemplo: /api/reports/filter/?week=46&school=1
        """
        week = request.query_params.get('week')
        school_id = request.query_params.get('school')

        queryset = self.get_queryset()

        if week:
            queryset = queryset.filter(week_number=week)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

        if not queryset.exists():
            return Response(
                {"mensaje": "No se encontraron reportes con esos filtros."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
