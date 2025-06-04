# usuarios/serializers.py
"""
Serializers para API REST do módulo de usuários

Este módulo implementa serializers para diferentes operações:
- Criação e autenticação de usuários
- Perfis de segurança
- Logs de atividade
- Operações específicas por tipo de usuário

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Usuario, PerfilSeguranca, LogAtividade


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer básico para o modelo Usuario
    
    Usado para listagem e visualização de dados do usuário
    """
    
    nome_completo = serializers.CharField(source='get_full_name', read_only=True)
    nome_curto = serializers.CharField(source='get_short_name', read_only=True)
    tipo_usuario = serializers.CharField(source='get_tipo_usuario', read_only=True)
    conta_bloqueada = serializers.BooleanField(source='conta_esta_bloqueada', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'telefone',
            'nome_completo',
            'nome_curto',
            'tipo_usuario',
            'is_active',
            'is_admin',
            'is_paciente',
            'is_moderador',
            'idioma_preferido',
            'timezone_usuario',
            'receber_email_notificacoes',
            'receber_sms_notificacoes',
            'last_login',
            'created_at',
            'updated_at',
            'conta_bloqueada'
        ]
        read_only_fields = [
            'id',
            'is_admin',
            'is_paciente',
            'is_moderador',
            'last_login',
            'created_at',
            'updated_at'
        ]


class UsuarioCriacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novos usuários
    
    Inclui validação de senha e campos obrigatórios
    """
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Senha deve ter no mínimo 8 caracteres'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text='Confirmação da senha'
    )
    
    class Meta:
        model = Usuario
        fields = [
            'email',
            'telefone',
            'password',
            'password_confirm',
            'idioma_preferido',
            'timezone_usuario',
            'receber_email_notificacoes',
            'receber_sms_notificacoes'
        ]
    
    def validate_email(self, value):
        """Valida se o email já não está em uso"""
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Este email já está sendo usado por outro usuário.'
            )
        return value
    
    def validate_password(self, value):
        """Valida a senha usando os validadores do Django"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Valida se as senhas coincidem"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'As senhas não coincidem.'
            })
        return attrs
    
    def create(self, validated_data):
        """Cria um novo usuário"""
        # Remove password_confirm dos dados
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Define como paciente por padrão
        validated_data['is_paciente'] = True
        
        # Cria o usuário
        usuario = Usuario.objects.create_user(
            password=password,
            **validated_data
        )
        
        return usuario


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização do perfil do usuário
    
    Permite ao usuário atualizar suas próprias informações
    """
    
    class Meta:
        model = Usuario
        fields = [
            'telefone',
            'idioma_preferido',
            'timezone_usuario',
            'receber_email_notificacoes',
            'receber_sms_notificacoes'
        ]
    
    def update(self, instance, validated_data):
        """Atualiza o perfil do usuário"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Registra a atividade
        LogAtividade.registrar_atividade(
            usuario=instance,
            tipo_atividade='profile_update',
            descricao='Perfil atualizado pelo usuário'
        )
        
        return instance


class MudancaSenhaSerializer(serializers.Serializer):
    """
    Serializer para mudança de senha
    """
    
    senha_atual = serializers.CharField(write_only=True)
    nova_senha = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Nova senha deve ter no mínimo 8 caracteres'
    )
    nova_senha_confirm = serializers.CharField(
        write_only=True,
        help_text='Confirmação da nova senha'
    )
    
    def validate_nova_senha(self, value):
        """Valida a nova senha"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Valida se as novas senhas coincidem"""
        if attrs['nova_senha'] != attrs['nova_senha_confirm']:
            raise serializers.ValidationError({
                'nova_senha_confirm': 'As senhas não coincidem.'
            })
        return attrs
    
    def validate_senha_atual(self, value):
        """Valida se a senha atual está correta"""
        usuario = self.context['request'].user
        if not usuario.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value
    
    def save(self):
        """Atualiza a senha do usuário"""
        usuario = self.context['request'].user
        nova_senha = self.validated_data['nova_senha']
        
        # Atualiza a senha
        usuario.set_password(nova_senha)
        usuario.save()
        
        # Atualiza o perfil de segurança
        if hasattr(usuario, 'perfil_seguranca'):
            from django.contrib.auth.hashers import make_password
            usuario.perfil_seguranca.adicionar_senha_historico(
                make_password(nova_senha)
            )
        
        # Registra a atividade
        LogAtividade.registrar_atividade(
            usuario=usuario,
            tipo_atividade='password_change',
            descricao='Senha alterada pelo usuário'
        )
        
        return usuario


