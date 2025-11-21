from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import (
    District, School, Teacher, Student,
    Report, MLModelVersion, Prediction, TeacherStudentPrediction
)

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'


class SchoolSerializer(serializers.ModelSerializer):
    district = DistrictSerializer(read_only=True)

    class Meta:
        model = School
        fields = '__all__'


class TeacherSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Teacher
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password', 'school']

    def create(self, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name',
            'puntaje', 'promedio', 'score_total', 'cant_evaluaciones',
            'persistente_total', 'competente_total', 'observador_total',
            'teacher', 'school',
        ]

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"

class MLModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModelVersion
        fields = '__all__'


class PredictionSerializer(serializers.ModelSerializer):
    model_version = MLModelVersionSerializer(read_only=True)

    class Meta:
        model = Prediction
        fields = '__all__'


class TeacherStudentPredictionSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    student = StudentSerializer(read_only=True)
    report = ReportSerializer(read_only=True)
    prediction = PredictionSerializer(read_only=True)

    class Meta:
        model = TeacherStudentPrediction
        fields = '__all__'
