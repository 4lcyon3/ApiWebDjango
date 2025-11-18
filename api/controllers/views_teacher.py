from rest_framework import viewsets, permissions
from api.models import Teacher
from api.serializers import TeacherSerializer
from api.permissions import IsAdmin, IsTeacher
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsTeacher]
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = TeacherSerializer(request.user)
        return Response(serializer.data)
