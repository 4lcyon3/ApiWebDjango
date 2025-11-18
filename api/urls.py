from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import api_overview
from api.controllers.views_teacher import TeacherViewSet
from api.controllers.views_student import StudentViewSet
from api.controllers.views_report import ReportViewSet
from api.controllers.views_ml import MLModelVersionViewSet, PredictionViewSet
from api.controllers.views_school import SchoolViewSet
from api.controllers.views_auth import CustomTokenObtainPairView

# Router principal para los viewsets
router = routers.DefaultRouter()
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'schools', SchoolViewSet, basename='school')
router.register(r'ml/models', MLModelVersionViewSet, basename='ml-model')
router.register(r'ml/predictions', PredictionViewSet, basename='ml-prediction')

urlpatterns = [
    path('', api_overview, name='api-overview'),

    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('', include(router.urls)),
]
