
from django.db import models
from django.contrib.auth.models import User

class SolicitudCuenta(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, default='')
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, default='')
    ciudad = models.CharField(max_length=100, default='')
    distrito = models.CharField(max_length=100, default='')
    contraseña = models.CharField(max_length=100, default='')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    atendida = models.BooleanField(default=False)
    activada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"

class Especialidad(models.Model):
	nombre = models.CharField(max_length=100, unique=True)
	descripcion = models.TextField(blank=True, null=True)
	fecha_creacion = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['nombre']
		verbose_name_plural = "Especialidades"

	def __str__(self):
		return self.nombre

class Docente(models.Model):
	nombre = models.CharField(max_length=100)
	apellido = models.CharField(max_length=100)
	email = models.EmailField(unique=True)
	telefono = models.CharField(max_length=20)
	especialidad = models.CharField(max_length=100, blank=True, null=True)
	fecha_ingreso = models.DateField()
	codigo_docente = models.CharField(max_length=50, unique=True, blank=True)
	foto = models.ImageField(upload_to='docentes/', blank=True, null=True)
	usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='docente')

	def __str__(self):
		return f"{self.nombre} {self.apellido}"

class Curso(models.Model):
	nombre = models.CharField(max_length=100)
	descripcion = models.TextField()
	docente = models.ForeignKey(Docente, on_delete=models.CASCADE)
	codigo = models.CharField(max_length=20, unique=True)
	fecha_inicio = models.DateField()
	fecha_fin = models.DateField()

	def __str__(self):
		return self.nombre

class Estudiante(models.Model):
	nombres = models.CharField(max_length=100)
	apellidos = models.CharField(max_length=100)
	email = models.EmailField(unique=True)
	telefono = models.CharField(max_length=20, blank=True, null=True)
	fecha_nacimiento = models.DateField(blank=True, null=True)
	direccion = models.CharField(max_length=200, blank=True, null=True)
	distrito = models.CharField(max_length=100, blank=True, null=True)
	foto = models.ImageField(upload_to='estudiantes/', blank=True, null=True)
	codigo_estudiante = models.CharField(max_length=50, unique=True, blank=True)
	fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
	usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='estudiante')

	class Meta:
		ordering = ['-fecha_creacion']
		verbose_name_plural = "Estudiantes"

	def __str__(self):
		return f"{self.nombres} {self.apellidos}"

class Nota(models.Model):
	estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
	curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
	calificacion = models.DecimalField(max_digits=4, decimal_places=2)
	fecha = models.DateField()
	observacion = models.TextField(blank=True)
	periodo = models.CharField(max_length=20)

	def __str__(self):
		return f"{self.estudiante} - {self.curso}: {self.calificacion}"
