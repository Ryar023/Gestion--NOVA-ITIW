from django.shortcuts import render

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
import requests
import json
from datetime import datetime
from core.decorators import es_estudiante, es_docente, es_admin, rol_requerido

def generar_codigo_estudiante():
	"""Genera código de estudiante: U + año (2 dígitos) + número secuencial (6 dígitos)"""
	from core.models import Estudiante
	year = str(datetime.now().year)[2:]  # Últimos 2 dígitos del año
	
	# Obtener el último código del año actual
	codigos_year = Estudiante.objects.filter(codigo_estudiante__startswith=f"U{year}").values_list('codigo_estudiante', flat=True)
	
	if codigos_year:
		# Extraer números secuenciales y obtener el máximo
		numeros = [int(cod[3:]) for cod in codigos_year if cod[3:].isdigit()]
		siguiente = max(numeros) + 1 if numeros else 1
	else:
		siguiente = 1
	
	return f"U{year}{siguiente:06d}"

def generar_codigo_docente():
	"""Genera código de docente: C + año (2 dígitos) + número secuencial (6 dígitos)"""
	from core.models import Docente
	year = str(datetime.now().year)[2:]  # Últimos 2 dígitos del año
	
	# Obtener el último código del año actual
	codigos_year = Docente.objects.filter(codigo_docente__startswith=f"C{year}").values_list('codigo_docente', flat=True)
	
	if codigos_year:
		# Extraer números secuenciales y obtener el máximo
		numeros = [int(cod[3:]) for cod in codigos_year if cod[3:].isdigit()]
		siguiente = max(numeros) + 1 if numeros else 1
	else:
		siguiente = 1
	
	return f"C{year}{siguiente:06d}"

def generar_codigo_curso():
	"""Genera código de curso: CRS + año (2 dígitos) + número secuencial (5 dígitos)"""
	from core.models import Curso
	year = str(datetime.now().year)[2:]  # Últimos 2 dígitos del año
	
	# Obtener el último código del año actual
	codigos_year = Curso.objects.filter(codigo__startswith=f"CRS{year}").values_list('codigo', flat=True)
	
	if codigos_year:
		# Extraer números secuenciales y obtener el máximo
		numeros = [int(cod[5:]) for cod in codigos_year if cod[5:].isdigit()]
		siguiente = max(numeros) + 1 if numeros else 1
	else:
		siguiente = 1
	
	return f"CRS{year}{siguiente:05d}"

def login_view(request):
	if request.method == 'POST':
		username_or_email = request.POST.get('username', '').strip()
		password = request.POST.get('password', '').strip()
		from django.contrib.auth.models import User
		
		# Intentar autenticación directa primero
		user = authenticate(request, username=username_or_email, password=password)
		
		# Si falla, intentar por email
		if user is None:
			try:
				user_obj = User.objects.get(email=username_or_email)
				user = authenticate(request, username=user_obj.username, password=password)
			except User.DoesNotExist:
				pass
		
		if user is not None:
			login(request, user)
			return redirect('login_success', username=user.username)
		else:
			messages.error(request, "Usuario y/o clave incorrecto")
	return render(request, 'core/login.html')

def login_success_view(request, username):
	if not request.user.is_authenticated:
		return redirect('login')
	
	# Redirigir según rol
	user = request.user
	
	# Determinar URL de destino según rol
	if hasattr(user, 'docente') and user.docente and not user.is_superuser:
		next_url = reverse('listar_docentes')
	elif hasattr(user, 'estudiante') and user.estudiante and not user.is_superuser:
		next_url = reverse('listar_estudiantes')
	else:
		next_url = reverse('dashboard')
	
	# Renderizar template de confirmación y pasar la URL de destino
	return render(request, 'core/login_success.html', {'next_url': next_url})

def logout_view(request):
	logout(request)
	return render(request, 'core/logout_success.html')

@login_required(login_url='login')
def cambiar_password_view(request):
	"""Vista para que usuarios cambien su contraseña"""
	if request.method == 'POST':
		current_password = request.POST.get('current_password')
		new_password = request.POST.get('new_password')
		confirm_password = request.POST.get('confirm_password')
		
		# Validar contraseña actual
		if not request.user.check_password(current_password):
			messages.error(request, "La contraseña actual es incorrecta")
			return render(request, 'core/cambiar_password.html')
		
		# Validar que las contraseñas coincidan
		if new_password != confirm_password:
			messages.error(request, "Las contraseñas no coinciden")
			return render(request, 'core/cambiar_password.html')
		
		# Validar longitud mínima
		if len(new_password) < 8:
			messages.error(request, "La contraseña debe tener mínimo 8 caracteres")
			return render(request, 'core/cambiar_password.html')
		
		# Validar que no sea igual a la actual
		if current_password == new_password:
			messages.error(request, "La nueva contraseña no puede ser igual a la actual")
			return render(request, 'core/cambiar_password.html')
		
		# Cambiar la contraseña
		try:
			request.user.set_password(new_password)
			request.user.save()
			
			# Re-autenticar al usuario para mantener sesión
			from django.contrib.auth import update_session_auth_hash
			update_session_auth_hash(request, request.user)
			
			messages.success(request, "✅ Contraseña actualizada correctamente")
			return redirect('dashboard')
		except Exception as e:
			messages.error(request, f"Error al actualizar contraseña: {str(e)}")
			return render(request, 'core/cambiar_password.html')
	
	return render(request, 'core/cambiar_password.html')

