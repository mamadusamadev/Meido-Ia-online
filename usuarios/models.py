# usuarios/models.py
"""
Modelos de Usuário Personalizado para o Sistema Médico IA Guiné-Bissau

Este módulo implementa um sistema de usuário personalizado com diferentes tipos:
- Administrador: Acesso completo ao sistema
- Paciente: Usuário final que utiliza os serviços médicos
- Moderador: Usuário com permissões específicas para moderação

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from .managers import UsuarioManager


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário personalizado para o sistema.
    
    Estende AbstractBaseUser para permitir autenticação com email
    ao invés de username tradicional.
    
    Attributes:
        email (str): Email único do usuário (usado como username)
        telefone (str): Número de telefone no formato da Guiné-Bissau
        is_active (bool): Se o usuário está ativo no sistema
        is_staff (bool): Se o usuário é staff (acesso ao admin)
        is_admin (bool): Se o usuário é administrador do sistema
        is_paciente (bool): Se o usuário é um paciente
        is_moderador (bool): Se o usuário é moderador
        idioma_preferido (str): Idioma preferido (Português/Crioulo)
        created_at (datetime): Data de criação da conta
        updated_at (datetime): Última atualização da conta
        ultimo_login_ip (str): IP do último login
        tentativas_login (int): Contador de tentativas de login falhadas
        conta_bloqueada_ate (datetime): Data até quando a conta está bloqueada
    """
    
    # Choices para tipos de usuário
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('paciente', 'Paciente'),
        ('moderador', 'Moderador'),
    ]
    
    # Choices para idiomas
    IDIOMA_CHOICES = [
        ('pt', 'Português'),
        ('gcr', 'Crioulo da Guiné-Bissau'),
        ('fr', 'Francês'),
    ]
    
    # Validador para telefone da Guiné-Bissau
    telefone_validator = RegexValidator(
        regex=r'^(\+245)?9[0-9]{8}$',
        message='Formato de telefone inválido. Use +245XXXXXXX ou XXXXXXX'
    )
    
    # Campos principais
    email = models.EmailField(
        verbose_name='Email',
        max_length=255,
        unique=True,
        help_text='Email único do usuário'
    )
    
    telefone = models.CharField(
        max_length=15,
        validators=[telefone_validator],
        blank=True,
        null=True,
        help_text='Telefone no formato +245XXXXXXX'
    )
    
    # Flags de tipo de usuário
    is_active = models.BooleanField(
        default=True,
        help_text='Designa se este usuário deve ser tratado como ativo.'
    )
    
    is_staff = models.BooleanField(
        default=False,
        help_text='Designa se o usuário pode acessar o site de administração.'
    )
    
    is_admin = models.BooleanField(
        default=False,
        help_text='Usuário tem acesso completo ao sistema'
    )
    
    is_paciente = models.BooleanField(
        default=False,
        help_text='Usuário é um paciente do sistema'
    )
    
    is_moderador = models.BooleanField(
        default=False,
        help_text='Usuário pode moderar consultas e conteúdo'
    )
    
    # Configurações pessoais
    idioma_preferido = models.CharField(
        max_length=3,
        choices=IDIOMA_CHOICES,
        default='pt',
        help_text='Idioma preferido da interface'
    )
    
    timezone_usuario = models.CharField(
        max_length=50,
        default='Africa/Bissau',
        help_text='Fuso horário do usuário'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Data de criação da conta'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Última atualização da conta'
    )
    
    # Segurança e auditoria
    ultimo_login_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text='IP do último login'
    )
    
    tentativas_login = models.PositiveIntegerField(
        default=0,
        help_text='Número de tentativas de login falhadas'
    )
    
    conta_bloqueada_ate = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Data até quando a conta está bloqueada'
    )
    
    # Configurações de notificação
    receber_email_notificacoes = models.BooleanField(
        default=True,
        help_text='Receber notificações por email'
    )
    
    receber_sms_notificacoes = models.BooleanField(
        default=False,
        help_text='Receber notificações por SMS'
    )
    
    # Manager personalizado
    objects = UsuarioManager()
    
    # Configurações do Django
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'usuarios_usuario'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'is_paciente']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        """Representação string do usuário"""
        return self.email
    
    def get_full_name(self):
        """Retorna o nome completo do usuário"""
        if hasattr(self, 'paciente'):
            return self.paciente.nome_completo
        return self.email
    
    def get_short_name(self):
        """Retorna o nome curto do usuário"""
        if hasattr(self, 'paciente'):
            nome_partes = self.paciente.nome_completo.split()
            return nome_partes[0] if nome_partes else self.email.split('@')[0]
        return self.email.split('@')[0]
    
    def get_tipo_usuario(self):
        """Retorna o tipo de usuário como string"""
        if self.is_admin:
            return 'admin'
        elif self.is_moderador:
            return 'moderador'
        elif self.is_paciente:
            return 'paciente'
        return 'indefinido'
    
    def pode_acessar_admin(self):
        """Verifica se o usuário pode acessar o painel administrativo"""
        return self.is_admin or self.is_staff
    
    def pode_moderar_consultas(self):
        """Verifica se o usuário pode moderar consultas"""
        return self.is_admin or self.is_moderador
    
    def conta_esta_bloqueada(self):
        """Verifica se a conta está bloqueada"""
        if self.conta_bloqueada_ate:
            return timezone.now() < self.conta_bloqueada_ate
        return False
    
    def resetar_tentativas_login(self):
        """Reseta o contador de tentativas de login"""
        self.tentativas_login = 0
        self.conta_bloqueada_ate = None
        self.save(update_fields=['tentativas_login', 'conta_bloqueada_ate'])
    
    def incrementar_tentativas_login(self):
        """
        Incrementa as tentativas de login e bloqueia a conta se necessário
        
        Bloqueia por:
        - 15 minutos após 5 tentativas
        - 1 hora após 10 tentativas
        - 24 horas após 15 tentativas
        """
        self.tentativas_login += 1
        
        if self.tentativas_login >= 15:
            # Bloquear por 24 horas
            self.conta_bloqueada_ate = timezone.now() + timezone.timedelta(hours=24)
        elif self.tentativas_login >= 10:
            # Bloquear por 1 hora
            self.conta_bloqueada_ate = timezone.now() + timezone.timedelta(hours=1)
        elif self.tentativas_login >= 5:
            # Bloquear por 15 minutos
            self.conta_bloqueada_ate = timezone.now() + timezone.timedelta(minutes=15)
        
        self.save(update_fields=['tentativas_login', 'conta_bloqueada_ate'])
    
    def atualizar_ultimo_login(self, ip_address=None):
        """Atualiza informações do último login"""
        self.last_login = timezone.now()
        if ip_address:
            self.ultimo_login_ip = ip_address
        self.resetar_tentativas_login()
        self.save(update_fields=['last_login', 'ultimo_login_ip'])


