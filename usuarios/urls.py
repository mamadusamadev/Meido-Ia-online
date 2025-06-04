# usuarios/urls.py
"""
URLs para o módulo de usuários

Este arquivo define todas as rotas da API REST para:
- Autenticação e autorização
- Gerenciamento de perfis
- Administração de usuários
- Logs e relatórios
- Configurações do sistema

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from django.urls import path, include
#from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    # Autenticação
    LoginView,
    LogoutView,
    RegistroView,
    ValidarTokenView,
    
    # Perfil do usuário
    PerfilUsuarioView,
    MudancaSenhaView,
    PerfilSegurancaView,
    NotificacoesUsuarioView,
    AlterarIdiomaView,
    DesativarContaView,
    HistoricoSenhasView,
    DispositivosConectadosView,
    
    # Logs e atividades
    LogAtividadeView,
    
    # Recuperação de senha
    RecuperacaoSenhaView,
    RedefinirSenhaView,
    
    # Views administrativas
    GerenciarUsuariosView,
    DetalhesUsuarioAdminView,
    ModeracaoUsuarioView,
    EstatisticasView,
    ExportarUsuariosView,
    LogsAdminView,
    
    # Views específicas por tipo
    PacientesView,
    ModeradoresView,
    
    # Relatórios e backup
    RelatoriosUsuariosView,
    BackupUsuariosView,
    ConfiguracaoSistemaView,
    
    # Utilitárias
    UsuariosResumoView,
    HealthCheckView
)

app_name = 'usuarios'

# URLs principais da API
urlpatterns = [
    
    # ========== AUTENTICAÇÃO ==========
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/registro/', RegistroView.as_view(), name='registro'),
    path('auth/validar-token/', ValidarTokenView.as_view(), name='validar_token'),
    
    # ========== RECUPERAÇÃO DE SENHA ==========
    path('auth/recuperar-senha/', RecuperacaoSenhaView.as_view(), name='recuperar_senha'),
    path('auth/redefinir-senha/<str:uidb64>/<str:token>/', RedefinirSenhaView.as_view(), name='redefinir_senha'),
    
    # ========== PERFIL DO USUÁRIO ==========
    path('perfil/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
    path('perfil/mudar-senha/', MudancaSenhaView.as_view(), name='mudar_senha'),
    path('perfil/seguranca/', PerfilSegurancaView.as_view(), name='perfil_seguranca'),
    path('perfil/notificacoes/', NotificacoesUsuarioView.as_view(), name='notificacoes_usuario'),
    path('perfil/idioma/', AlterarIdiomaView.as_view(), name='alterar_idioma'),
    path('perfil/desativar/', DesativarContaView.as_view(), name='desativar_conta'),
    path('perfil/historico-senhas/', HistoricoSenhasView.as_view(), name='historico_senhas'),
    path('perfil/dispositivos/', DispositivosConectadosView.as_view(), name='dispositivos_conectados'),
    
    # ========== LOGS E ATIVIDADES ==========
    path('atividades/', LogAtividadeView.as_view(), name='log_atividade'),
    
    # ========== ADMINISTRAÇÃO DE USUÁRIOS ==========
    path('admin/usuarios/', GerenciarUsuariosView.as_view(), name='gerenciar_usuarios'),
    path('admin/usuarios/<int:user_id>/', DetalhesUsuarioAdminView.as_view(), name='detalhes_usuario_admin'),
    path('admin/usuarios/<int:user_id>/moderacao/', ModeracaoUsuarioView.as_view(), name='moderacao_usuario'),
    path('admin/estatisticas/', EstatisticasView.as_view(), name='estatisticas'),
    path('admin/exportar/', ExportarUsuariosView.as_view(), name='exportar_usuarios'),
    path('admin/logs/', LogsAdminView.as_view(), name='logs_admin'),
    
    # ========== GERENCIAMENTO POR TIPO ==========
    path('admin/pacientes/', PacientesView.as_view(), name='listar_pacientes'),
    path('admin/moderadores/', ModeradoresView.as_view(), name='gerenciar_moderadores'),
    path('admin/moderadores/<int:user_id>/', ModeradoresView.as_view(), name='remover_moderador'),
    
    # ========== RELATÓRIOS E BACKUP ==========
    path('admin/relatorios/', RelatoriosUsuariosView.as_view(), name='relatorios_usuarios'),
    path('admin/backup/', BackupUsuariosView.as_view(), name='backup_usuarios'),
    path('admin/configuracoes/', ConfiguracaoSistemaView.as_view(), name='configuracao_sistema'),
    
    # ========== UTILITÁRIAS ==========
    path('resumo/', UsuariosResumoView.as_view(), name='usuarios_resumo'),
    path('health/', HealthCheckView.as_view(), name='health_check'),
]

# URLs para documentação da API (opcional)
api_info_patterns = [
    path('', include('rest_framework.urls')),
]

# Adiciona as URLs de info se necessário
# urlpatterns += api_info_patterns