from rest_framework import viewsets, permissions
from api.models import Student
from api.serializers import StudentSerializer
from api.permissions import IsTeacher, IsOwnerTeacherOrAdmin

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsTeacher, IsOwnerTeacherOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Student.objects.all()
        return Student.objects.filter(teacher=user)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)
