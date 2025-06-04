from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Cidade, Tabanca
from .serializers import (
    CidadeSerializer,
    CidadeCriacaoSerializer,
    TabancaSerializer,
    TabancaCriacaoSerializer,
)
from usuarios.permissions import IsAdminUser, IsModerador


class CidadeViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD de cidades."""

    queryset = Cidade.objects.select_related("regiao").all()

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdminUser()]
        elif self.action in ["create", "update", "partial_update"]:
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CidadeCriacaoSerializer
        return CidadeSerializer


class TabancaViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD de tabancas."""

    queryset = Tabanca.objects.select_related("cidade__regiao").all()

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdminUser()]
        elif self.action in ["create", "update", "partial_update"]:
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TabancaCriacaoSerializer
        return TabancaSerializer