@login_required
@es_admin
def administrar_usuarios_view(request):
	"""Vista para que admin gestione contraseñas de usuarios"""
	from django.contrib.auth.models import User
	
	if request.method == 'POST':
		usuario_id = request.POST.get('usuario_id')
		nueva_password = request.POST.get('nueva_password')
		confirmar_password = request.POST.get('confirmar_password')
		
		try:
			usuario = User.objects.get(id=usuario_id)
			
			# Validaciones
			if nueva_password != confirmar_password:
				messages.error(request, f"❌ Las contraseñas no coinciden para {usuario.first_name}")
				return redirect('administrar_usuarios')
			
			if len(nueva_password) < 8:
				messages.error(request, f"❌ La contraseña debe tener mínimo 8 caracteres para {usuario.first_name}")
				return redirect('administrar_usuarios')
			
			# Cambiar contraseña
			usuario.set_password(nueva_password)
			usuario.save()
			
			messages.success(request, f"✅ Contraseña actualizada para {usuario.first_name} {usuario.last_name}")
			return redirect('administrar_usuarios')
		
		except User.DoesNotExist:
			messages.error(request, "❌ Usuario no encontrado")
			return redirect('administrar_usuarios')
		except Exception as e:
			messages.error(request, f"❌ Error al actualizar contraseña: {str(e)}")
			return redirect('administrar_usuarios')
	
	# GET: Mostrar lista de usuarios
	from django.contrib.auth.models import User
	usuarios = User.objects.all().order_by('first_name')
	
	return render(request, 'core/administrar_usuarios.html', {
		'usuarios': usuarios
	})

def dashboard_view(request):
	if not request.user.is_authenticated:
		return redirect('login')
	
	from core.models import Docente, Estudiante, Curso, Nota
	from django.db.models import Avg
	
	# Calcular estadísticas generales
	total_estudiantes = Estudiante.objects.count()
	total_docentes = Docente.objects.count()
	total_cursos = Curso.objects.count()
	total_notas = Nota.objects.count()
	
	# Promedio general
	promedio_general = 0
	if total_notas > 0:
		promedio = Nota.objects.aggregate(Avg('calificacion'))['calificacion__avg']
		promedio_general = round(promedio, 2) if promedio else 0
	
	# Calcular aprobados y desaprobados (nota mínima es 12)
	aprobados = Nota.objects.filter(calificacion__gte=12).count()
	desaprobados = Nota.objects.filter(calificacion__lt=12).count()
	
	porcentaje_aprobados = 0
	porcentaje_desaprobados = 0
	if total_notas > 0:
		porcentaje_aprobados = round((aprobados / total_notas) * 100)
		porcentaje_desaprobados = round((desaprobados / total_notas) * 100)
	
	# Estudiantes por curso
	estudiantes_por_curso = 0
	if total_cursos > 0:
		estudiantes_por_curso = round(total_estudiantes / total_cursos)
	
	# Notas por estudiante
	notas_por_estudiante = 0
	if total_estudiantes > 0:
		notas_por_estudiante = round(total_notas / total_estudiantes)
	
	# Cursos por docente
	cursos_por_docente = 0
	if total_docentes > 0:
		cursos_por_docente = round((total_cursos / total_docentes) * 10) / 10
	
	# KPIs para estudiantes
	kpi_promedio_estudiante = 0
	kpi_total_notas = 0
	kpi_aprobadas = 0
	kpi_desaprobadas = 0
	
	if hasattr(request.user, 'estudiante') and request.user.estudiante:
		estudiante = request.user.estudiante
		notas_estudiante = Nota.objects.filter(estudiante=estudiante)
		kpi_total_notas = notas_estudiante.count()
		
		if kpi_total_notas > 0:
			promedio = notas_estudiante.aggregate(Avg('calificacion'))['calificacion__avg']
			kpi_promedio_estudiante = round(promedio, 2) if promedio else 0
			kpi_aprobadas = notas_estudiante.filter(calificacion__gte=12).count()
			kpi_desaprobadas = notas_estudiante.filter(calificacion__lt=12).count()
	
	# KPIs para docentes
	kpi_docente_cursos = 0
	kpi_docente_estudiantes = 0
	kpi_docente_notas = 0
	kpi_docente_promedio = 0
	
	if hasattr(request.user, 'docente') and request.user.docente:
		docente = request.user.docente
		cursos_docente = Curso.objects.filter(docente=docente)
		kpi_docente_cursos = cursos_docente.count()
		
		# Estudiantes únicos de los cursos del docente
		estudiantes_unicos = set()
		notas_docente = Nota.objects.filter(curso__docente=docente)
		for nota in notas_docente:
			estudiantes_unicos.add(nota.estudiante)
		kpi_docente_estudiantes = len(estudiantes_unicos)
		
		# Notas y promedio
		kpi_docente_notas = notas_docente.count()
		if kpi_docente_notas > 0:
			promedio = notas_docente.aggregate(Avg('calificacion'))['calificacion__avg']
			kpi_docente_promedio = round(promedio, 2) if promedio else 0
	
	context = {
		'user': request.user,
		'total_estudiantes': total_estudiantes,
		'total_docentes': total_docentes,
		'total_cursos': total_cursos,
		'total_notas': total_notas,
		'promedio_general': promedio_general,
		'porcentaje_aprobados': porcentaje_aprobados,
		'porcentaje_desaprobados': porcentaje_desaprobados,
		'estudiantes_por_curso': estudiantes_por_curso,
		'notas_por_estudiante': notas_por_estudiante,
		'cursos_por_docente': cursos_por_docente,
		# KPIs del estudiante
		'kpi_promedio_estudiante': kpi_promedio_estudiante,
		'kpi_total_notas': kpi_total_notas,
		'kpi_aprobadas': kpi_aprobadas,
		'kpi_desaprobadas': kpi_desaprobadas,
		# KPIs del docente
		'kpi_docente_cursos': kpi_docente_cursos,
		'kpi_docente_estudiantes': kpi_docente_estudiantes,
		'kpi_docente_notas': kpi_docente_notas,
		'kpi_docente_promedio': kpi_docente_promedio,
	}
	
	return render(request, 'core/dashboard.html', context)

