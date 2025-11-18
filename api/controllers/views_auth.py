from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from api.models import Teacher, School

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    school = serializers.CharField(required=True)

    def validate(self, attrs):
        school_name = attrs.get('school')
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            school = School.objects.get(fullname__iexact=school_name)
        except School.DoesNotExist:
            raise serializers.ValidationError({'school': 'Colegio no encontrado'})

        try:
            user = Teacher.objects.get(username=username, school=school)
        except Teacher.DoesNotExist:
            raise serializers.ValidationError({'username': 'Usuario no encontrado en el colegio indicado'})

        if not user.check_password(password): # type: ignore
            raise serializers.ValidationError({'password': 'Contraseña incorrecta'})

        refresh = self.get_token(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token), # type: ignore
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'school': user.school.fullname, # type: ignore
        }
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
