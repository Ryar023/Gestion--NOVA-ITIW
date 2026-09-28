from django import forms
from django.core.exceptions import ValidationError
from .models import Estudiante, Docente, Curso, Nota
import re

class EstudianteForm(forms.ModelForm):
    confirmPassword = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la contraseña'}),
        required=False,
        label='Confirmar Contraseña'
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 6 caracteres'}),
        required=False,
        label='Contraseña'
    )
    foto = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        required=False,
        label='Foto del Estudiante'
    )

    class Meta:
        model = Estudiante
        fields = ['nombres', 'apellidos', 'email', 'telefono', 'fecha_nacimiento', 'direccion', 'distrito', 'foto']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan', 'required': True}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: estudiante@ejemplo.com', 'required': True}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 987654321'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ingresa tu dirección'}),
            'distrito': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Lista de distritos
        distritos = [
            'Ancón', 'Ate', 'Barranco', 'Breña Alta', 'Breña Baja', 'Chaclacayo', 
            'Chorrillos', 'Cieneguilla', 'Comas', 'Chaclacayo', 'El Agustino', 
            'La Molina', 'La Victoria', 'Lima', 'Los Olivos', 'Lurín', 'Magdalena del Mar',
            'Miraflores', 'Pachacamac', 'Pucusana', 'Puente Piedra', 'Punta Hermosa',
            'Punta Negra', 'Rímac', 'San Andrés', 'San Bartolo', 'San Isidro',
            'San Juan de Lurigancho', 'San Juan de Miraflores', 'San Luis', 'San Martín de Porres',
            'San Miguel', 'Santa Anita', 'Santa María del Mar', 'Santa Rosa', 'Santiago de Surco',
            'Surquillo', 'Villa El Salvador', 'Villa María del Triunfo'
        ]
        
        self.fields['distrito'].widget = forms.Select(
            choices=[('', 'Selecciona un distrito')] + [(d, d) for d in sorted(distritos)],
            attrs={'class': 'form-control'}
        )
        
        # Si es edición (update), no requerir contraseña
        if self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirmPassword'].required = False
        else:
            self.fields['password'].required = True
            self.fields['confirmPassword'].required = True

    def clean_nombres(self):
        nombres = self.cleaned_data.get('nombres', '').strip()
        if not nombres:
            raise ValidationError('El nombre es obligatorio')
        if len(nombres) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombres):
            raise ValidationError('El nombre solo puede contener letras')
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos', '').strip()
        if not apellidos:
            raise ValidationError('Los apellidos son obligatorios')
        if len(apellidos) < 2:
            raise ValidationError('Los apellidos deben tener al menos 2 caracteres')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', apellidos):
            raise ValidationError('Los apellidos solo pueden contener letras')
        return apellidos

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError('El email es obligatorio')
        
        # Verificar si el email ya existe (excepto para el mismo usuario en edición)
        existe = Estudiante.objects.filter(email=email)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise ValidationError('Este email ya está registrado')
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if telefono and not re.match(r'^\d{7,}$', telefono):
            raise ValidationError('El teléfono debe contener solo números (mínimo 7 dígitos)')
        return telefono

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 6:
            raise ValidationError('La contraseña debe tener al menos 6 caracteres')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirmPassword')
        
        if password or confirm_password:
            if password != confirm_password:
                raise ValidationError('Las contraseñas no coinciden')
        
        return cleaned_data


class DocenteForm(forms.ModelForm):
    confirmPassword = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la contraseña'}),
        required=False,
        label='Confirmar Contraseña'
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 6 caracteres'}),
        required=False,
        label='Contraseña'
    )
    foto = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        required=False,
        label='Foto del Docente'
    )

    class Meta:
        model = Docente
        fields = ['nombre', 'apellido', 'email', 'telefono', 'especialidad', 'fecha_ingreso', 'foto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: docente@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 987654321'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar especialidades dinámicamente desde la BD
        from core.models import Especialidad
        especialidades = Especialidad.objects.all().order_by('nombre')
        especialidad_choices = [(e.nombre, e.nombre) for e in especialidades]
        
        # Si no hay especialidades, usar la lista predeterminada
        if not especialidad_choices:
            especialidad_choices = [
                ('Matemática', 'Matemática'),
                ('Lenguaje', 'Lenguaje'),
                ('Inglés', 'Inglés'),
                ('Ciencias', 'Ciencias'),
                ('Historia', 'Historia'),
                ('Geografía', 'Geografía'),
                ('Educación Física', 'Educación Física'),
                ('Arte', 'Arte'),
                ('Música', 'Música'),
                ('Informática', 'Informática'),
                ('Tecnología', 'Tecnología'),
                ('Filosofía', 'Filosofía'),
                ('Psicología', 'Psicología'),
                ('Economía', 'Economía'),
                ('Contabilidad', 'Contabilidad'),
            ]
        
        # Usar ChoiceField para compatibilidad con CharField
        self.fields['especialidad'] = forms.ChoiceField(
            choices=[('', 'Selecciona una especialidad')] + especialidad_choices,
            widget=forms.Select(attrs={'class': 'form-control'}),
            required=False
        )
        
        # Si es edición (update), no requerir contraseña
        if self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirmPassword'].required = False

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirmPassword')
        
        if password or confirm_password:
            if password != confirm_password:
                raise ValidationError('Las contraseñas no coinciden')
        
        return cleaned_data


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'codigo', 'descripcion', 'docente', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'docente': forms.Select(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer el campo código no requerido (se genera automáticamente)
        self.fields['codigo'].required = False


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['estudiante', 'curso', 'calificacion', 'fecha', 'periodo', 'observacion']
        widgets = {
            'estudiante': forms.Select(attrs={'class': 'form-control'}),
            'curso': forms.Select(attrs={'class': 'form-control'}),
            'calificacion': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '20', 'step': '0.1'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'periodo': forms.TextInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
