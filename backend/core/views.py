from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Aula, Alumno, Proyecto
from .serializers import AulaSerializer, AlumnoSerializer, ProyectoSerializer
from .llm_service import HuggingFaceLLMService  # Nueva importación

class AulaViewSet(viewsets.ModelViewSet):
    queryset = Aula.objects.all()
    serializer_class = AulaSerializer

class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer

class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer
    
    @action(detail=False, methods=['get'])
    def por_area(self, request):
        """Filtrar proyectos por área curricular"""
        area = request.query_params.get('area', None)
        if area:
            proyectos = Proyecto.objects.filter(areas_curriculares__icontains=area)
            serializer = self.get_serializer(proyectos, many=True)
            return Response(serializer.data)
        return Response({"error": "Parámetro 'area' requerido"})
    
    @action(detail=True, methods=['post'])
    def generar_adaptaciones(self, request, pk=None):
        """Generar adaptaciones con LLM para un proyecto específico"""
        proyecto = self.get_object()
        tipo_adaptacion = request.data.get('tipo', None)  # 'tea', 'tdah', 'aacc'
        
        if not tipo_adaptacion:
            return Response({"error": "Parámetro 'tipo' requerido (tea, tdah, aacc)"})
        
        llm_service = HuggingFaceLLMService()
        
        if tipo_adaptacion == 'tea':
            resultado = llm_service.generar_adaptacion_tea(proyecto.titulo, proyecto.contenido_completo)
        elif tipo_adaptacion == 'tdah':
            resultado = llm_service.generar_adaptacion_tdah(proyecto.titulo, proyecto.contenido_completo)
        elif tipo_adaptacion == 'aacc':
            resultado = llm_service.generar_adaptacion_aacc(proyecto.titulo, proyecto.contenido_completo)
        else:
            return Response({"error": "Tipo debe ser: tea, tdah o aacc"})
        
        return Response({
            "proyecto": proyecto.titulo,
            "tipo_adaptacion": tipo_adaptacion,
            "adaptaciones_generadas": resultado
        })