def solicitar_cuenta_view(request):
	if request.method == 'POST':
		nombre = request.POST.get('nombre')
		apellido = request.POST.get('apellido')
		email = request.POST.get('email')
		telefono = request.POST.get('telefono')
		ciudad = request.POST.get('ciudad')
		distrito = request.POST.get('distrito')
		password = request.POST.get('password')
		from core.models import SolicitudCuenta
		if SolicitudCuenta.objects.filter(email=email).exists():
			messages.error(request, "Este correo ya tiene una solicitud registrada.")
		else:
			SolicitudCuenta.objects.create(
				nombre=nombre,
				apellido=apellido,
				email=email,
				telefono=telefono,
				ciudad=ciudad,
				distrito=distrito,
				contraseña=password
			)
			messages.success(request, "Solicitud enviada correctamente. El administrador la revisará pronto.")
			return redirect('login')
	return render(request, 'core/solicitar_cuenta.html')

def solicitudes_pendientes_view(request):
	if not request.user.is_superuser:
		messages.error(request, "No tienes permiso para acceder a esta página")
		return redirect('dashboard')
	from core.models import SolicitudCuenta
	solicitudes = SolicitudCuenta.objects.filter(atendida=False).order_by('-fecha_solicitud')
	return render(request, 'core/solicitudes_pendientes.html', {'solicitudes': solicitudes})

def aprobar_solicitud_view(request, solicitud_id):
	if not request.user.is_superuser:
		return redirect('dashboard')
	from core.models import SolicitudCuenta
	from django.contrib.auth.models import User
	solicitud = SolicitudCuenta.objects.get(id=solicitud_id)
	if request.method == 'POST':
		# Usar la contraseña que el usuario ingresó en la solicitud
		username = solicitud.email.split('@')[0]
		User.objects.create_user(
			username=username,
			email=solicitud.email,
			password=solicitud.contraseña,
			is_active=True
		)
		solicitud.atendida = True
		solicitud.activada = True
		solicitud.save()
		messages.success(request, f"Cuenta activada para {solicitud.nombre}")
		return redirect('solicitudes_pendientes')
	return render(request, 'core/aprobar_solicitud.html', {'solicitud': solicitud})

def rechazar_solicitud_view(request, solicitud_id):
	if not request.user.is_superuser:
		return redirect('dashboard')
	from core.models import SolicitudCuenta
	solicitud = SolicitudCuenta.objects.get(id=solicitud_id)
	solicitud.delete()
	messages.success(request, "Solicitud rechazada")
	return redirect('solicitudes_pendientes')

