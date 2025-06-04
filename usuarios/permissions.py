"""
Permissões customizadas para controle de acesso de usuários

Este módulo define classes de permissão específicas para:
- Administradores
- Moderadores
- Proprietários dos dados

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permite acesso apenas a administradores do sistema.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsModerador(permissions.BasePermission):
    """
    Permite acesso apenas a moderadores do sistema.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_moderador)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permite acesso ao proprietário do objeto ou a um administrador.
    """

    def has_object_permission(self, request, view, obj):
        return (
            obj == request.user or
            (request.user and request.user.is_authenticated and request.user.is_admin)
        )
