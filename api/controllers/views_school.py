from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from api.models import School
from api.serializers import SchoolSerializer

class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'location']

