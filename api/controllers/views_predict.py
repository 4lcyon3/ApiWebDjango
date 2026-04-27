import requests # type: ignore
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from ..models import Report, Student

# Asegúrate de que esta URL apunte a tu servidor ML (puerto 8180 u otro configurado)
ML_SERVER_URL = "http://127.0.0.1:8180/api/predict/"

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def predict_student_performance(request, student_id):
    """
    Obtiene datos acumulados del estudiante desde la BD,
    los envía al servidor de ML para inferencia,
    y retorna una predicción enriquecida (Nivel, Confianza, Recomendación).
    """
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Estudiante no encontrado"}, status=404)

    reports_count = Report.objects.filter(student=student)
    if not reports_count.exists():
        return JsonResponse({"error": "No hay reportes para este estudiante"}, status=400)

    if student.cant_evaluaciones is None or student.cant_evaluaciones == 0:
        cant_evaluaciones = 1 
    else:
        cant_evaluaciones = student.cant_evaluaciones

    payload = {
        "persistente": student.persistente_total,
        "competente": student.competente_total,
        "observador": student.observador_total,
        "cant_evaluaciones": cant_evaluaciones
    }

    # Validación básica de datos (evitar negativos)
    if any(v < 0 for v in payload.values()):
        return JsonResponse({"error": "Datos del estudiante inválidos (valores negativos)"}, status=400)

    # 4. Llamar al Servidor de ML
    try:
        ml_response = requests.post(ML_SERVER_URL, json=payload, timeout=5)
    except requests.exceptions.ConnectionError:
        return JsonResponse({"error": "No se pudo conectar al servidor de Machine Learning. Verifica que esté ejecutándose."}, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Tiempo de espera agotado al contactar al servidor ML."}, status=504)
    except Exception as e:
        return JsonResponse({"error": f"Error interno al conectar con ML: {str(e)}"}, status=500)

    try:
        ml_data = ml_response.json()
    except ValueError:
        return JsonResponse({"error": "Respuesta inválida (no JSON) del servidor ML"}, status=500)

    if ml_response.status_code != 200:
        error_msg = ml_data.get("error", "Error desconocido en el servicio ML")
        return JsonResponse({"error": error_msg, "details": ml_data.get("details")}, status=500)

    prediction_result = ml_data.get("prediction", {})
    
    return JsonResponse({
        "status": "success",
        "student_id": student_id,
        "student_name": f"{student.first_name} {student.last_name}",
        "section": student.section,
        "data_context": {
            "total_evaluations": cant_evaluaciones,
            "scores": {
                "persistente": student.persistente_total,
                "competente": student.competente_total,
                "observador": student.observador_total
            }
        },
        "prediction": {
            "level_id": prediction_result.get("level_id"),
            "level_label": prediction_result.get("level_label", "Desconocido"),
            "confidence": prediction_result.get("confidence", 0.0),
            "probabilities": prediction_result.get("probabilities", {}),
            "recommendation": ml_data.get("recommendation", "No hay recomendación disponible.")
        },
        "debug_info": ml_data.get("debug", {})
    }, status=200)