from django.db import models

class Aula(models.Model):
    nombre= models.CharField(max_length=100)
    curso= models.CharField(max_length=50)
    numero_alumnos= models.IntegerField()

    def __str__(self):
        return self.nombre

class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    diagnostico = models.CharField(max_length=200, blank=True, null=True)
    caracteristicas = models.TextField(blank=True)

    def __str__(self):
        return self.nombre 
    
class Proyecto(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion_breve = models.TextField()
    objetivos = models.TextField(blank=True)
    areas_curriculares = models.CharField(max_length=200)
    duracion_sesiones = models.IntegerField()
    contenido_completo = models.JSONField()
    adaptaciones_tea = models.TextField(blank=True)
    adaptaciones_tdah = models.TextField(blank=True)
    adaptaciones_aacc = models.TextField(blank=True)

    def __str__(self):
        return self.titulo
