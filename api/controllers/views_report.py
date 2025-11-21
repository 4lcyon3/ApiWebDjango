from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import csv, io

from api.models import Report, Student, Teacher
from api.serializers import ReportSerializer

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().select_related('student', 'teacher', 'school')
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Report.objects.all()
        # CORRECCIÓN: buscar Teacher por su user
        teacher = Teacher.objects.filter(user=user).first()
        if not teacher:
            return Report.objects.none()
        return Report.objects.filter(teacher=teacher)

    def perform_create(self, serializer):
        user = self.request.user
        teacher = Teacher.objects.filter(user=user).first()
        if not teacher:
            raise ValueError("Usuario no registrado como profesor")

        report = serializer.save(
            teacher=teacher,
            school=teacher.school,
            upload_date=timezone.now().date(),
            week_number=timezone.now().isocalendar()[1]
        )

        student = report.student
        # actualizar acumulados
        student.persistente_total += report.persistente
        student.competente_total += report.competente
        student.observador_total += report.observador
        student.score_total += report.score_total
        student.cant_evaluaciones = (student.cant_evaluaciones or 0) + 1
        student.save()

    # ------------------------------------------------------------------
    # PREVIEW CSV (no guarda, solo parsea y retorna detected / unmatched)
    # ------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='preview_csv', permission_classes=[permissions.IsAuthenticated])
    def preview_csv(self, request):
        """
        Recibe multipart/form-data con 'file' (CSV).
        No guarda nada: devuelve 'detected' y 'unmatched'.
        """
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No se envió archivo"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        teacher = Teacher.objects.filter(id=request.user.id).first()
        if not teacher:
            return Response({"error": "Usuario no es profesor"}, status=status.HTTP_403_FORBIDDEN)

        try:
            data = io.TextIOWrapper(file.file, encoding='utf-8')
            # Auto-detect delimiter and header using csv.Sniffer? We'll assume comma
            csv_reader = csv.DictReader(data)
        except Exception as e:
            return Response({"error": f"Error leyendo CSV: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        detected = []
        unmatched = []

        for row in csv_reader:
            # busco campo 'Estudiante' con distintas variantes
            student_name = (row.get("Estudiante") or row.get("Alumno") or "").strip()
            if not student_name:
                # intentar tomar la primera columna si no hay header "Estudiante"
                # row is a dict; find first non-empty value
                vals = [v for v in row.values() if v and str(v).strip()]
                if vals:
                    student_name = vals[0].strip()
            if not student_name:
                continue

            # split nombre
            parts = student_name.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

            # buscar student (case-insensitive) dentro de la misma escuela y teacher
            student = Student.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
                teacher=teacher,
                school=teacher.school
            ).first()

            # buscar columnas de puntaje con flexibilidad en header
            def get_int_from_row(keys):
                for k in keys:
                    val = row.get(k)
                    if val is None:
                        # try stripped keys
                        for rk, rv in row.items():
                            if rk and k.lower() in rk.lower():
                                val = rv
                                break
                    if val not in (None, ""):
                        try:
                            return int(val)
                        except ValueError:
                            # limpiar caracteres y reintentar
                            cleaned = ''.join(ch for ch in str(val) if ch.isdigit() or ch == "-")
                            try:
                                return int(cleaned) if cleaned else 0
                            except Exception:
                                return 0
                return 0

            persistente = get_int_from_row(["Persistente (1)", "Persistente", "persistente"])
            competente = get_int_from_row(["Competente (1)", "Competente", "competente"])
            observador = get_int_from_row(["Observador (1)", "Observador", "observador"])
            score_total = persistente + competente + observador

            item = {
                "full_name": student_name,
                "first_name": first_name,
                "last_name": last_name,
                "persistente": persistente,
                "competente": competente,
                "observador": observador,
                "score_total": score_total,
                "student_id": student.id if student else None, # type: ignore
            }

            if student:
                detected.append(item)
            else:
                unmatched.append({**item, "reason": "No registrado en la sección"})

        return Response({
            "detected": detected,
            "unmatched": unmatched,
            "mensaje": f"Se encontraron {len(detected)} alumnos vinculados y {len(unmatched)} no vinculados."
        }, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # BULK SAVE (confirma guardado de los detectados)
    # ------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='bulk_save', permission_classes=[permissions.IsAuthenticated])
    def bulk_save(self, request):
        """
        Espera payload:
        {
          "items": [
            {"student_id": 1, "persistente": 1, "competente": 2, "observador": 0, "score_total": 3},
            ...
          ]
        }
        Guarda reports y actualiza estudiantes.
        """
        user = request.user
        teacher = Teacher.objects.filter(id=request.user.id).first()
        if not teacher:
            return Response({"error": "Usuario no es profesor"}, status=status.HTTP_403_FORBIDDEN)

        items = request.data.get("items", [])
        if not isinstance(items, list):
            return Response({"error": "items debe ser una lista"}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        skipped = []
        with transaction.atomic():
            for it in items:
                sid = it.get("student_id")
                try:
                    student = Student.objects.get(id=sid, teacher=teacher, school=teacher.school)
                except Student.DoesNotExist:
                    skipped.append({"student_id": sid, "reason": "student no encontrado"})
                    continue

                persistente = int(it.get("persistente", 0) or 0)
                competente = int(it.get("competente", 0) or 0)
                observador = int(it.get("observador", 0) or 0)
                score_total = int(persistente + competente + observador)

                report = Report.objects.create(
                    student=student,
                    teacher=teacher,
                    persistente=persistente,
                    competente=competente,
                    observador=observador,
                    score_total=score_total,
                    upload_date=timezone.now().date(),
                    week_number=timezone.now().isocalendar()[1]
                )

                # actualizar acumulados
                student.persistente_total += persistente
                student.competente_total += competente
                student.observador_total += observador
                student.score_total += score_total # type: ignore
                student.cant_evaluaciones = (student.cant_evaluaciones or 0) + 1
                student.save()

                created.append(report.id) # type: ignore

        return Response({
            "created": created,
            "skipped": skipped,
            "mensaje": f"{len(created)} reportes creados, {len(skipped)} omitidos"
        }, status=status.HTTP_201_CREATED)