from rest_framework import viewsets, permissions
from api.models import MLModelVersion, Prediction
from api.serializers import MLModelVersionSerializer, PredictionSerializer
from api.permissions import IsAdmin, IsTeacher

class MLModelVersionViewSet(viewsets.ModelViewSet):
    queryset = MLModelVersion.objects.all()
    serializer_class = MLModelVersionSerializer
    permission_classes = [IsAdmin]


class PredictionViewSet(viewsets.ModelViewSet):
    queryset = Prediction.objects.all().select_related('ml_model_version', 'student')
    serializer_class = PredictionSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Prediction.objects.all()
        return Prediction.objects.filter(student__teacher=user)

