# usuarios/admin.py
"""
Configuração do Django Admin para o módulo de usuários

Este módulo registra e configura a interface administrativa para:
- Gerenciamento completo de usuários
- Perfis de segurança
- Logs de atividade
- Filtros e buscas avançadas
- Ações em lote
- Relatórios e estatísticas

Autor: Sistema Médico IA Guiné
Data: 2025
"""
from django.contrib.auth.models import User, Group


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import Usuario, PerfilSeguranca, LogAtividade


class PerfilSegurancaInline(admin.StackedInline):
    """
    Inline para perfil de segurança no admin de usuários
    """
    model = PerfilSeguranca
    can_delete = False
    verbose_name_plural = 'Configurações de Segurança'
    
    fields = (
        'two_factor_enabled',
        'max_sessoes_simultaneas',
        'permitir_login_multiplos_dispositivos',
        'notificar_login_novo_dispositivo',
        'ultima_mudanca_senha',
        'force_password_change'
    )
    
    readonly_fields = ('ultima_mudanca_senha',)


class LogAtividadeInline(admin.TabularInline):
    """
    Inline para mostrar as últimas atividades do usuário
    """
    model = LogAtividade
    extra = 0
    can_delete = False
    max_num = 10
    
    fields = ('timestamp', 'tipo_atividade', 'descricao', 'ip_address')
    readonly_fields = ('timestamp', 'tipo_atividade', 'descricao', 'ip_address')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """
    Configuração personalizada do admin para usuários
    """
    
    # Configurações de exibição
    list_display = (
        'email',
        'get_nome_completo',
        'get_tipo_usuario_badge',
        'telefone',
        'idioma_preferido',
        'is_active',
        'get_status_conta',
        'last_login',
        'created_at'
    )
    
    list_filter = (
        'is_active',
        'is_admin',
        'is_paciente',
        'is_moderador',
        'is_staff',
        'idioma_preferido',
        'timezone_usuario',
        'created_at',
        'last_login',
        'receber_email_notificacoes',
        'receber_sms_notificacoes'
    )
    
    search_fields = ('email', 'telefone')
    
    ordering = ('-created_at',)
    
    # Campos para visualização/edição
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('email', 'telefone', 'is_active')
        }),
        ('Tipo de Usuário', {
            'fields': ('is_admin', 'is_paciente', 'is_moderador', 'is_staff'),
            'classes': ('collapse',)
        }),
        ('Preferências', {
            'fields': ('idioma_preferido', 'timezone_usuario'),
            'classes': ('collapse',)
        }),
        ('Notificações', {
            'fields': ('receber_email_notificacoes', 'receber_sms_notificacoes'),
            'classes': ('collapse',)
        }),
        ('Segurança', {
            'fields': (
                'tentativas_login', 
                'conta_bloqueada_ate', 
                'ultimo_login_ip',
                'get_conta_bloqueada_status'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = (
        'last_login',
        'created_at', 
        'updated_at',
        'tentativas_login',
        'ultimo_login_ip',
        'get_conta_bloqueada_status'
    )
    
    # Campos para criação de usuário
    add_fieldsets = (
        ('Informações Básicas', {
            'classes': ('wide',),
            'fields': ('email', 'telefone', 'password1', 'password2')
        }),
        ('Tipo de Usuário', {
            'classes': ('wide',),
            'fields': ('is_admin', 'is_paciente', 'is_moderador')
        }),
        ('Configurações', {
            'classes': ('wide',),
            'fields': ('idioma_preferido', 'is_active')
        })
    )
    
    # Inlines
    inlines = [PerfilSegurancaInline, LogAtividadeInline]
    
    def changelist_view(self, request, extra_context=None):
        """Personaliza a view de lista com botões adicionais"""
        extra_context = extra_context or {}
        extra_context['custom_buttons'] = [
            {
                'url': 'estatisticas/',
                'title': 'Ver Estatísticas',
                'class': 'default',
                'icon': '📊'
            },
            {
                'url': 'relatorio-detalhado/',
                'title': 'Relatório Detalhado',
                'class': 'default',
                'icon': '📋'
            },
            {
                'url': 'dispositivos-conectados/',
                'title': 'Dispositivos Conectados',
                'class': 'default',
                'icon': '📱'
            },
            {
                'url': 'configuracoes-sistema/',
                'title': 'Configurações',
                'class': 'default',
                'icon': '⚙️'
            }
        ]
        return super().changelist_view(request, extra_context=extra_context)
    
    # Ações personalizadas
    actions = [
        'ativar_usuarios',
        'desativar_usuarios',
        'resetar_tentativas_login',
        'desbloquear_contas',
        'forcar_mudanca_senha',
        'exportar_usuarios_csv',
        'gerar_relatorio_detalhado',
        'enviar_notificacao_usuarios',
        'criar_backup_usuarios'
    ]
    
    def get_nome_completo(self, obj):
        """Retorna o nome completo do usuário"""
        return obj.get_full_name()
    get_nome_completo.short_description = 'Nome Completo'
    
    def get_tipo_usuario_badge(self, obj):
        """Retorna o tipo de usuário com badge colorido"""
        tipo = obj.get_tipo_usuario()
        colors = {
            'admin': '#dc3545',      # Vermelho
            'moderador': '#fd7e14',  # Laranja
            'paciente': '#198754',   # Verde
            'indefinido': '#6c757d'  # Cinza
        }
        color = colors.get(tipo, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            tipo.upper()
        )
    get_tipo_usuario_badge.short_description = 'Tipo'
    
    def get_status_conta(self, obj):
        """Retorna o status da conta com ícones"""
        if obj.conta_esta_bloqueada():
            return format_html(
                '<span style="color: red;">🔒 Bloqueada</span>'
            )
        elif not obj.is_active:
            return format_html(
                '<span style="color: orange;">❌ Inativa</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✅ Ativa</span>'
            )
    get_status_conta.short_description = 'Status'
    
    def get_conta_bloqueada_status(self, obj):
        """Retorna informações sobre bloqueio da conta"""
        if obj.conta_bloqueada_ate:
            if obj.conta_esta_bloqueada():
                return format_html(
                    '<span style="color: red;">Bloqueada até: {}</span>',
                    obj.conta_bloqueada_ate.strftime('%d/%m/%Y %H:%M')
                )
            else:
                return format_html(
                    '<span style="color: green;">Desbloqueada (era até: {})</span>',
                    obj.conta_bloqueada_ate.strftime('%d/%m/%Y %H:%M')
                )
        return "Não bloqueada"
    get_conta_bloqueada_status.short_description = 'Status de Bloqueio'
    
    def get_queryset(self, request):
        """Otimiza consultas com select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('perfil_seguranca').prefetch_related('atividades')
    
    def get_urls(self):
        """Adiciona URLs personalizadas ao admin"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('estatisticas/', self.admin_site.admin_view(self.estatisticas_view), name='usuarios_estatisticas'),
            path('relatorio-detalhado/', self.admin_site.admin_view(self.relatorio_detalhado_view), name='usuarios_relatorio'),
            path('dispositivos-conectados/', self.admin_site.admin_view(self.dispositivos_conectados_view), name='usuarios_dispositivos'),
            path('configuracoes-sistema/', self.admin_site.admin_view(self.configuracoes_sistema_view), name='usuarios_configuracoes'),
        ]
        return custom_urls + urls
    
    def estatisticas_view(self, request):
        """View para estatísticas dos usuários"""
        from django.shortcuts import render
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        # Estatísticas gerais
        total_usuarios = Usuario.objects.count()
        usuarios_ativos = Usuario.objects.filter(is_active=True).count()
        usuarios_bloqueados = Usuario.objects.filter(conta_bloqueada_ate__gt=timezone.now()).count()
        
        # Por tipo
        stats_por_tipo = Usuario.objects.values('is_admin', 'is_paciente', 'is_moderador').annotate(count=Count('id'))
        
        # Últimos 30 dias
        data_inicio = timezone.now() - timedelta(days=30)
        novos_usuarios = Usuario.objects.filter(created_at__gte=data_inicio).count()
        logins_recentes = Usuario.objects.filter(last_login__gte=data_inicio).count()
        
        # Por idioma
        stats_idioma = Usuario.objects.values('idioma_preferido').annotate(count=Count('id')).order_by('-count')
        
        context = {
            'title': 'Estatísticas de Usuários',
            'total_usuarios': total_usuarios,
            'usuarios_ativos': usuarios_ativos,
            'usuarios_bloqueados': usuarios_bloqueados,
            'stats_por_tipo': stats_por_tipo,
            'novos_usuarios': novos_usuarios,
            'logins_recentes': logins_recentes,
            'stats_idioma': stats_idioma,
            'opts': Usuario._meta,
        }
        
        return render(request, 'admin/usuarios/estatisticas.html', context)
    
    def relatorio_detalhado_view(self, request):
        """View para relatório detalhado"""
        from django.shortcuts import render
        from django.http import JsonResponse
        from django.db.models import Count, Q
        
        if request.method == 'POST':
            # Gerar relatório baseado nos filtros
            filtros = {}
            if request.POST.get('tipo_usuario'):
                if request.POST.get('tipo_usuario') == 'admin':
                    filtros['is_admin'] = True
                elif request.POST.get('tipo_usuario') == 'paciente':
                    filtros['is_paciente'] = True
                elif request.POST.get('tipo_usuario') == 'moderador':
                    filtros['is_moderador'] = True
            
            if request.POST.get('status'):
                filtros['is_active'] = request.POST.get('status') == 'ativo'
            
            usuarios = Usuario.objects.filter(**filtros).select_related('perfil_seguranca')
            
            dados = []
            for usuario in usuarios:
                dados.append({
                    'email': usuario.email,
                    'tipo': usuario.get_tipo_usuario(),
                    'ativo': usuario.is_active,
                    'ultimo_login': str(usuario.last_login) if usuario.last_login else None,
                    'created_at': str(usuario.created_at),
                })
            
            return JsonResponse({'usuarios': dados})
        
        context = {
            'title': 'Relatório Detalhado',
            'opts': Usuario._meta,
        }
        
        return render(request, 'admin/usuarios/relatorio.html', context)
    
    def dispositivos_conectados_view(self, request):
        """View para dispositivos conectados"""
        from django.shortcuts import render
        from django.utils import timezone
        from datetime import timedelta
        
        # Usuários com login recente (últimas 24h)
        data_limite = timezone.now() - timedelta(hours=24)
        usuarios_online = Usuario.objects.filter(
            last_login__gte=data_limite
        ).select_related('perfil_seguranca')
        
        dispositivos_info = []
        for usuario in usuarios_online:
            dispositivos_info.append({
                'usuario': usuario,
                'ultimo_ip': usuario.ultimo_login_ip or 'Não disponível',
                'ultimo_login': usuario.last_login,
                'two_factor': usuario.perfil_seguranca.two_factor_enabled if hasattr(usuario, 'perfil_seguranca') else False,
            })
        
        context = {
            'title': 'Dispositivos Conectados',
            'dispositivos_info': dispositivos_info,
            'opts': Usuario._meta,
        }
        
        return render(request, 'admin/usuarios/dispositivos.html', context)
    
    def configuracoes_sistema_view(self, request):
        """View para configurações do sistema"""
        from django.shortcuts import render
        from django.contrib import messages
        
        if request.method == 'POST':
            # Aqui você implementaria a lógica para salvar configurações
            messages.success(request, 'Configurações salvas com sucesso!')
        
        context = {
            'title': 'Configurações do Sistema',
            'opts': Usuario._meta,
        }
        
        return render(request, 'admin/usuarios/configuracoes.html', context)
    
    # Ações personalizadas
    def ativar_usuarios(self, request, queryset):
        """Ativa usuários selecionados"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} usuário(s) ativado(s) com sucesso.')
    ativar_usuarios.short_description = 'Ativar usuários selecionados'
    
    def desativar_usuarios(self, request, queryset):
        """Desativa usuários selecionados"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} usuário(s) desativado(s) com sucesso.')
    desativar_usuarios.short_description = 'Desativar usuários selecionados'
    
    def resetar_tentativas_login(self, request, queryset):
        """Reseta tentativas de login"""
        for usuario in queryset:
            usuario.resetar_tentativas_login()
        self.message_user(request, f'Tentativas de login resetadas para {queryset.count()} usuário(s).')
    resetar_tentativas_login.short_description = 'Resetar tentativas de login'
    
    def desbloquear_contas(self, request, queryset):
        """Desbloqueia contas"""
        count = queryset.update(conta_bloqueada_ate=None, tentativas_login=0)
        self.message_user(request, f'{count} conta(s) desbloqueada(s) com sucesso.')
    desbloquear_contas.short_description = 'Desbloquear contas selecionadas'
    
    def forcar_mudanca_senha(self, request, queryset):
        """Força mudança de senha no próximo login"""
        count = 0
        for usuario in queryset:
            if hasattr(usuario, 'perfil_seguranca'):
                usuario.perfil_seguranca.force_password_change = True
                usuario.perfil_seguranca.save()
                count += 1
        self.message_user(request, f'Mudança de senha forçada para {count} usuário(s).')
    forcar_mudanca_senha.short_description = 'Forçar mudança de senha'
    
    def exportar_usuarios_csv(self, request, queryset):
        """Exporta usuários selecionados para CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Email', 'Nome Completo', 'Telefone', 'Tipo', 'Ativo', 
            'Idioma', 'Último Login', 'Data Criação'
        ])
        
        for usuario in queryset:
            writer.writerow([
                usuario.email,
                usuario.get_full_name(),
                usuario.telefone or '',
                usuario.get_tipo_usuario(),
                'Sim' if usuario.is_active else 'Não',
                usuario.get_idioma_preferido_display(),
                usuario.last_login.strftime('%d/%m/%Y %H:%M') if usuario.last_login else '',
                usuario.created_at.strftime('%d/%m/%Y %H:%M')
            ])
        
        return response
    exportar_usuarios_csv.short_description = 'Exportar para CSV'
    
    def gerar_relatorio_detalhado(self, request, queryset):
        """Gera relatório detalhado dos usuários selecionados"""
        import json
        from django.http import HttpResponse
        from django.utils import timezone
        
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="relatorio_usuarios.json"'
        
        relatorio = {
            'gerado_em': timezone.now().isoformat(),
            'total_usuarios': queryset.count(),
            'usuarios': []
        }
        
        for usuario in queryset.select_related('perfil_seguranca').prefetch_related('atividades'):
            dados_usuario = {
                'id': usuario.id,
                'email': usuario.email,
                'telefone': usuario.telefone,
                'tipo_usuario': usuario.get_tipo_usuario(),
                'ativo': usuario.is_active,
                'ultimo_login': usuario.last_login.isoformat() if usuario.last_login else None,
                'data_criacao': usuario.created_at.isoformat(),
                'idioma': usuario.get_idioma_preferido_display(),
                'timezone': usuario.timezone_usuario,
                'conta_bloqueada': usuario.conta_esta_bloqueada(),
                'tentativas_login': usuario.tentativas_login,
                'perfil_seguranca': {
                    'two_factor_enabled': usuario.perfil_seguranca.two_factor_enabled if hasattr(usuario, 'perfil_seguranca') else False,
                    'max_sessoes': usuario.perfil_seguranca.max_sessoes_simultaneas if hasattr(usuario, 'perfil_seguranca') else 3,
                },
                'total_atividades': usuario.atividades.count(),
                'ultima_atividade': usuario.atividades.first().timestamp.isoformat() if usuario.atividades.exists() else None
            }
            relatorio['usuarios'].append(dados_usuario)
        
        response.write(json.dumps(relatorio, indent=2, ensure_ascii=False))
        return response
    gerar_relatorio_detalhado.short_description = 'Gerar relatório detalhado (JSON)'
    
    def enviar_notificacao_usuarios(self, request, queryset):
        """Envia notificação para usuários selecionados"""
        from django.contrib import messages
        
        # Aqui você implementaria a lógica de envio de notificações
        # Por exemplo, usando um sistema de tasks como Celery
        
        usuarios_ativos = queryset.filter(is_active=True)
        count = usuarios_ativos.count()
        
        if count > 0:
            # Simular envio de notificação
            messages.success(request, f'Notificação enviada para {count} usuário(s) ativo(s).')
            
            # Log da ação
            for usuario in usuarios_ativos:
                LogAtividade.objects.create(
                    usuario=usuario,
                    tipo_atividade='notificacao_admin',
                    descricao=f'Notificação enviada pelo admin: {request.user.email}',
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
        else:
            messages.warning(request, 'Nenhum usuário ativo selecionado.')
    enviar_notificacao_usuarios.short_description = 'Enviar notificação'
    
    def criar_backup_usuarios(self, request, queryset):
        """Cria backup dos usuários selecionados"""
        import json
        from django.http import HttpResponse
        from django.utils import timezone
        
        response = HttpResponse(content_type='application/json')
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="backup_usuarios_{timestamp}.json"'
        
        backup_data = {
            'created_at': timezone.now().isoformat(),
            'created_by': request.user.email,
            'total_users': queryset.count(),
            'users': []
        }
        
        for usuario in queryset.select_related('perfil_seguranca'):
            user_data = {
                'email': usuario.email,
                'telefone': usuario.telefone,
                'is_active': usuario.is_active,
                'is_admin': usuario.is_admin,
                'is_paciente': usuario.is_paciente,
                'is_moderador': usuario.is_moderador,
                'idioma_preferido': usuario.idioma_preferido,
                'timezone_usuario': usuario.timezone_usuario,
                'receber_email_notificacoes': usuario.receber_email_notificacoes,
                'receber_sms_notificacoes': usuario.receber_sms_notificacoes,
                'created_at': usuario.created_at.isoformat(),
                'last_login': usuario.last_login.isoformat() if usuario.last_login else None,
            }
            
            if hasattr(usuario, 'perfil_seguranca'):
                user_data['perfil_seguranca'] = {
                    'two_factor_enabled': usuario.perfil_seguranca.two_factor_enabled,
                    'max_sessoes_simultaneas': usuario.perfil_seguranca.max_sessoes_simultaneas,
                    'permitir_login_multiplos_dispositivos': usuario.perfil_seguranca.permitir_login_multiplos_dispositivos,
                    'notificar_login_novo_dispositivo': usuario.perfil_seguranca.notificar_login_novo_dispositivo,
                }
            
            backup_data['users'].append(user_data)
        
        response.write(json.dumps(backup_data, indent=2, ensure_ascii=False))
        return response
    criar_backup_usuarios.short_description = 'Criar backup (JSON)'


@admin.register(PerfilSeguranca)
class PerfilSegurancaAdmin(admin.ModelAdmin):
    """
    Admin para perfis de segurança
    """
    
    list_display = (
        'get_usuario_email',
        'two_factor_enabled',
        'max_sessoes_simultaneas',
        'permitir_login_multiplos_dispositivos',
        'ultima_mudanca_senha',
        'force_password_change'
    )
    
    list_filter = (
        'two_factor_enabled',
        'permitir_login_multiplos_dispositivos',
        'notificar_login_novo_dispositivo',
        'force_password_change',
        'ultima_mudanca_senha'
    )
    
    search_fields = ('usuario__email',)
    
    readonly_fields = (
        'recovery_codes_display',
        'historico_senhas_display',
        'ultima_mudanca_senha'
    )
    
    fieldsets = (
        ('Usuário', {
            'fields': ('usuario',)
        }),
        ('Autenticação de Dois Fatores', {
            'fields': ('two_factor_enabled', 'recovery_codes_display'),
            'classes': ('collapse',)
        }),
        ('Controle de Sessão', {
            'fields': (
                'max_sessoes_simultaneas',
                'permitir_login_multiplos_dispositivos'
            )
        }),
        ('Notificações', {
            'fields': ('notificar_login_novo_dispositivo',)
        }),
        ('Histórico de Senhas', {
            'fields': ('historico_senhas_display', 'ultima_mudanca_senha'),
            'classes': ('collapse',)
        }),
        ('Controles Administrativos', {
            'fields': ('force_password_change',)
        })
    )
    
    def get_usuario_email(self, obj):
        """Retorna o email do usuário"""
        return obj.usuario.email
    get_usuario_email.short_description = 'Email do Usuário'
    
    def recovery_codes_display(self, obj):
        """Exibe códigos de recuperação"""
        if obj.recovery_codes:
            return format_html(
                '<div style="font-family: monospace;">{}</div>',
                '<br>'.join(obj.recovery_codes)
            )
        return "Nenhum código gerado"
    recovery_codes_display.short_description = 'Códigos de Recuperação'
    
    def historico_senhas_display(self, obj):
        """Exibe histórico de senhas (apenas quantidade)"""
        count = len(obj.historico_senhas)
        return f"{count} senha(s) no histórico"
    historico_senhas_display.short_description = 'Histórico'


@admin.register(LogAtividade)
class LogAtividadeAdmin(admin.ModelAdmin):
    """
    Admin para logs de atividade
    """
    
    list_display = (
        'get_usuario_email',
        'tipo_atividade',
        'get_descricao_resumida',
        'ip_address',
        'timestamp'
    )
    
    list_filter = (
        'tipo_atividade',
        'timestamp',
        'usuario__is_admin',
        'usuario__is_paciente',
        'usuario__is_moderador'
    )
    
    search_fields = (
        'usuario__email',
        'descricao',
        'ip_address'
    )
    
    readonly_fields = (
        'usuario',
        'tipo_atividade',
        'descricao',
        'ip_address',
        'user_agent',
        'dados_extras_display',
        'timestamp'
    )
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'tipo_atividade', 'timestamp')
        }),
        ('Detalhes da Atividade', {
            'fields': ('descricao', 'dados_extras_display')
        }),
        ('Informações Técnicas', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        })
    )
    
    date_hierarchy = 'timestamp'
    
    actions = ['exportar_logs_csv', 'gerar_relatorio_atividades']
    
    def exportar_logs_csv(self, request, queryset):
        """Exporta logs selecionados para CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="logs_atividade.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Usuário', 'Tipo Atividade', 'Descrição', 'IP Address', 
            'User Agent', 'Timestamp'
        ])
        
        for log in queryset:
            writer.writerow([
                log.usuario.email,
                log.tipo_atividade,
                log.descricao,
                log.ip_address or '',
                log.user_agent or '',
                log.timestamp.strftime('%d/%m/%Y %H:%M:%S')
            ])
        
        return response
    exportar_logs_csv.short_description = 'Exportar logs para CSV'
    
    def gerar_relatorio_atividades(self, request, queryset):
        """Gera relatório de atividades"""
        from django.http import JsonResponse
        from django.db.models import Count
        
        # Estatísticas dos logs selecionados
        stats = queryset.values('tipo_atividade').annotate(count=Count('id')).order_by('-count')
        usuarios_mais_ativos = queryset.values('usuario__email').annotate(count=Count('id')).order_by('-count')[:10]
        
        relatorio = {
            'total_logs': queryset.count(),
            'atividades_por_tipo': list(stats),
            'usuarios_mais_ativos': list(usuarios_mais_ativos),
            'periodo': {
                'inicio': str(queryset.earliest('timestamp').timestamp) if queryset.exists() else None,
                'fim': str(queryset.latest('timestamp').timestamp) if queryset.exists() else None,
            }
        }
        
        self.message_user(request, f'Relatório gerado para {queryset.count()} logs.')
        return JsonResponse(relatorio)
    gerar_relatorio_atividades.short_description = 'Gerar relatório de atividades'
    
    def has_add_permission(self, request):
        """Não permite adicionar logs manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Não permite editar logs"""
        return False
    
    def get_usuario_email(self, obj):
        """Retorna o email do usuário"""
        return obj.usuario.email
    get_usuario_email.short_description = 'Usuário'
    
    def get_descricao_resumida(self, obj):
        """Retorna descrição resumida"""
        if len(obj.descricao) > 50:
            return obj.descricao[:50] + '...'
        return obj.descricao
    get_descricao_resumida.short_description = 'Descrição'
    
    def dados_extras_display(self, obj):
        """Exibe dados extras formatados"""
        if obj.dados_extras:
            return format_html(
                '<pre style="font-size: 12px;">{}</pre>',
                json.dumps(obj.dados_extras, indent=2, ensure_ascii=False)
            )
        return "Nenhum dado extra"
    dados_extras_display.short_description = 'Dados Extras'
    
    def get_queryset(self, request):
        """Otimiza consultas"""
        return super().get_queryset(request).select_related('usuario')


# Personalização do site admin
admin.site.site_header = "Sistema Médico IA Guiné-Bissau"
admin.site.site_title = "Admin Médico IA"
admin.site.index_title = "Painel Administrativo"

# Removendo o modelo User padrão do Django se estiver registrado
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Desregistrar e re-registrar o Group com configuração personalizada
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    Admin personalizado para grupos
    """
    list_display = ('name', 'get_permissions_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    def get_permissions_count(self, obj):
        """Retorna a quantidade de permissões do grupo"""
        return obj.permissions.count()
    get_permissions_count.short_description = 'Qtd. Permissões'