# ============ CRUD ESTUDIANTES ============
def listar_estudiantes_view(request):
	if not request.user.is_authenticated:
		return redirect('login')
	from core.models import Estudiante
	from django.db.models import Q
	
	# Obtener búsqueda y filtro
	search_term = request.GET.get('search', '').strip()
	filter_distrito = request.GET.get('distrito', '').strip()
	
	# Base queryset
	estudiantes = Estudiante.objects.all().order_by('-fecha_creacion')
	
	# Aplicar búsqueda
	if search_term:
		estudiantes = estudiantes.filter(
			Q(nombres__icontains=search_term) |
			Q(apellidos__icontains=search_term) |
			Q(email__icontains=search_term) |
			Q(codigo_estudiante__icontains=search_term)
		)
	
	# Aplicar filtro por distrito - usar iexact para comparación case-insensitive
	if filter_distrito:
		# Filtrar excluyendo NULLs y campos vacíos
		estudiantes = estudiantes.exclude(Q(distrito__isnull=True) | Q(distrito=''))
		estudiantes = estudiantes.filter(distrito__iexact=filter_distrito)
	
	# Obtener distritos únicos para el filtro dropdown
	# Excluir NULL y strings vacíos, ordenar alfabéticamente
	distritos = (Estudiante.objects
		.filter(distrito__isnull=False)
		.exclude(distrito='')
		.values_list('distrito', flat=True)
		.distinct()
		.order_by('distrito'))
	
	# Convertir a list y remover duplicados manteniendo orden
	distritos = sorted(set(d.strip() for d in distritos if d and d.strip()))
	
	context = {
		'estudiantes': estudiantes,
		'distritos': distritos,
		'search_term': search_term,
		'filter_distrito': filter_distrito,
	}
	return render(request, 'core/estudiantes/listar.html', context)

@es_admin
def crear_estudiante_view(request):
	from core.models import Estudiante
	from core.forms import EstudianteForm
	from django.contrib.auth.models import User
	
	if request.method == 'POST':
		form = EstudianteForm(request.POST, request.FILES)
		if form.is_valid():
			try:
				estudiante = form.save(commit=False)
				
				# Generar código automático
				estudiante.codigo_estudiante = generar_codigo_estudiante()
				
				# Obtener contraseña del formulario
				password = form.cleaned_data.get('password')
				
				# Crear usuario de Django si no existe y hay contraseña
				if password:
					username = estudiante.email.split('@')[0]
					
					# Verificar que no exista el usuario
					if not User.objects.filter(username=username).exists():
						user = User.objects.create_user(
							username=username,
							email=estudiante.email,
							password=password,
							first_name=estudiante.nombres,
							last_name=estudiante.apellidos,
							is_active=True
						)
						estudiante.usuario = user
					else:
						messages.warning(request, f"El usuario {username} ya existe")
				
				# Manejar foto
				if 'foto' in request.FILES:
					estudiante.foto = request.FILES['foto']
				
				estudiante.save()
				messages.success(request, "Estudiante creado correctamente")
				return redirect('listar_estudiantes')
			except Exception as e:
				messages.error(request, f"Error al crear estudiante: {str(e)}")
		else:
			for field, errors in form.errors.items():
				for error in errors:
					messages.error(request, f"{field}: {error}")
	else:
		form = EstudianteForm()
	
	return render(request, 'core/estudiantes/formulario.html', {'form': form, 'modo': 'crear'})

@es_admin
def editar_estudiante_view(request, estudiante_id):
	from core.models import Estudiante
	from core.forms import EstudianteForm
	
	# Solo admin puede editar
	if not request.user.is_staff or (hasattr(request.user, 'docente') and request.user.docente):
		messages.error(request, "No tienes permiso para editar estudiantes")
		return redirect('listar_estudiantes')
	
	try:
		estudiante = Estudiante.objects.get(id=estudiante_id)
	except Estudiante.DoesNotExist:
		messages.error(request, "Estudiante no encontrado")
		return redirect('listar_estudiantes')
	
	if request.method == 'POST':
		form = EstudianteForm(request.POST, request.FILES, instance=estudiante)
		if form.is_valid():
			try:
				# Si se proporciona contraseña, actualizar
				password = form.cleaned_data.get('password')
				if password:
					from django.contrib.auth.models import User
					try:
						user = User.objects.get(username=estudiante.email.split('@')[0])
						user.set_password(password)
						user.save()
					except User.DoesNotExist:
						pass
				
				# Manejar foto
				if 'foto' in request.FILES:
					estudiante.foto = request.FILES['foto']
				
				form.save()
				messages.success(request, "Estudiante actualizado correctamente")
				return redirect('listar_estudiantes')
			except Exception as e:
				messages.error(request, f"Error al actualizar estudiante: {str(e)}")
		else:
			for field, errors in form.errors.items():
				for error in errors:
					messages.error(request, f"{field}: {error}")
	else:
		form = EstudianteForm(instance=estudiante)
	
	return render(request, 'core/estudiantes/formulario.html', {'form': form, 'estudiante': estudiante, 'modo': 'editar'})

