import csv
import io
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from api.models import Report, Student

class ReportUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Carga un CSV con los campos:
        Estudiante, Persistente (1), Competente (1), Observador (1)
        Calcula automáticamente el score_total y asocia los reportes al docente autenticado.
        """
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({"error": "No se proporcionó un archivo CSV."}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({"error": "El archivo debe tener formato .csv"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        not_found_students = []
        created_reports = []

        for row in reader:
            student_name = (row.get('Estudiante') or '').strip()
            if not student_name:
                continue

            student = Student.objects.filter(full_name__iexact=student_name).first()
            if not student:
                not_found_students.append(student_name)
                continue

            # Extrae valores principales
            persistente = int(row.get('Persistente (1)', 0) or 0)
            competente = int(row.get('Competente (1)', 0) or 0)
            observador = int(row.get('Observador (1)', 0) or 0)

            report = Report.objects.create(
                teacher=request.user,
                student=student,
                persistente=persistente,
                competente=competente,
                observador=observador,
            )
            created_reports.append(report.id) # type: ignore

        return Response({
            "message": "Carga procesada correctamente.",
            "reportes_creados": len(created_reports),
            "no_encontrados": not_found_students
        }, status=status.HTTP_201_CREATED)
