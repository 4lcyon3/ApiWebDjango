from rest_framework import serializers
from .models import (
    District, School, Teacher, Student,
    Report, MLModelVersion, Prediction, TeacherStudentPrediction
)


# =====================
# SERIALIZERS BÁSICOS
# =====================
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

    class Meta:
        model = Teacher
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'school']


class StudentSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    school = SchoolSerializer(read_only=True)

    class Meta:
        model = Student
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source='student', write_only=True
    )

    class Meta:
        model = Report
        fields = [
            'id',
            'teacher',
            'student',
            'student_id',
            'persistente',
            'competente',
            'observador',
            'score_total',
            'upload_date',
            'week_number',
            'created_at'
        ]
        read_only_fields = ['id', 'score_total', 'upload_date', 'week_number', 'created_at']

    def create(self, validated_data):
        """
        Crea un nuevo reporte calculando automáticamente el score_total
        y vinculándolo al docente autenticado.
        """
        teacher = self.context['request'].user
        student = validated_data.pop('student')
        report = Report.objects.create(teacher=teacher, student=student, **validated_data)
        return report

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