@es_admin
def eliminar_estudiante_view(request, estudiante_id):
	from core.models import Estudiante
	try:
		estudiante = Estudiante.objects.get(id=estudiante_id)
		estudiante.delete()
		messages.success(request, "Estudiante eliminado correctamente")
	except Estudiante.DoesNotExist:
		messages.error(request, "Estudiante no encontrado")
	return redirect('listar_estudiantes')

# ============ CRUD DOCENTES ============
def listar_docentes_view(request):
	if not request.user.is_authenticated:
		return redirect('login')
	from core.models import Docente
	from django.db.models import Q
	
	# Obtener término de búsqueda
	search_term = request.GET.get('search', '').strip()
	
	# Base queryset
	docentes = Docente.objects.all().order_by('nombre')
	
	# Aplicar búsqueda con Q objects
	if search_term:
		docentes = docentes.filter(
			Q(nombre__icontains=search_term) |
			Q(apellido__icontains=search_term) |
			Q(email__icontains=search_term) |
			Q(codigo_docente__icontains=search_term) |
			Q(especialidad__icontains=search_term)
		)
	
	context = {
		'docentes': docentes,
		'search_term': search_term,
	}
	return render(request, 'core/docentes/listar.html', context)

@es_admin
def crear_docente_view(request):
	from core.models import Docente
	from core.forms import DocenteForm
	from django.contrib.auth.models import User
	
	if request.method == 'POST':
		form = DocenteForm(request.POST, request.FILES)
		if form.is_valid():
			try:
				docente = form.save(commit=False)
				# Generar código automático
				docente.codigo_docente = generar_codigo_docente()
				# Asignar especialidad (si no se proporciona, usar "Generalista")
				if not docente.especialidad:
					docente.especialidad = 'Generalista'
				
				# Obtener contraseña del formulario
				password = form.cleaned_data.get('password')
				if password:
					username = docente.email.split('@')[0]
					
					# Verificar que no exista el usuario
					if not User.objects.filter(username=username).exists():
						user = User.objects.create_user(
							username=username,
							email=docente.email,
							password=password,
							first_name=docente.nombre,
							last_name=docente.apellido,
							is_active=True,
							is_staff=True
						)
						docente.usuario = user
					else:
						messages.warning(request, f"El usuario {username} ya existe")
				
				# Manejar foto
				if 'foto' in request.FILES:
					docente.foto = request.FILES['foto']
				
				docente.save()
				messages.success(request, "Docente creado correctamente")
				return redirect('listar_docentes')
			except Exception as e:
				messages.error(request, f"Error al crear docente: {str(e)}")
		else:
			for field, errors in form.errors.items():
				for error in errors:
					messages.error(request, f"{field}: {error}")
	else:
		form = DocenteForm()
	
	return render(request, 'core/docentes/formulario.html', {'form': form, 'modo': 'crear'})

@es_admin
def editar_docente_view(request, docente_id):
	from core.models import Docente
	from core.forms import DocenteForm
	
	# Solo admin puede editar docentes
	if not request.user.is_staff or (hasattr(request.user, 'docente') and request.user.docente):
		messages.error(request, "No tienes permiso para editar docentes")
		return redirect('listar_docentes')
	
	try:
		docente = Docente.objects.get(id=docente_id)
	except Docente.DoesNotExist:
		messages.error(request, "Docente no encontrado")
		return redirect('listar_docentes')
	
	if request.method == 'POST':
		form = DocenteForm(request.POST, request.FILES, instance=docente)
		if form.is_valid():
			try:
				# Si se proporciona contraseña, actualizar
				password = form.cleaned_data.get('password')
				if password:
					from django.contrib.auth.models import User
					try:
						user = User.objects.get(username=docente.email.split('@')[0])
						user.set_password(password)
						user.save()
					except User.DoesNotExist:
						pass
				
				docente_actualizado = form.save(commit=False)
				
				# Manejar foto
				if 'foto' in request.FILES:
					docente_actualizado.foto = request.FILES['foto']
				
				docente_actualizado.save()
				messages.success(request, "Docente actualizado correctamente")
				return redirect('listar_docentes')
			except Exception as e:
				messages.error(request, f"Error al actualizar docente: {str(e)}")
		else:
			for field, errors in form.errors.items():
				for error in errors:
					messages.error(request, f"{field}: {error}")
	else:
		form = DocenteForm(instance=docente)
	
	return render(request, 'core/docentes/formulario.html', {'form': form, 'docente': docente, 'modo': 'editar'})

@es_admin
def eliminar_docente_view(request, docente_id):
	from core.models import Docente
	docente = Docente.objects.get(id=docente_id)
	docente.delete()
	messages.success(request, "Docente eliminado correctamente")
	return redirect('listar_docentes')

# ============ CRUD CURSOS ============
def api_cursos_json(request):
	"""API endpoint para obtener cursos en JSON"""
	
	from core.models import Curso
	cursos = Curso.objects.all().values('id', 'nombre', 'codigo').order_by('nombre')
	return JsonResponse(list(cursos), safe=False)

