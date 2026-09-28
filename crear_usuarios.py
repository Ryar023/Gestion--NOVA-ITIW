"""
Script temporal para crear usuarios iniciales de prueba
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novagestion.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Docente, Estudiante

# Crear usuario administrador
if not User.objects.filter(username='admin').exists():
    admin_password = os.environ.get('INITIAL_ADMIN_PASSWORD')
    if not admin_password:
        raise RuntimeError('Set INITIAL_ADMIN_PASSWORD before creating the admin user')
    admin = User.objects.create_superuser('admin', 'admin@example.com', admin_password)
    print("✅ Administrador creado")

# Crear usuarios de prueba
users_data = [
    ('docente1', 'docente@example.com', 'INITIAL_TEACHER_PASSWORD'),
    ('estudiante1', 'estudiante@example.com', 'INITIAL_STUDENT_PASSWORD'),
]

for username, email, password_variable in users_data:
    if not User.objects.filter(username=username).exists():
        password = os.environ.get(password_variable)
        if not password:
            raise RuntimeError(f'Set {password_variable} before creating {username}')
        user = User.objects.create_user(username, email, password)
        print(f"✅ Usuario {username} creado")
    else:
        print(f"⚠️ Usuario {username} ya existe")

print("\n✅ Script completado")
