from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_overview(request):
    """
    Vista general de la API.
    Permite verificar que el backend esté activo y conocer los endpoints disponibles.
    """
    return Response({
        "message": "API de análisis de rendimiento escolar activa",
        "endpoints": {
            "auth": {
                "obtain_token": "/api/token/",
                "refresh_token": "/api/token/refresh/"
            },
            "students": "/api/students/",
            "teachers": "/api/teachers/",
            "reports": {
                "list_create": "/api/reports/",
                "upload_csv": "/api/reports/upload/",
                "filter": "/api/reports/filter/?week={num}&school={id}"
            },
            "ml_models": "/api/ml/models/",
            "predictions": "/api/ml/predictions/",
        }
    })
