"""
Script para fijar relaciones de docentes con sus especialidades
Migración temporal de datos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novagestion.settings')
django.setup()

from core.models import Docente, Especialidad

# Asegurar que los docentes tienen especialidad
docentes = Docente.objects.all()
for docente in docentes:
    if not docente.especialidad:
        # Asignar especialidad por defecto
        especialidad, created = Especialidad.objects.get_or_create(
            nombre='General',
            defaults={'descripcion': 'Especialidad General'}
        )
        docente.especialidad = especialidad
        docente.save()
        print(f"✅ {docente.nombre} - Especialidad asignada")

print(f"\n✅ {docentes.count()} docentes procesados")