class PerfilSeguranca(models.Model):
    """
    Modelo para armazenar informações de segurança adicionais do usuário
    
    Mantém histórico de atividades sensíveis e configurações de segurança
    """
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_seguranca'
    )
    
    # Autenticação de dois fatores
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text='2FA habilitado'
    )
    
    two_factor_secret = models.CharField(
        max_length=32,
        blank=True,
        help_text='Chave secreta para 2FA'
    )
    
    # Códigos de recuperação
    recovery_codes = models.JSONField(
        default=list,
        help_text='Códigos de recuperação para 2FA'
    )
    
    # Histórico de senhas
    historico_senhas = models.JSONField(
        default=list,
        help_text='Hash das últimas 5 senhas para evitar reutilização'
    )
    
    # Sessões ativas
    max_sessoes_simultaneas = models.PositiveIntegerField(
        default=3,
        help_text='Máximo de sessões simultâneas permitidas'
    )
    
    # Auditoria
    ultima_mudanca_senha = models.DateTimeField(
        auto_now_add=True,
        help_text='Data da última mudança de senha'
    )
    
    force_password_change = models.BooleanField(
        default=False,
        help_text='Forçar mudança de senha no próximo login'
    )
    
    # Configurações de segurança
    permitir_login_multiplos_dispositivos = models.BooleanField(
        default=True,
        help_text='Permitir login em múltiplos dispositivos'
    )
    
    notificar_login_novo_dispositivo = models.BooleanField(
        default=True,
        help_text='Notificar sobre login em novo dispositivo'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Segurança'
        verbose_name_plural = 'Perfis de Segurança'
        db_table = 'usuarios_perfil_seguranca'
    
    def __str__(self):
        return f'Segurança - {self.usuario.email}'
    
    def adicionar_senha_historico(self, senha_hash):
        """Adiciona uma senha ao histórico (máximo 5)"""
        if len(self.historico_senhas) >= 5:
            self.historico_senhas.pop(0)
        self.historico_senhas.append(senha_hash)
        self.ultima_mudanca_senha = timezone.now()
        self.save()
    
    def senha_ja_utilizada(self, senha_hash):
        """Verifica se a senha já foi utilizada recentemente"""
        return senha_hash in self.historico_senhas


class LogAtividade(models.Model):
    """
    Modelo para registrar atividades dos usuários no sistema
    
    Mantém um log detalhado de ações para auditoria e segurança
    """
    
    TIPO_ATIVIDADE_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Tentativa de Login Falhada'),
        ('password_change', 'Mudança de Senha'),
        ('profile_update', 'Atualização de Perfil'),
        ('consulta_create', 'Nova Consulta'),
        ('consulta_view', 'Visualização de Consulta'),
        ('relatorio_generate', 'Geração de Relatório'),
        ('admin_action', 'Ação Administrativa'),
        ('data_export', 'Exportação de Dados'),
        ('account_lock', 'Conta Bloqueada'),
        ('account_unlock', 'Conta Desbloqueada'),
    ]
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='atividades'
    )
    
    tipo_atividade = models.CharField(
        max_length=20,
        choices=TIPO_ATIVIDADE_CHOICES
    )
    
    descricao = models.TextField(
        help_text='Descrição detalhada da atividade'
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text='Informações do navegador/dispositivo'
    )
    
    dados_extras = models.JSONField(
        default=dict,
        help_text='Dados adicionais sobre a atividade'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Atividade'
        verbose_name_plural = 'Logs de Atividade'
        db_table = 'usuarios_log_atividade'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usuario', '-timestamp']),
            models.Index(fields=['tipo_atividade', '-timestamp']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f'{self.usuario.email} - {self.get_tipo_atividade_display()} - {self.timestamp}'
    
    @classmethod
    def registrar_atividade(cls, usuario, tipo_atividade, descricao, 
                           ip_address=None, user_agent=None, dados_extras=None):
        """
        Método de conveniência para registrar uma nova atividade
        
        Args:
            usuario: Instância do usuário
            tipo_atividade: Tipo da atividade (deve estar em TIPO_ATIVIDADE_CHOICES)
            descricao: Descrição da atividade
            ip_address: IP do usuário (opcional)
            user_agent: User agent do navegador (opcional)
            dados_extras: Dados extras em formato dict (opcional)
        
        Returns:
            LogAtividade: Instância criada
        """
        return cls.objects.create(
            usuario=usuario,
            tipo_atividade=tipo_atividade,
            descricao=descricao,
            ip_address=ip_address,
            user_agent=user_agent,
            dados_extras=dados_extras or {}
        )


