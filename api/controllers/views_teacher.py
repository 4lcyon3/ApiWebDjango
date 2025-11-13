from rest_framework import viewsets, permissions
from api.models import Teacher
from api.serializers import TeacherSerializer
from api.permissions import IsTeacher

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsTeacher]