def api_docentes_json(request):
	"""API endpoint para obtener docentes en JSON"""
	
	from core.models import Docente
	docentes = Docente.objects.all().values('id', 'nombre', 'apellido').order_by('nombre')
	# Formatear la respuesta para que incluya nombre completo
	docentes_list = [
		{'id': d['id'], 'nombre': f"{d['nombre']} {d['apellido']}"} 
		for d in docentes
	]
	return JsonResponse(docentes_list, safe=False)

def api_especialidades_json(request):
	"""API endpoint para obtener especialidades en JSON"""
	
	from core.models import Especialidad
	especialidades = Especialidad.objects.all().values('id', 'nombre').order_by('nombre')
	return JsonResponse(list(especialidades), safe=False)

# ============ API NOTAS ============
def api_notas_json(request):
	"""API endpoint para obtener todas las notas en JSON"""
	
	from core.models import Nota
	
	# Filtros opcionales
	estudiante_id = request.GET.get('estudiante_id')
	curso_id = request.GET.get('curso_id')
	
	notas = Nota.objects.all()
	
	if estudiante_id:
		notas = notas.filter(estudiante_id=estudiante_id)
	if curso_id:
		notas = notas.filter(curso_id=curso_id)
	
	notas_data = []
	for nota in notas.order_by('-fecha'):
		notas_data.append({
			'id': nota.id,
			'estudiante': nota.estudiante.nombres + ' ' + nota.estudiante.apellidos,
			'estudiante_id': nota.estudiante.id,
			'curso': nota.curso.nombre,
			'curso_id': nota.curso.id,
			'calificacion': float(nota.calificacion),
			'fecha': nota.fecha.strftime('%Y-%m-%d'),
			'periodo': nota.periodo,
			'observacion': nota.observacion
		})
	
	return JsonResponse(notas_data, safe=False)

def api_nota_detail(request, nota_id):
	"""API endpoint para obtener una nota específica"""
	
	from core.models import Nota
	
	try:
		nota = Nota.objects.get(id=nota_id)
		nota_data = {
			'id': nota.id,
			'estudiante': nota.estudiante.nombres + ' ' + nota.estudiante.apellidos,
			'estudiante_id': nota.estudiante.id,
			'curso': nota.curso.nombre,
			'curso_id': nota.curso.id,
			'calificacion': float(nota.calificacion),
			'fecha': nota.fecha.strftime('%Y-%m-%d'),
			'periodo': nota.periodo,
			'observacion': nota.observacion
		}
		return JsonResponse(nota_data)
	except Nota.DoesNotExist:
		return JsonResponse({'error': 'Nota no encontrada'}, status=404)

def api_notas_create(request):
	"""API endpoint para crear una nota (POST)"""
	if not request.user.is_authenticated:
		return JsonResponse({'error': 'No autorizado'}, status=401)
	
	if request.method != 'POST':
		return JsonResponse({'error': 'Método no permitido'}, status=405)
	
	from core.models import Nota, Estudiante, Curso
	import json
	
	try:
		data = json.loads(request.body)
		
		estudiante = Estudiante.objects.get(id=data.get('estudiante_id'))
		curso = Curso.objects.get(id=data.get('curso_id'))
		
		nota = Nota.objects.create(
			estudiante=estudiante,
			curso=curso,
			calificacion=data.get('calificacion'),
			fecha=data.get('fecha'),
			periodo=data.get('periodo', ''),
			observacion=data.get('observacion', '')
		)
		
		return JsonResponse({
			'success': True,
			'message': 'Nota creada correctamente',
			'id': nota.id
		}, status=201)
	
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=400)

def api_notas_update(request, nota_id):
	"""API endpoint para actualizar una nota (PUT)"""
	if not request.user.is_authenticated:
		return JsonResponse({'error': 'No autorizado'}, status=401)
	
	if request.method != 'PUT':
		return JsonResponse({'error': 'Método no permitido'}, status=405)
	
	from core.models import Nota, Estudiante, Curso
	import json
	
	try:
		nota = Nota.objects.get(id=nota_id)
		data = json.loads(request.body)
		
		if 'estudiante_id' in data:
			nota.estudiante = Estudiante.objects.get(id=data['estudiante_id'])
		if 'curso_id' in data:
			nota.curso = Curso.objects.get(id=data['curso_id'])
		if 'calificacion' in data:
			nota.calificacion = data['calificacion']
		if 'fecha' in data:
			nota.fecha = data['fecha']
		if 'periodo' in data:
			nota.periodo = data['periodo']
		if 'observacion' in data:
			nota.observacion = data['observacion']
		
		nota.save()
		
		return JsonResponse({
			'success': True,
			'message': 'Nota actualizada correctamente'
		})
	
	except Nota.DoesNotExist:
		return JsonResponse({'error': 'Nota no encontrada'}, status=404)
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=400)

