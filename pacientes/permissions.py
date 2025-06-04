# usuarios/permissions.py
"""
Permissões customizadas para o sistema médico

Define permissões específicas para diferentes tipos de usuários
"""

from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

User = get_user_model()


class IsPacienteOwner(BasePermission):
    """
    Permissão que permite acesso apenas ao próprio paciente
    """
    
    def has_permission(self, request, view):
        """Verifica se o usuário está autenticado e é um paciente"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verifica se o usuário tem perfil de paciente
        try:
            return hasattr(request.user, 'paciente') and request.user.paciente is not None
        except AttributeError:
            return False
    
    def has_object_permission(self, request, view, obj):
        """Verifica se o objeto pertence ao paciente logado"""
        if not self.has_permission(request, view):
            return False
        
        # Se o objeto é o próprio paciente
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Se o objeto pertence ao paciente (ex: HistoricoFamiliar, DoencaFamiliar)
        if hasattr(obj, 'paciente'):
            return obj.paciente.user == request.user
        
        return False


class IsMedicoOrEnfermeiro(BasePermission):
    """
    Permissão que permite acesso apenas a médicos e enfermeiros
    """
    
    def has_permission(self, request, view):
        """Verifica se o usuário é médico ou enfermeiro"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verifica o tipo de usuário
        return request.user.tipo_usuario in ['medico', 'enfermeiro']


class IsMedico(BasePermission):
    """
    Permissão que permite acesso apenas a médicos
    """
    
    def has_permission(self, request, view):
        """Verifica se o usuário é médico"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.tipo_usuario == 'medico'


class IsEnfermeiro(BasePermission):
    """
    Permissão que permite acesso apenas a enfermeiros
    """
    
    def has_permission(self, request, view):
        """Verifica se o usuário é enfermeiro"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.tipo_usuario == 'enfermeiro'


class IsAdministrador(BasePermission):
    """
    Permissão que permite acesso apenas a administradores
    """
    
    def has_permission(self, request, view):
        """Verifica se o usuário é administrador"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.tipo_usuario == 'administrador' or request.user.is_superuser


class IsPacienteOrAdmin(BasePermission):
    """
    Permissão que permite acesso a pacientes (próprio perfil) ou médicos/enfermeiros
    """
    
    def has_permission(self, request, view):
        """Verifica se é paciente ou profissional de saúde"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Profissionais de saúde têm acesso total
        if request.user and request.user.is_authenticated and request.user.is_admin:
            return True
        return False