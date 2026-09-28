from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('login/', views.login_view, name='login'),
    path('login-success/<str:username>/', views.login_success_view, name='login_success'),
    path('logout/', views.logout_view, name='logout'),
    path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
    path('administrar-usuarios/', views.administrar_usuarios_view, name='administrar_usuarios'),
    path('solicitar-cuenta/', views.solicitar_cuenta_view, name='solicitar_cuenta'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('solicitudes-pendientes/', views.solicitudes_pendientes_view, name='solicitudes_pendientes'),
    path('aprobar-solicitud/<int:solicitud_id>/', views.aprobar_solicitud_view, name='aprobar_solicitud'),
    path('rechazar-solicitud/<int:solicitud_id>/', views.rechazar_solicitud_view, name='rechazar_solicitud'),
    
    # Rutas CRUD Estudiantes
    path('estudiantes/', views.listar_estudiantes_view, name='listar_estudiantes'),
    path('estudiantes/crear/', views.crear_estudiante_view, name='crear_estudiante'),
    path('estudiantes/<int:estudiante_id>/editar/', views.editar_estudiante_view, name='editar_estudiante'),
    path('estudiantes/<int:estudiante_id>/eliminar/', views.eliminar_estudiante_view, name='eliminar_estudiante'),
    
    # Rutas CRUD Docentes
    path('docentes/', views.listar_docentes_view, name='listar_docentes'),
    path('docentes/crear/', views.crear_docente_view, name='crear_docente'),
    path('docentes/<int:docente_id>/editar/', views.editar_docente_view, name='editar_docente'),
    path('docentes/<int:docente_id>/eliminar/', views.eliminar_docente_view, name='eliminar_docente'),
    
    # Rutas CRUD Cursos
    path('cursos/', views.listar_cursos_view, name='listar_cursos'),
    path('cursos/crear/', views.crear_curso_view, name='crear_curso'),
    path('cursos/<int:curso_id>/editar/', views.editar_curso_view, name='editar_curso'),
    path('cursos/<int:curso_id>/eliminar/', views.eliminar_curso_view, name='eliminar_curso'),
    path('api/cursos/', views.api_cursos_json, name='api_cursos'),
    path('api/docentes/', views.api_docentes_json, name='api_docentes'),
    path('api/especialidades/', views.api_especialidades_json, name='api_especialidades'),
    
    # Rutas CRUD Notas
    path('notas/', views.listar_notas_view, name='listar_notas'),
    path('notas/crear/', views.crear_nota_view, name='crear_nota'),
    path('notas/<int:nota_id>/editar/', views.editar_nota_view, name='editar_nota'),
    path('notas/<int:nota_id>/eliminar/', views.eliminar_nota_view, name='eliminar_nota'),
    
    # API Notas
    path('api/notas/', views.api_notas_json, name='api_notas'),
    path('api/notas/<int:nota_id>/', views.api_nota_detail, name='api_nota_detail'),
    path('api/notas/create/', views.api_notas_create, name='api_notas_create'),
    path('api/notas/<int:nota_id>/update/', views.api_notas_update, name='api_notas_update'),
    path('api/notas/<int:nota_id>/delete/', views.api_notas_delete, name='api_notas_delete'),
    
    # Ruta API REST
    path('api-rest/', views.api_rest_view, name='api_rest'),
]
