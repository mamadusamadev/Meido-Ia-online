# usuarios/views.py
"""
Views para API REST do módulo de usuários

Este módulo implementa todas as views necessárias para:
- Autenticação e autorização
- Gerenciamento de usuários
- Perfis e configurações
- Logs de atividade
- Administração de usuários

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
import json
#from django.core import serializers
        
import csv
import io
from datetime import datetime, timedelta

from .models import Usuario, PerfilSeguranca, LogAtividade
from .serializers import (
    UsuarioSerializer,
    UsuarioCriacaoSerializer,
    UsuarioPerfilSerializer,
    MudancaSenhaSerializer,
    PerfilSegurancaSerializer,
    LogAtividadeSerializer,
    TokenPersonalizadoSerializer,
    UsuarioAdminSerializer,
    UsuarioResumoSerializer,
    EstatisticasUsuarioSerializer,
    RecuperacaoSenhaSerializer,
    RedefinirSenhaSerializer,
    UsuarioModeracaoSerializer,
    UsuarioExportacaoSerializer
)

from .permissions import IsAdminUser,  IsModerador


class CustomPagination(PageNumberPagination):
    """Paginação personalizada"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LoginView(TokenObtainPairView):
    """
    View para login de usuários
    
    Utiliza JWT tokens e registra atividade de login
    """
    serializer_class = TokenPersonalizadoSerializer
    
    def post(self, request, *args, **kwargs):
        """Processa tentativa de login"""
        response = super().post(request, *args, **kwargs)
        
        # Se o login falhou, registra a tentativa
        if response.status_code != 200:
            email = request.data.get('email')
            if email:
                try:
                    usuario = Usuario.objects.get(email=email)
                    usuario.incrementar_tentativas_login()
                    
                    # Registra tentativa de login falhada
                    LogAtividade.registrar_atividade(
                        usuario=usuario,
                        tipo_atividade='login_failed',
                        descricao='Tentativa de login com credenciais inválidas',
                        ip_address=self.get_client_ip(request)
                    )
                except Usuario.DoesNotExist:
                    pass
        
        return response
    
    def get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    View para logout de usuários
    
    Invalida o token JWT e registra atividade
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Processa logout do usuário"""
        try:
            # Obtém o refresh token
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Registra atividade de logout
            LogAtividade.registrar_atividade(
                usuario=request.user,
                tipo_atividade='logout',
                descricao='Logout realizado pelo usuário'
            )
            
            return Response({
                'message': 'Logout realizado com sucesso'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Erro ao processar logout'
            }, status=status.HTTP_400_BAD_REQUEST)


class RegistroView(APIView):
    """
    View para registro de novos usuários
    
    Permite que novos usuários se cadastrem no sistema
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Registra um novo usuário"""
        serializer = UsuarioCriacaoSerializer(data=request.data)
        
        if serializer.is_valid():
            usuario = serializer.save()
            
            # Registra atividade de criação de conta
            LogAtividade.registrar_atividade(
                usuario=usuario,
                tipo_atividade='profile_update',
                descricao='Conta criada com sucesso'
            )
            
            # Serializa dados do usuário criado
            user_serializer = UsuarioSerializer(usuario)
            
            return Response({
                'message': 'Usuário criado com sucesso',
                'user': user_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PerfilUsuarioView(APIView):
    """
    View para visualizar e atualizar perfil do usuário
    
    Permite que usuários vejam e editem suas próprias informações
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retorna dados do perfil do usuário"""
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Atualiza perfil do usuário"""
        serializer = UsuarioPerfilSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            usuario = serializer.save()
            response_serializer = UsuarioSerializer(usuario)
            
            return Response({
                'message': 'Perfil atualizado com sucesso',
                'user': response_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MudancaSenhaView(APIView):
    """
    View para mudança de senha do usuário
    
    Permite que usuários alterem suas senhas
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Processa mudança de senha"""
        serializer = MudancaSenhaSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'message': 'Senha alterada com sucesso'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PerfilSegurancaView(APIView):
    """
    View para configurações de segurança do usuário
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retorna configurações de segurança"""
        try:
            perfil_seguranca = request.user.perfil_seguranca
            serializer = PerfilSegurancaSerializer(perfil_seguranca)
            return Response(serializer.data)
        except PerfilSeguranca.DoesNotExist:
            return Response({
                'error': 'Perfil de segurança não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request):
        """Atualiza configurações de segurança"""
        try:
            perfil_seguranca = request.user.perfil_seguranca
            serializer = PerfilSegurancaSerializer(
                perfil_seguranca,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Configurações de segurança atualizadas',
                    'data': serializer.data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except PerfilSeguranca.DoesNotExist:
            return Response({
                'error': 'Perfil de segurança não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class LogAtividadeView(APIView):
    """
    View para visualizar logs de atividade do usuário
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request):
        """Retorna logs de atividade do usuário"""
        queryset = LogAtividade.objects.filter(usuario=request.user)
        
        # Filtros opcionais
        tipo_atividade = request.query_params.get('tipo')
        if tipo_atividade:
            queryset = queryset.filter(tipo_atividade=tipo_atividade)
        
        data_inicio = request.query_params.get('data_inicio')
        if data_inicio:
            try:
                data_inicio = datetime.fromisoformat(data_inicio.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=data_inicio)
            except ValueError:
                pass
        
        data_fim = request.query_params.get('data_fim')
        if data_fim:
            try:
                data_fim = datetime.fromisoformat(data_fim.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=data_fim)
            except ValueError:
                pass
        
        # Paginação
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LogAtividadeSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = LogAtividadeSerializer(queryset, many=True)
        return Response(serializer.data)


class RecuperacaoSenhaView(APIView):
    """
    View para solicitar recuperação de senha
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Envia email de recuperação de senha"""
        serializer = RecuperacaoSenhaSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                usuario = Usuario.objects.get(email=email, is_active=True)
                
                # Gera token de recuperação
                token = default_token_generator.make_token(usuario)
                uid = urlsafe_base64_encode(force_bytes(usuario.pk))
                
                # URL de recuperação
                reset_url = f"{settings.FRONTEND_URL}/redefinir-senha/{uid}/{token}/"
                
                # Envia email
                context = {
                    'usuario': usuario,
                    'reset_url': reset_url,
                    'domain': settings.DOMAIN_NAME,
                    'site_name': settings.SITE_NAME
                }
                
                subject = 'Recuperação de Senha - Sistema Médico IA Guiné'
                message = render_to_string('emails/recuperacao_senha.html', context)
                
                send_mail(
                    subject=subject,
                    message='',
                    html_message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False
                )
                
                # Registra atividade
                LogAtividade.registrar_atividade(
                    usuario=usuario,
                    tipo_atividade='password_reset_request',
                    descricao='Solicitação de recuperação de senha'
                )
                
            except Usuario.DoesNotExist:
                # Por segurança, não revelamos se o usuário existe
                pass
            
            return Response({
                'message': 'Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RedefinirSenhaView(APIView):
    """
    View para redefinir senha via token
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, uidb64, token):
        """Redefine a senha do usuário"""
        serializer = RedefinirSenhaSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Decodifica o UID
                uid = force_str(urlsafe_base64_decode(uidb64))
                usuario = Usuario.objects.get(pk=uid)
                
                # Verifica se o token é válido
                if default_token_generator.check_token(usuario, token):
                    nova_senha = serializer.validated_data['nova_senha']
                    
                    # Atualiza a senha
                    usuario.set_password(nova_senha)
                    usuario.tentativas_login = 0  # Reset tentativas
                    usuario.conta_bloqueada_ate = None  # Desbloqueia conta
                    usuario.save()
                    
                    # Atualiza perfil de segurança
                    if hasattr(usuario, 'perfil_seguranca'):
                        from django.contrib.auth.hashers import make_password
                        usuario.perfil_seguranca.adicionar_senha_historico(
                            make_password(nova_senha)
                        )
                    
                    # Registra atividade
                    LogAtividade.registrar_atividade(
                        usuario=usuario,
                        tipo_atividade='password_reset',
                        descricao='Senha redefinida via recuperação por email'
                    )
                    
                    return Response({
                        'message': 'Senha redefinida com sucesso'
                    })
                else:
                    return Response({
                        'error': 'Token inválido ou expirado'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
                return Response({
                    'error': 'Link de recuperação inválido'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== VIEWS ADMINISTRATIVAS ==========

class GerenciarUsuariosView(APIView):
    """
    View para administradores gerenciarem usuários
    """
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    
    def get(self, request):
        """Lista todos os usuários com filtros"""
        queryset = Usuario.objects.all().order_by('-created_at')
        
        # Filtros
        tipo_usuario = request.query_params.get('tipo')
        if tipo_usuario == 'paciente':
            queryset = queryset.filter(is_paciente=True)
        elif tipo_usuario == 'moderador':
            queryset = queryset.filter(is_moderador=True)
        elif tipo_usuario == 'admin':
            queryset = queryset.filter(is_admin=True)
        
        is_active = request.query_params.get('ativo')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Busca por email ou telefone
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | 
                Q(telefone__icontains=search)
            )
        
        # Filtro por data de criação
        data_inicio = request.query_params.get('data_inicio')
        if data_inicio:
            try:
                data_inicio = datetime.fromisoformat(data_inicio)
                queryset = queryset.filter(created_at__gte=data_inicio)
            except ValueError:
                pass
        
        # Paginação
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = UsuarioAdminSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = UsuarioAdminSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Cria um novo usuário (admin)"""
        serializer = UsuarioCriacaoSerializer(data=request.data)
        
        if serializer.is_valid():
            usuario = serializer.save()
            
            # Registra atividade administrativa
            LogAtividade.registrar_atividade(
                usuario=request.user,
                tipo_atividade='admin_action',
                descricao=f'Usuário {usuario.email} criado pelo administrador'
            )
            
            response_serializer = UsuarioAdminSerializer(usuario)
            return Response({
                'message': 'Usuário criado com sucesso',
                'user': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DetalhesUsuarioAdminView(APIView):
    """
    View para administradores verem detalhes de um usuário específico
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request, user_id):
        """Retorna detalhes completos do usuário"""
        try:
            usuario = Usuario.objects.get(id=user_id)
            serializer = UsuarioAdminSerializer(usuario)
            
            # Adiciona estatísticas extras
            data = serializer.data
            data['total_logins'] = usuario.atividades.filter(
                tipo_atividade='login'
            ).count()
            data['total_atividades'] = usuario.atividades.count()
            
            # Últimas atividades
            ultimas_atividades = usuario.atividades.order_by('-timestamp')[:10]
            data['ultimas_atividades'] = LogAtividadeSerializer(
                ultimas_atividades, many=True
            ).data
            
            return Response(data)
            
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuário não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, user_id):
        """Atualiza dados do usuário (admin)"""
        try:
            usuario = Usuario.objects.get(id=user_id)
            serializer = UsuarioAdminSerializer(
                usuario, 
                data=request.data, 
                partial=True
            )
            
            if serializer.is_valid():
                usuario_atualizado = serializer.save()
                
                
                # Registra atividade administrativa
                LogAtividade.registrar_atividade(
                    usuario=request.user,
                    tipo_atividade='admin_action',
                    descricao=f'Dados do usuário {usuario.email} atualizados pelo administrador',
                    dados_extras=request.data
                )
                
                return Response({
                    'message': 'Usuário atualizado com sucesso',
                    'user': usuario_atualizado
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuário não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, user_id):
        """Desativa usuário (soft delete)"""
        try:
            usuario = Usuario.objects.get(id=user_id)
            
            # Não permite deletar administradores
            if usuario.is_admin:
                return Response({
                    'error': 'Não é possível desativar usuários administradores'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Desativa o usuário
            usuario.is_active = False
            usuario.save()
            
            # Registra atividade
            LogAtividade.registrar_atividade(
                usuario=request.user,
                tipo_atividade='admin_action',
                descricao=f'Usuário {usuario.email} desativado pelo administrador'
            )
            
            return Response({
                'message': 'Usuário desativado com sucesso'
            })
            
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuário não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class ModeracaoUsuarioView(APIView):
    """
    View para ações de moderação (bloquear/desbloquear usuários)
    """
    permission_classes = [IsModerador]
    
    def post(self, request, user_id):
        """Aplica ação de moderação"""
        try:
            usuario = Usuario.objects.get(id=user_id)
            
            # Não permite moderar administradores ou moderadores
            if usuario.is_admin or usuario.is_moderador:
                return Response({
                    'error': 'Não é possível moderar administradores ou moderadores'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = UsuarioModeracaoSerializer(
                usuario,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                
                return Response({
                    'message': 'Ação de moderação aplicada com sucesso',
                    'user': serializer.data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuário não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class EstatisticasView(APIView):
    """
    View para estatísticas do sistema de usuários
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Retorna estatísticas gerais do sistema"""
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        
        # Contadores básicos
        total_usuarios = Usuario.objects.count()
        usuarios_ativos = Usuario.objects.filter(is_active=True).count()
        usuarios_inativos = total_usuarios - usuarios_ativos
        
        # Por tipo de usuário
        total_pacientes = Usuario.objects.filter(is_paciente=True).count()
        total_moderadores = Usuario.objects.filter(is_moderador=True).count()
        total_administradores = Usuario.objects.filter(is_admin=True).count()
        
        # Novos usuários no mês
        novos_usuarios_mes = Usuario.objects.filter(
            created_at__gte=inicio_mes
        ).count()
        
        # Usuários bloqueados
        usuarios_bloqueados = Usuario.objects.filter(
            conta_bloqueada_ate__gt=timezone.now()
        ).count()
        
        # Logins hoje
        logins_hoje = LogAtividade.objects.filter(
            tipo_atividade='login',
            timestamp__date=hoje
        ).count()
        
        # Usuários por idioma
        usuarios_por_idioma = dict(
            Usuario.objects.values_list('idioma_preferido')
            .annotate(count=Count('idioma_preferido'))
            .order_by('-count')
        )
        
        estatisticas = {
            'total_usuarios': total_usuarios,
            'usuarios_ativos': usuarios_ativos,
            'usuarios_inativos': usuarios_inativos,
            'total_pacientes': total_pacientes,
            'total_moderadores': total_moderadores,
            'total_administradores': total_administradores,
            'novos_usuarios_mes': novos_usuarios_mes,
            'usuarios_bloqueados': usuarios_bloqueados,
            'logins_hoje': logins_hoje,
            'usuarios_por_idioma': usuarios_por_idioma
        }
        
        serializer = EstatisticasUsuarioSerializer(estatisticas)
        return Response(serializer.data)


class ExportarUsuariosView(APIView):
    """
    View para exportar dados de usuários em CSV
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Exporta usuários para CSV"""
        # Aplica filtros similares ao GerenciarUsuariosView
        queryset = Usuario.objects.all().order_by('-created_at')
        
        tipo_usuario = request.query_params.get('tipo')
        if tipo_usuario == 'paciente':
            queryset = queryset.filter(is_paciente=True)
        elif tipo_usuario == 'moderador':
            queryset = queryset.filter(is_moderador=True)
        elif tipo_usuario == 'admin':
            queryset = queryset.filter(is_admin=True)
        
        is_active = request.query_params.get('ativo')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Serializa os dados
        serializer = UsuarioExportacaoSerializer(queryset, many=True)
        
        # Cria o CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        if serializer.data:
            headers = list(serializer.data[0].keys())
            writer.writerow(headers)
            
            # Dados
            for item in serializer.data:
                row = []
                for field in headers:
                    value = item.get(field, '')
                    # Converte valores não string para string
                    if value is None:
                        value = ''
                    elif isinstance(value, bool):
                        value = 'Sim' if value else 'Não'
                    elif isinstance(value, datetime):
                        value = value.strftime('%d/%m/%Y %H:%M:%S')
                    row.append(str(value))
                writer.writerow(row)
        
        # Registra atividade
        LogAtividade.registrar_atividade(
            usuario=request.user,
            tipo_atividade='admin_action',
            descricao='Exportação de dados de usuários realizada'
        )
        
        # Resposta HTTP
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='text/csv'
        )
        response['Content-Disposition'] = f'attachment; filename="usuarios_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        return response


class LogsAdminView(APIView):
    """
    View para administradores visualizarem todos os logs
    """
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    
    def get(self, request):
        """Retorna logs de atividade de todos os usuários"""
        queryset = LogAtividade.objects.all().order_by('-timestamp')
        
        # Filtros
        usuario_id = request.query_params.get('usuario_id')
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        
        tipo_atividade = request.query_params.get('tipo')
        if tipo_atividade:
            queryset = queryset.filter(tipo_atividade=tipo_atividade)
        
        data_inicio = request.query_params.get('data_inicio')
        if data_inicio:
            try:
                data_inicio = datetime.fromisoformat(data_inicio.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=data_inicio)
            except ValueError:
                pass
        
        data_fim = request.query_params.get('data_fim')
        if data_fim:
            try:
                data_fim = datetime.fromisoformat(data_fim.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=data_fim)
            except ValueError:
                pass
        
        # Busca por IP
        ip_address = request.query_params.get('ip')
        if ip_address:
            queryset = queryset.filter(ip_address__icontains=ip_address)
        
        # Paginação
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LogAtividadeSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = LogAtividadeSerializer(queryset, many=True)
        return Response(serializer.data)


class UsuariosResumoView(APIView):
    """
    View para listagem resumida de usuários (para seleção em formulários)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retorna lista resumida de usuários ativos"""
        # Apenas usuários ativos
        queryset = Usuario.objects.filter(is_active=True).order_by('email')
        
        # Filtro por tipo se fornecido
        tipo = request.query_params.get('tipo')
        if tipo == 'paciente':
            queryset = queryset.filter(is_paciente=True)
        elif tipo == 'moderador':
            queryset = queryset.filter(is_moderador=True)
        
        # Busca
        # Continuação do arquivo usuarios/views.py

        # Busca por email
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(email__icontains=search)
        
        # Limita o número de resultados
        limit = request.query_params.get('limit', 50)
        try:
            limit = int(limit)
            if limit > 100:
                limit = 100
        except ValueError:
            limit = 50
        
        queryset = queryset[:limit]
        
        serializer = UsuarioResumoSerializer(queryset, many=True)
        return Response(serializer.data)


class ValidarTokenView(APIView):
    """
    View para validar tokens de autenticação
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Valida se o token está válido e retorna dados do usuário"""
        user_data = UsuarioSerializer(request.user).data
        
        return Response({
            'valid': True,
            'user': user_data,
            'expires_at': request.auth.payload.get('exp') if hasattr(request.auth, 'payload') else None
        })


class NotificacoesUsuarioView(APIView):
    """
    View para gerenciar notificações do usuário
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retorna configurações de notificação do usuário"""
        usuario = request.user
        return Response({
            'receber_email_notificacoes': usuario.receber_email_notificacoes,
            'receber_sms_notificacoes': usuario.receber_sms_notificacoes
        })
    
    def put(self, request):
        """Atualiza configurações de notificação"""
        usuario = request.user
        
        # Campos permitidos para atualização
        campos_permitidos = ['receber_email_notificacoes', 'receber_sms_notificacoes']
        dados_atualizados = {}
        
        for campo in campos_permitidos:
            if campo in request.data:
                valor = request.data[campo]
                if isinstance(valor, bool):
                    setattr(usuario, campo, valor)
                    dados_atualizados[campo] = valor
        
        if dados_atualizados:
            usuario.save()
            
            # Registra a atividade
            LogAtividade.registrar_atividade(
                usuario=usuario,
                tipo_atividade='profile_update',
                descricao='Configurações de notificação atualizadas',
                dados_extras=dados_atualizados
            )
            
            return Response({
                'message': 'Configurações de notificação atualizadas com sucesso',
                'data': dados_atualizados
            })
        
        return Response({
            'error': 'Nenhuma configuração válida fornecida'
        }, status=status.HTTP_400_BAD_REQUEST)


class AlterarIdiomaView(APIView):
    """
    View para alterar idioma preferido do usuário
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Altera o idioma preferido do usuário"""
        novo_idioma = request.data.get('idioma')
        
        # Idiomas suportados
        idiomas_suportados = dict(Usuario.IDIOMAS_CHOICES).keys()
        
        if not novo_idioma:
            return Response({
                'error': 'Idioma é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if novo_idioma not in idiomas_suportados:
            return Response({
                'error': f'Idioma não suportado. Idiomas disponíveis: {list(idiomas_suportados)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Atualiza o idioma
        usuario = request.user
        idioma_anterior = usuario.idioma_preferido
        usuario.idioma_preferido = novo_idioma
        usuario.save()
        
        # Registra a atividade
        LogAtividade.registrar_atividade(
            usuario=usuario,
            tipo_atividade='profile_update',
            descricao=f'Idioma alterado de {idioma_anterior} para {novo_idioma}'
        )
        
        return Response({
            'message': 'Idioma alterado com sucesso',
            'idioma_anterior': idioma_anterior,
            'novo_idioma': novo_idioma
        })


class DesativarContaView(APIView):
    """
    View para o usuário desativar sua própria conta
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Desativa a conta do usuário atual"""
        usuario = request.user
        
        # Verifica se é administrador
        if usuario.is_admin:
            return Response({
                'error': 'Administradores não podem desativar suas próprias contas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Confirma com senha
        senha = request.data.get('senha')
        if not senha:
            return Response({
                'error': 'Senha é obrigatória para desativar a conta'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not usuario.check_password(senha):
            return Response({
                'error': 'Senha incorreta'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Desativa a conta
        usuario.is_active = False
        usuario.save()
        
        # Registra a atividade
        LogAtividade.registrar_atividade(
            usuario=usuario,
            tipo_atividade='profile_update',
            descricao='Conta desativada pelo próprio usuário'
        )
        
        return Response({
            'message': 'Conta desativada com sucesso'
        })


class HistoricoSenhasView(APIView):
    """
    View para consultar histórico de mudanças de senha
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retorna histórico de mudanças de senha (sem as senhas)"""
        try:
            perfil_seguranca = request.user.perfil_seguranca
            
            # Conta quantas vezes a senha foi alterada
            historico_count = len(perfil_seguranca.historico_senhas) if perfil_seguranca.historico_senhas else 0
            
            return Response({
                'total_mudancas': historico_count,
                'ultima_mudanca': perfil_seguranca.ultima_mudanca_senha,
                'two_factor_enabled': perfil_seguranca.two_factor_enabled,
                'max_sessoes_simultaneas': perfil_seguranca.max_sessoes_simultaneas
            })
            
        except PerfilSeguranca.DoesNotExist:
            return Response({
                'total_mudancas': 0,
                'ultima_mudanca': None,
                'two_factor_enabled': False,
                'max_sessoes_simultaneas': 3
            })


class DispositivosConectadosView(APIView):
    """
    View para listar dispositivos conectados (sessões ativas)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lista dispositivos/sessões ativas do usuário"""
        # Esta implementação dependeria de um sistema de rastreamento de sessões
        # Por enquanto, retornamos informações básicas
        
        usuario = request.user
        return Response({
            'usuario': usuario.email,
            'ultimo_login': usuario.last_login,
            'ultimo_ip': usuario.ultimo_login_ip,
            'sessoes_ativas': 1,  # Seria calculado com base em tokens ativos
            'message': 'Para implementação completa, necessário sistema de rastreamento de sessões JWT'
        })


# ========== VIEWS ESPECÍFICAS PARA TIPOS DE USUÁRIO ==========

class PacientesView(APIView):
    """
    View específica para listar e gerenciar pacientes
    """
    permission_classes = [IsModerador]
    pagination_class = CustomPagination
    
    def get(self, request):
        """Lista todos os pacientes"""
        queryset = Usuario.objects.filter(
            is_paciente=True,
            is_active=True
        ).order_by('-created_at')
        
        # Filtros específicos para pacientes
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(telefone__icontains=search)
            )
        
        # Filtro por data de cadastro
        periodo = request.query_params.get('periodo')
        if periodo:
            hoje = timezone.now()
            if periodo == 'hoje':
                queryset = queryset.filter(created_at__date=hoje.date())
            elif periodo == 'semana':
                inicio_semana = hoje - timedelta(days=7)
                queryset = queryset.filter(created_at__gte=inicio_semana)
            elif periodo == 'mes':
                inicio_mes = hoje.replace(day=1)
                queryset = queryset.filter(created_at__gte=inicio_mes)
        
        # Paginação
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = UsuarioResumoSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = UsuarioResumoSerializer(queryset, many=True)
        return Response(serializer.data)


class ModeradoresView(APIView):
    """
    View específica para listar e gerenciar moderadores
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Lista todos os moderadores"""
        queryset = Usuario.objects.filter(
            is_moderador=True
        ).order_by('-created_at')
        
        serializer = UsuarioAdminSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Promove usuário a moderador"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({
                'error': 'ID do usuário é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            usuario = Usuario.objects.get(id=user_id)
            
            if usuario.is_admin:
                return Response({
                    'error': 'Administradores já possuem privilégios de moderação'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if usuario.is_moderador:
                return Response({
                    'error': 'Usuário já é moderador'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Promove a moderador
            usuario.is_moderador = True
            usuario.save()
            
            # Registra a atividade
            LogAtividade.registrar_atividade(
                usuario=request.user,
                tipo_atividade='admin_action',
                descricao=f'Usuário {usuario.email} promovido a moderador'
            )
            
            LogAtividade.registrar_atividade(
                usuario=usuario,
                tipo_atividade='profile_update',
                descricao='Promovido a moderador'
            )
            
            return Response({
                'message': f'Usuário {usuario.email} promovido a moderador com sucesso',
                'user': UsuarioAdminSerializer(usuario).data
            })
            
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuário não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, user_id):
        """Remove privilégios de moderador"""
        try:
            usuario = Usuario.objects.get(id=user_id)
            
            if not usuario.is_moderador:
                return Response({
                    'error': 'Usuário não é moderador'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if usuario.is_admin:
                return Response({
                    'error': 'Não é possível remover privilégios de administradores'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Remove privilégios de moderador
            usuario.is_moderador = False
            usuario.save()
            
            # Registra a atividade
            LogAtividade.registrar_atividade(
                usuario=request.user,
                tipo_atividade='admin_action',
                descricao=f'Privilégios de moderador removidos do usuário {usuario.email}'
            )
            
            LogAtividade.registrar_atividade(
                usuario=usuario,
                tipo_atividade='profile_update',
                descricao='Privilégios de moderador removidos'
            )
            
            return Response({
                'message': f'Privilégios de moderador removidos do usuário {usuario.email}'
            })
            
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuário não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class RelatoriosUsuariosView(APIView):
    """
    View para gerar relatórios sobre usuários
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Gera relatório detalhado de usuários"""
        # Período do relatório
        periodo = request.query_params.get('periodo', 'mes')
        hoje = timezone.now()
        
        if periodo == 'dia':
            data_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'semana':
            data_inicio = hoje - timedelta(days=7)
        elif periodo == 'mes':
            data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'ano':
            data_inicio = hoje.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Estatísticas básicas
        total_usuarios = Usuario.objects.count()
        usuarios_ativos = Usuario.objects.filter(is_active=True).count()
        
        # Novos usuários no período
        novos_usuarios = Usuario.objects.filter(
            created_at__gte=data_inicio
        ).count()
        
        # Logins no período
        logins_periodo = LogAtividade.objects.filter(
            tipo_atividade='login',
            timestamp__gte=data_inicio
        ).count()
        
        # Usuários por tipo
        usuarios_por_tipo = {
            'pacientes': Usuario.objects.filter(is_paciente=True).count(),
            'moderadores': Usuario.objects.filter(is_moderador=True).count(),
            'administradores': Usuario.objects.filter(is_admin=True).count()
        }
        
        # Top 10 usuários mais ativos
        usuarios_ativos_query = Usuario.objects.annotate(
            total_atividades=Count('atividades')
        ).filter(total_atividades__gt=0).order_by('-total_atividades')[:10]
        
        usuarios_mais_ativos = []
        for usuario in usuarios_ativos_query:
            usuarios_mais_ativos.append({
                'email': usuario.email,
                'tipo_usuario': usuario.get_tipo_usuario(),
                'total_atividades': usuario.total_atividades,
                'ultimo_login': usuario.last_login
            })
        
        # Usuários por idioma
        usuarios_por_idioma = dict(
            Usuario.objects.values_list('idioma_preferido')
            .annotate(count=Count('idioma_preferido'))
            .order_by('-count')
        )
        
        # Registra que o relatório foi gerado
        LogAtividade.registrar_atividade(
            usuario=request.user,
            tipo_atividade='admin_action',
            descricao=f'Relatório de usuários gerado (período: {periodo})'
        )
        
        relatorio = {
            'periodo': periodo,
            'data_inicio': data_inicio,
            'data_geracao': hoje,
            'estatisticas_gerais': {
                'total_usuarios': total_usuarios,
                'usuarios_ativos': usuarios_ativos,
                'usuarios_inativos': total_usuarios - usuarios_ativos,
                'novos_usuarios_periodo': novos_usuarios,
                'logins_periodo': logins_periodo
            },
            'usuarios_por_tipo': usuarios_por_tipo,
            'usuarios_mais_ativos': usuarios_mais_ativos,
            'usuarios_por_idioma': usuarios_por_idioma
        }
        
        return Response(relatorio)


class ConfiguracaoSistemaView(APIView):
    """
    View para configurações do sistema relacionadas a usuários
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Retorna configurações atuais do sistema"""
        # Estas configurações normalmente viriam de um modelo de configuração
        # ou do settings.py - aqui simulamos algumas configurações comuns
        
        configuracoes = {
            'registro_publico_ativo': True,
            'verificacao_email_obrigatoria': False,
            'max_tentativas_login': 5,
            'tempo_bloqueio_conta': 30,  # minutos
            'senha_min_length': 8,
            'senha_requer_numeros': True,
            'senha_requer_simbolos': True,
            'sessao_timeout': 24,  # horas
            'max_sessoes_simultaneas_padrao': 3,
            'notificacoes_email_padrao': True,
            'notificacoes_sms_padrao': False,
            'idioma_padrao': 'pt'
        }
        
        return Response(configuracoes)


class BackupUsuariosView(APIView):
    """
    View para criar backup dos dados de usuários
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """Cria um backup dos dados de usuários"""
       
        try:
            # Serializa todos os usuários
            usuarios = Usuario.objects.all()
            usuarios_data = []
            
            for usuario in usuarios:
                usuario_data = {
                    'email': usuario.email,
                    'telefone': usuario.telefone,
                    'is_active': usuario.is_active,
                    'is_admin': usuario.is_admin,
                    'is_paciente': usuario.is_paciente,
                    'is_moderador': usuario.is_moderador,
                    'idioma_preferido': usuario.idioma_preferido,
                    'timezone_usuario': usuario.timezone_usuario,
                    'created_at': usuario.created_at.isoformat(),
                    'last_login': usuario.last_login.isoformat() if usuario.last_login else None
                }
                usuarios_data.append(usuario_data)
            
            # Cria o arquivo de backup
            backup_data = {
                'data_backup': timezone.now().isoformat(),
                'total_usuarios': len(usuarios_data),
                'usuarios': usuarios_data
            }
            
            # Registra a atividade
            LogAtividade.registrar_atividade(
                usuario=request.user,
                tipo_atividade='admin_action',
                descricao=f'Backup de usuários criado ({len(usuarios_data)} usuários)'
            )
            
            # Retorna o backup como JSON
            response = HttpResponse(
                json.dumps(backup_data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="backup_usuarios_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Erro ao criar backup: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== VIEW PARA SAÚDE DO SISTEMA ==========

class HealthCheckView(APIView):
    """
    View para verificar a saúde do sistema de usuários
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Verifica a saúde do sistema"""
        try:
            # Testa conexão com banco de dados
            total_usuarios = Usuario.objects.count()
            
            # Verifica se há usuários administradores ativos
            admin_ativo = Usuario.objects.filter(
                is_admin=True,
                is_active=True
            ).exists()
            
            # Status geral
            status_sistema = 'healthy' if admin_ativo else 'warning'
            
            health_data = {
                'status': status_sistema,
                'timestamp': timezone.now(),
                'database': 'connected',
                'total_usuarios': total_usuarios,
                'admin_ativo': admin_ativo,
                'version': '1.0.0'
            }
            
            return Response(health_data)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'timestamp': timezone.now(),
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)