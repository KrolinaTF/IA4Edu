from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'aulas', views.AulaViewSet)
router.register(r'alumnos', views.AlumnoViewSet)
router.register(r'proyectos', views.ProyectoViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]