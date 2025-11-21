import requests # type: ignore
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from ..models import Report, Student

ML_SERVER_URL = "http://127.0.0.1:8180/api/predict/"

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def predict_student_performance(request, student_id):
    """
    Obtiene datos del estudiante desde el backend,
    llama al servidor ML y retorna un valor final de predicción.
    """

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Estudiante no encontrado"}, status=404)
    reports = Report.objects.filter(student=student)

    if not reports.exists():
        return JsonResponse({"error": "No hay reportes para este estudiante"}, status=400)


    payload = {
        "persistente": student.persistente_total,
        "competente": student.competente_total,
        "observador": student.observador_total,
    }

    try:
        ml_response = requests.post(ML_SERVER_URL, json=payload, timeout=5)
    except Exception:
        return JsonResponse({"error": "No se pudo conectar al servidor ML"}, status=500)

    try:
        ml_data = ml_response.json()
    except:
        return JsonResponse({"error": "Respuesta inválida del servidor ML"}, status=500)

    if ml_response.status_code != 200:
        return JsonResponse({"error": ml_data.get("error", "Error ML")}, status=500)

    return JsonResponse({
        "student_id": student_id,
        "prediction": ml_data.get("rendimiento_predicho") or ml_data.get("prediction"),
        "inputs_used": payload
    }, status=200)