class PerfilSegurancaSerializer(serializers.ModelSerializer):
    """
    Serializer para configurações de segurança
    """
    
    class Meta:
        model = PerfilSeguranca
        fields = [
            'two_factor_enabled',
            'max_sessoes_simultaneas',
            'permitir_login_multiplos_dispositivos',
            'notificar_login_novo_dispositivo',
            'ultima_mudanca_senha'
        ]
        read_only_fields = ['ultima_mudanca_senha' ]
    
    def update(self, instance, validated_data):
        """Atualiza configurações de segurança"""
        usuario = instance.usuario
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Registra a atividade
        LogAtividade.registrar_atividade(
            usuario=usuario,
            tipo_atividade='profile_update',
            descricao='Configurações de segurança atualizadas',
            dados_extras=validated_data
        )
        
        return instance


class LogAtividadeSerializer(serializers.ModelSerializer):
    """
    Serializer para logs de atividade (somente leitura)
    """
    
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    tipo_atividade_display = serializers.CharField(
        source='get_tipo_atividade_display',
        read_only=True
    )
    
    class Meta:
        model = LogAtividade
        fields = [
            'id',
            'usuario_email',
            'tipo_atividade',
            'tipo_atividade_display',
            'descricao',
            'ip_address',
            'timestamp'
        ]
        read_only_fields = [
            'id',
            'usuario_email',
            'tipo_atividade_display',
            'timestamp',
            'descricao',
            'ip_address'
        ]


class TokenPersonalizadoSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para JWT Token
    
    Adiciona informações extras ao token e registra atividade de login
    """
    
    def validate(self, attrs):
        """Valida credenciais e adiciona informações extras"""
        data = super().validate(attrs)
        
        # Verifica se a conta está bloqueada
        if self.user.conta_esta_bloqueada():
            raise serializers.ValidationError(
                'Conta temporariamente bloqueada devido a múltiplas tentativas de login.'
            )
        
        # Adiciona informações extras ao token
        self.get_token(self.user)
        
        # Informações do usuário
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'nome_completo': self.user.get_full_name(),
            'tipo_usuario': self.user.get_tipo_usuario(),
            'idioma_preferido': self.user.idioma_preferido,
            'is_admin': self.user.is_admin,
            'is_paciente': self.user.is_paciente,
            'is_moderador': self.user.is_moderador
        }
        
        # Registra o login bem-sucedido
        request = self.context.get('request')
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Atualiza informações de login
        self.user.atualizar_ultimo_login(ip_address)
        
        # Registra atividade
        LogAtividade.registrar_atividade(
            usuario=self.user,
            tipo_atividade='login',
            descricao='Login realizado com sucesso',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return data
    
    def get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @classmethod
    def get_token(cls, user):
        """Personaliza o token JWT"""
        token = super().get_token(user)
        
        # Adiciona claims personalizados
        token['email'] = user.email
        token['tipo_usuario'] = user.get_tipo_usuario()
        token['idioma'] = user.idioma_preferido
        
        return token


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """
    Serializer para administradores gerenciarem usuários
    
    Inclui todos os campos e permite modificações administrativas
    """
    
    nome_completo = serializers.CharField(source='get_full_name', read_only=True)
    tipo_usuario = serializers.CharField(source='get_tipo_usuario', read_only=True)
    total_consultas = serializers.SerializerMethodField()
    ultima_atividade = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'telefone',
            'nome_completo',
            'tipo_usuario',
            'is_active',
            'is_staff',
            'is_admin',
            'is_paciente',
            'is_moderador',
            'idioma_preferido',
            'timezone_usuario',
            'receber_email_notificacoes',
            'receber_sms_notificacoes',
            'tentativas_login',
            'conta_bloqueada_ate',
            'ultimo_login_ip',
            'last_login',
            'created_at',
            'updated_at',
            'total_consultas',
            'ultima_atividade'
        ]
        read_only_fields = [
            'id',
            'tentativas_login',
            'ultimo_login_ip',
            'last_login',
            'created_at',
            'updated_at',
            'total_consultas',
            'ultima_atividade'
        ]
    
    def get_total_consultas(self, obj):
        """Retorna o total de consultas do usuário"""
        if hasattr(obj, 'consultas'):
            return obj.consultas.count()
        return 0
    
    def get_ultima_atividade(self, obj):
        """Retorna a data da última atividade do usuário"""
        ultima_atividade = obj.atividades.first()
        if ultima_atividade:
            return ultima_atividade.timestamp
        return obj.last_login


class UsuarioResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagens rápidas
    """
    
    nome_completo = serializers.CharField(source='get_full_name', read_only=True)
    tipo_usuario = serializers.CharField(source='get_tipo_usuario', read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'nome_completo',
            'tipo_usuario',
            'is_active',
            'last_login',
            'created_at'
        ]


class EstatisticasUsuarioSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de usuários
    """
    
    total_usuarios = serializers.IntegerField()
    usuarios_ativos = serializers.IntegerField()
    usuarios_inativos = serializers.IntegerField()
    total_pacientes = serializers.IntegerField()
    total_moderadores = serializers.IntegerField()
    total_administradores = serializers.IntegerField()
    novos_usuarios_mes = serializers.IntegerField()
    usuarios_bloqueados = serializers.IntegerField()
    logins_hoje = serializers.IntegerField()
    usuarios_por_idioma = serializers.DictField()


class RecuperacaoSenhaSerializer(serializers.Serializer):
    """
    Serializer para solicitação de recuperação de senha
    """
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Valida se o email existe no sistema"""
        try:
            usuario = Usuario.objects.get(email=value, is_active=True)
        except usuario.DoesNotExist:
            # Por segurança, não revelamos se o email existe ou não
            pass
        return value


class RedefinirSenhaSerializer(serializers.Serializer):
    """
    Serializer para redefinição de senha via token
    """
    
    token = serializers.CharField()
    nova_senha = serializers.CharField(
        min_length=8,
        help_text='Nova senha deve ter no mínimo 8 caracteres'
    )
    nova_senha_confirm = serializers.CharField(
        help_text='Confirmação da nova senha'
    )
    
    def validate_nova_senha(self, value):
        """Valida a nova senha"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Valida se as senhas coincidem"""
        if attrs['nova_senha'] != attrs['nova_senha_confirm']:
            raise serializers.ValidationError({
                'nova_senha_confirm': 'As senhas não coincidem.'
            })
        return attrs


class UsuarioModeracaoSerializer(serializers.ModelSerializer):
    """
    Serializer para ações de moderação de usuários
    """
    
    motivo_acao = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'is_active',
            'conta_bloqueada_ate',
            'motivo_acao'
        ]
        read_only_fields = ['id', 'email']
    
    def update(self, instance, validated_data):
        """Atualiza usuário com registro de moderação"""
        motivo = validated_data.pop('motivo_acao', '')
        request = self.context.get('request')
        
        # Salva as alterações
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Registra a ação de moderação
        if request and request.user:
            LogAtividade.registrar_atividade(
                usuario=request.user,
                tipo_atividade='admin_action',
                descricao=f'Moderação aplicada ao usuário {instance.email}',
                dados_extras={
                    'usuario_afetado': instance.email,
                    'motivo': motivo,
                    'alteracoes': validated_data
                }
            )
        
        return instance


class UsuarioExportacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para exportação de dados de usuários
    """
    
    nome_completo = serializers.CharField(source='get_full_name', read_only=True)
    tipo_usuario = serializers.CharField(source='get_tipo_usuario', read_only=True)
    total_consultas = serializers.SerializerMethodField()
    total_atividades = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'telefone',
            'nome_completo',
            'tipo_usuario',
            'is_active',
            'idioma_preferido',
            'timezone_usuario',
            'total_consultas',
            'total_atividades',
            'last_login',
            'created_at',
            'updated_at'
        ]
    
    def get_total_consultas(self, obj):
        """Retorna o total de consultas do usuário"""
        if hasattr(obj, 'consultas'):
            return obj.consultas.count()
        return 0
    
    def get_total_atividades(self, obj):
        """Retorna o total de atividades do usuário"""
        return obj.atividades.count()