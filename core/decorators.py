from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from functools import wraps

def es_estudiante(view_func):
    """Decorador para restringir acceso solo a estudiantes"""
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'estudiante') and request.user.estudiante:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("No tienes permiso para acceder a esta página. Solo estudiantes pueden acceder.")
    return wrapper

def es_docente(view_func):
    """Decorador para restringir acceso solo a docentes"""
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'docente') and request.user.docente:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("No tienes permiso para acceder a esta página. Solo docentes pueden acceder.")
    return wrapper

def es_admin(view_func):
    """Decorador para restringir acceso solo a administradores"""
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("No tienes permiso para acceder a esta página. Solo administradores pueden acceder.")
    return wrapper

def rol_requerido(rol):
    """Decorador genérico para requerir un rol específico
    Uso: @rol_requerido('estudiante') o @rol_requerido('docente')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            if rol == 'estudiante':
                if hasattr(request.user, 'estudiante') and request.user.estudiante:
                    return view_func(request, *args, **kwargs)
            elif rol == 'docente':
                if hasattr(request.user, 'docente') and request.user.docente:
                    return view_func(request, *args, **kwargs)
            elif rol == 'admin':
                if request.user.is_staff or request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden(f"No tienes permiso. Se requiere rol de {rol}.")
        return wrapper
    return decorator