def api_notas_delete(request, nota_id):
	"""API endpoint para eliminar una nota (DELETE)"""
	if not request.user.is_authenticated:
		return JsonResponse({'error': 'No autorizado'}, status=401)
	
	if request.method != 'DELETE':
		return JsonResponse({'error': 'Método no permitido'}, status=405)
	
	from core.models import Nota
	
	try:
		nota = Nota.objects.get(id=nota_id)
		nota.delete()
		
		return JsonResponse({
			'success': True,
			'message': 'Nota eliminada correctamente'
		})
	
	except Nota.DoesNotExist:
		return JsonResponse({'error': 'Nota no encontrada'}, status=404)
	except Exception as e:
		return JsonResponse({'error': str(e)}, status=400)

def listar_cursos_view(request):
	if not request.user.is_authenticated:
		return redirect('login')
	from core.models import Curso
	from django.db.models import Q
	
	# Obtener término de búsqueda
	search_term = request.GET.get('search', '').strip()
	
	# Base queryset
	cursos = Curso.objects.all().order_by('nombre')
	
	# Aplicar búsqueda con Q objects
	if search_term:
		cursos = cursos.filter(
			Q(nombre__icontains=search_term) |
			Q(codigo__icontains=search_term) |
			Q(descripcion__icontains=search_term) |
			Q(docente__nombre__icontains=search_term) |
			Q(docente__apellido__icontains=search_term)
		)
	
	context = {
		'cursos': cursos,
		'search_term': search_term,
	}
	return render(request, 'core/cursos/listar.html', context)

@es_admin
def crear_curso_view(request):
	from core.models import Curso
	from core.forms import CursoForm
	
	if request.method == 'POST':
		form = CursoForm(request.POST)
		if form.is_valid():
			try:
				curso = form.save(commit=False)
				curso.codigo = generar_codigo_curso()
				curso.save()
				messages.success(request, "Curso creado correctamente")
				return redirect('listar_cursos')
			except Exception as e:
				messages.error(request, f"Error al crear curso: {str(e)}")
		else:
			for field, errors in form.errors.items():
				for error in errors:
					messages.error(request, f"{field}: {error}")
	else:
		form = CursoForm()
	
	return render(request, 'core/cursos/formulario.html', {'form': form, 'modo': 'crear'})

@es_admin
def editar_curso_view(request, curso_id):
	from core.models import Curso
	from core.forms import CursoForm
	
	curso = get_object_or_404(Curso, pk=curso_id)
	
	if request.method == 'POST':
		form = CursoForm(request.POST, instance=curso)
		if form.is_valid():
			try:
				form.save()
				messages.success(request, "Curso actualizado correctamente")
				return redirect('listar_cursos')
			except Exception as e:
				messages.error(request, f"Error al actualizar curso: {str(e)}")
		else:
			for field, errors in form.errors.items():
				for error in errors:
					messages.error(request, f"{field}: {error}")
	else:
		form = CursoForm(instance=curso)
	
	return render(request, 'core/cursos/formulario.html', {'form': form, 'modo': 'editar', 'curso': curso})

@es_admin
def eliminar_curso_view(request, curso_id):
	from core.models import Curso
	curso = Curso.objects.get(id=curso_id)
	curso.delete()
	messages.success(request, "Curso eliminado correctamente")
	return redirect('listar_cursos')

# ============ CRUD NOTAS ============
@login_required(login_url='login')
def listar_notas_view(request):
	from core.models import Nota
	from django.db.models import Q
	
	# Obtener término de búsqueda
	search_term = request.GET.get('search', '').strip()
	
	# Admin ve todas las notas
	if request.user.is_staff or request.user.is_superuser:
		notas = Nota.objects.all().order_by('-fecha')
	# Estudiante solo ve sus notas
	elif hasattr(request.user, 'estudiante') and request.user.estudiante:
		estudiante = request.user.estudiante
		notas = Nota.objects.filter(estudiante=estudiante).order_by('-fecha')
	# Docente ve las notas de sus estudiantes
	elif hasattr(request.user, 'docente') and request.user.docente:
		docente = request.user.docente
		notas = Nota.objects.filter(curso__docente=docente).order_by('-fecha')
	else:
		return redirect('login')
	
	# Aplicar búsqueda con Q objects
	if search_term:
		notas = notas.filter(
			Q(estudiante__nombres__icontains=search_term) |
			Q(estudiante__apellidos__icontains=search_term) |
			Q(curso__nombre__icontains=search_term) |
			Q(periodo__icontains=search_term) |
			Q(observacion__icontains=search_term)
		)
	
	context = {
		'notas': notas,
		'search_term': search_term,
	}
	return render(request, 'core/notas/listar.html', context)

