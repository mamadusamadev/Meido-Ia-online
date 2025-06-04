# pacientes/urls.py
"""
URLs para o sistema de pacientes

Define todas as rotas relacionadas ao gerenciamento de pacientes
"""

from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    # Cadastro de paciente (público)
    path('cadastro/', views.PacienteCadastroView.as_view(), name='cadastro'),
    
    # Gerenciamento do próprio perfil (paciente logado)
    path('perfil/', views.PacientePerfilView.as_view(), name='perfil'),
    
    # Histórico familiar
    path('historico-familiar/', views.PacienteHistoricoFamiliarView.as_view(), name='historico-familiar'),
    
    # Doenças familiares
    path('doencas-familiares/', views.PacienteDoencasFamiliaresView.as_view(), name='doencas-familiares'),
    path('doencas-familiares/<int:pk>/', views.DoencaFamiliarDetailView.as_view(), name='doenca-familiar-detail'),
    
    # Listagem e busca (apenas Administrador)
    path('', views.PacienteListView.as_view(), name='list'),
    path('buscar/', views.PacienteBuscarView.as_view(), name='buscar'),
    path('estatisticas/', views.PacienteEstatisticasView.as_view(), name='estatisticas'),
    
    # Detalhes de paciente específico (apenas IsAdminUser)
    path('<int:pk>/', views.PacienteDetailView.as_view(), name='detail'),
]