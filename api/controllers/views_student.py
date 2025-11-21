from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import Student, Teacher
from api.serializers import StudentSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Student.objects.all()
        teacher = Teacher.objects.filter(id=user.id).first() # type: ignore
        if not teacher:
            return Student.objects.none()
        return Student.objects.filter(teacher=teacher)

    @action(detail=True, methods=["post"])
    def predict(self, request, pk=None):
        student = self.get_object()
        # aquí llamas tu modelo ML
        # ejemplo: predict(student.persistente_total, student.competente_total, student.observador_total)
        resultado = {"mensaje": f"Predicción para {student.first_name} {student.last_name}"}
        return Response(resultado)