@login_required(login_url='login')
def crear_nota_view(request):
	from core.models import Nota, Estudiante, Curso
	# Solo admin y docentes pueden crear notas
	if not (request.user.is_staff or request.user.is_superuser or hasattr(request.user, 'docente')):
		return HttpResponseForbidden("No tienes permiso para crear notas")
	
	if request.method == 'POST':
		try:
			Nota.objects.create(
				estudiante_id=request.POST.get('estudiante'),
				curso_id=request.POST.get('curso'),
				calificacion=request.POST.get('calificacion'),
				fecha=request.POST.get('fecha'),
				observacion=request.POST.get('observacion'),
				periodo=request.POST.get('periodo')
			)
			messages.success(request, "Nota creada correctamente")
			return redirect('listar_notas')
		except Exception as e:
			messages.error(request, f"Error al crear nota: {str(e)}")
	estudiantes = Estudiante.objects.all()
	cursos = Curso.objects.all()
	return render(request, 'core/notas/formulario.html', {'estudiantes': estudiantes, 'cursos': cursos})

@es_admin
def editar_nota_view(request, nota_id):
	from core.models import Nota, Estudiante, Curso
	nota = Nota.objects.get(id=nota_id)
	if request.method == 'POST':
		try:
			nota.estudiante_id = request.POST.get('estudiante')
			nota.curso_id = request.POST.get('curso')
			nota.calificacion = request.POST.get('calificacion')
			nota.fecha = request.POST.get('fecha')
			nota.observacion = request.POST.get('observacion')
			nota.periodo = request.POST.get('periodo')
			nota.save()
			messages.success(request, "Nota actualizada correctamente")
			return redirect('listar_notas')
		except Exception as e:
			messages.error(request, f"Error al actualizar nota: {str(e)}")
	estudiantes = Estudiante.objects.all()
	cursos = Curso.objects.all()
	return render(request, 'core/notas/formulario.html', {'nota': nota, 'estudiantes': estudiantes, 'cursos': cursos})

@es_admin
def eliminar_nota_view(request, nota_id):
	from core.models import Nota
	nota = Nota.objects.get(id=nota_id)
	nota.delete()
	messages.success(request, "Nota eliminada correctamente")
	return redirect('listar_notas')

from django.http import HttpResponseRedirect
def home_redirect(request):
	return HttpResponseRedirect('/login/')

# Vista para consumir API REST - DATOS REALES DEL PROYECTO
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

@login_required(login_url='login')
def api_rest_view(request):
	"""
	Vista que consume datos REALES de la base de datos del proyecto
	y los muestra en tablas (Estudiantes, Docentes, Cursos, Notas)
	"""
	context = {}
	
	try:
		# Obtener datos reales del proyecto
		from core.models import Estudiante, Docente, Curso, Nota
		
		# ESTUDIANTES
		estudiantes_qs = Estudiante.objects.all().values('id', 'nombres', 'apellidos', 'email', 'codigo_estudiante')
		estudiantes_list = list(estudiantes_qs)
		context['estudiantes'] = json.dumps(estudiantes_list, ensure_ascii=False, default=str)
		context['total_estudiantes'] = len(estudiantes_list)
		
		# DOCENTES
		docentes_qs = Docente.objects.all().values('id', 'nombre', 'apellido', 'email', 'especialidad', 'codigo_docente')
		docentes_list = list(docentes_qs)
		context['docentes'] = json.dumps(docentes_list, ensure_ascii=False, default=str)
		context['total_docentes'] = len(docentes_list)
		
		# CURSOS
		cursos_qs = Curso.objects.all().select_related('docente').values('id', 'nombre', 'descripcion', 'codigo', 'docente__nombre')
		cursos_list = list(cursos_qs)
		context['cursos'] = json.dumps(cursos_list, ensure_ascii=False, default=str)
		context['total_cursos'] = len(cursos_list)
		
		# NOTAS
		notas_qs = Nota.objects.all().select_related('estudiante', 'curso').values(
			'id', 'estudiante__nombres', 'curso__nombre', 'calificacion', 'fecha', 'periodo'
		)
		notas_list = list(notas_qs)
		context['notas'] = json.dumps(notas_list, ensure_ascii=False, default=str)
		context['total_notas'] = len(notas_list)
		
		context['error_message'] = None
		
	except Exception as e:
		context['error_message'] = f"Error al obtener datos: {str(e)}"
		context['estudiantes'] = json.dumps([], ensure_ascii=False)
		context['docentes'] = json.dumps([], ensure_ascii=False)
		context['cursos'] = json.dumps([], ensure_ascii=False)
		context['notas'] = json.dumps([], ensure_ascii=False)
		context['total_estudiantes'] = 0
		context['total_docentes'] = 0
		context['total_cursos'] = 0
		context['total_notas'] = 0
	
	return render(request, 'core/api_rest.html', context)
