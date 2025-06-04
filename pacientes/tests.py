# paciente/serializers.py
"""
Serializers para o cadastro e gerenciamento de pacientes

Este módulo implementa serializers para criar e gerenciar pacientes,
combinando dados de usuário e informações específicas do paciente.

Autor: Sistema Médico IA Guiné-Bissau
Data: 2025
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from datetime import date
from decimal import Decimal

from .models import Paciente, HistoricoFamiliar, DoencaFamiliar
from geografia.models import Regiao, Cidade, Tabanca
from usuarios.models import PerfilSeguranca

User = get_user_model()


class PacienteCadastroSerializer(serializers.ModelSerializer):
    """
    Serializer para cadastro completo de paciente
    
    Combina dados de usuário e paciente em uma única transação
    """
    
    # Campos do usuário
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    telefone = serializers.CharField(required=False, allow_blank=True)
    idioma_preferido = serializers.ChoiceField(
        choices=User.IDIOMA_CHOICES, 
        default='pt'
    )
    
    # Campos específicos de retorno
    numero_utente = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    idade = serializers.IntegerField(read_only=True)
    
    # Campos de localização (IDs dos objetos relacionados)
    regiao_id = serializers.IntegerField(required=True)
    cidade_id = serializers.IntegerField(required=True)
    tabanca_bairro_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Paciente
        fields = [
            # Campos do usuário
            'email', 'password', 'password_confirm', 'telefone', 'idioma_preferido',
            
            # Dados básicos do paciente
            'nome_completo', 'data_nascimento', 'genero', 'estado_civil',
            
            # Localização
            'regiao_id', 'cidade_id', 'tabanca_bairro_id', 'endereco_completo',
            
            # Dados socioeconômicos básicos
            'profissao', 'nivel_escolaridade', 'renda_familiar_mensal', 
            'numero_pessoas_casa', 'tipo_habitacao',
            
            # Acesso a serviços básicos
            'tem_agua_potavel', 'tem_saneamento_basico', 'tem_energia_eletrica',
            'meio_transporte_principal', 'tempo_deslocamento_hospital',
            
            # Contatos
            'telefone_principal', 'telefone_emergencia', 
            'contato_emergencia_nome', 'contato_emergencia_parentesco',
            
            # Campos de retorno
            'numero_utente', 'user_id', 'idade',
        ]
        extra_kwargs = {
            'nome_completo': {'required': True},
            'data_nascimento': {'required': True},
            'genero': {'required': True},
            'endereco_completo': {'required': True},
            'nivel_escolaridade': {'required': True},
            'renda_familiar_mensal': {'required': True},
            'tipo_habitacao': {'required': True},
        }
    
    def validate_email(self, value):
        """Valida se email já não está em uso"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Este email já está cadastrado no sistema."
            )
        return value
    
    def validate_password(self, value):
        """Valida a senha usando validadores do Django"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validações gerais"""
        # Verificar se senhas coincidem
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'As senhas não coincidem.'
            })
        
        # Validar data de nascimento
        data_nascimento = attrs['data_nascimento']
        hoje = date.today()
        
        if data_nascimento > hoje:
            raise serializers.ValidationError({
                'data_nascimento': 'Data de nascimento não pode ser no futuro.'
            })
        
        # Calcular idade
        idade = hoje.year - data_nascimento.year - (
            (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
        )
        
        if idade < 0 or idade > 150:
            raise serializers.ValidationError({
                'data_nascimento': 'Idade deve estar entre 0 e 150 anos.'
            })
        
        # Validar localização
        try:
            regiao = Regiao.objects.get(id=attrs['regiao_id'])
            cidade = Cidade.objects.get(id=attrs['cidade_id'])
            
            # Verificar se cidade pertence à região
            if cidade.regiao != regiao:
                raise serializers.ValidationError({
                    'cidade_id': 'A cidade selecionada não pertence à região informada.'
                })
            
            # Validar tabanca se fornecida
            if attrs.get('tabanca_bairro_id'):
                tabanca = Tabanca.objects.get(id=attrs['tabanca_bairro_id'])
                if tabanca.cidade != cidade:
                    raise serializers.ValidationError({
                        'tabanca_bairro_id': 'A tabanca selecionada não pertence à cidade informada.'
                    })
        
        except Regiao.DoesNotExist:
            raise serializers.ValidationError({
                'regiao_id': 'Região não encontrada.'
            })
        except Cidade.DoesNotExist:
            raise serializers.ValidationError({
                'cidade_id': 'Cidade não encontrada.'
            })
        except Tabanca.DoesNotExist:
            raise serializers.ValidationError({
                'tabanca_bairro_id': 'Tabanca não encontrada.'
            })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Cria usuário e paciente em uma transação atômica"""
        
        # Extrair dados do usuário
        user_data = {
            'email': validated_data.pop('email'),
            'telefone': validated_data.pop('telefone', ''),
            'idioma_preferido': validated_data.pop('idioma_preferido', 'pt'),
        }
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')  # Remover confirmação
        
        # Extrair IDs de localização
        regiao_id = validated_data.pop('regiao_id')
        cidade_id = validated_data.pop('cidade_id')
        tabanca_bairro_id = validated_data.pop('tabanca_bairro_id', None)
        
        # Criar usuário
        user = User.objects.create_paciente(
            password=password,
            **user_data
        )
        
        # Buscar objetos de localização
        regiao = Regiao.objects.get(id=regiao_id)
        cidade = Cidade.objects.get(id=cidade_id)
        tabanca_bairro = None
        if tabanca_bairro_id:
            tabanca_bairro = Tabanca.objects.get(id=tabanca_bairro_id)
        
        # Criar paciente
        paciente = Paciente.objects.create(
            user=user,
            regiao=regiao,
            cidade=cidade,
            tabanca_bairro=tabanca_bairro,
            **validated_data
        )
        
        # Criar perfil de segurança
        PerfilSeguranca.objects.create(usuario=user)
        
        return paciente
    
    def to_representation(self, instance):
        """Customiza a representação de saída"""
        data = super().to_representation(instance)
        data['user_id'] = instance.user.id
        data['email'] = instance.user.email
        data['telefone_usuario'] = instance.user.telefone
        data['idioma_preferido'] = instance.user.idioma_preferido
        data['regiao_nome'] = instance.regiao.get_nome_display() if instance.regiao else None
        data['cidade_nome'] = instance.cidade.nome if instance.cidade else None
        data['tabanca_nome'] = instance.tabanca_bairro.nome if instance.tabanca_bairro else None
        return data


class PacientePerfilCompletoSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização completa do perfil do paciente
    
    Permite atualizar todos os dados do paciente após o cadastro inicial
    """
    
    # Dados antropométricos
    peso = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        required=False,
        min_value=Decimal('0.5'),
        max_value=Decimal('300.0')
    )
    altura = serializers.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        required=False,
        min_value=Decimal('0.30'),
        max_value=Decimal('2.50')
    )
    
    # Campos calculados
    imc = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)
    classificacao_imc = serializers.CharField(read_only=True)
    classificacao_pressao = serializers.CharField(read_only=True)
    idade = serializers.IntegerField(read_only=True)
    porcentagem_preenchimento = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Paciente
        exclude = ['user', 'numero_utente', 'created_at', 'updated_at']
        extra_kwargs = {
            'perfil_completo': {'read_only': True},
            'ultima_atualizacao_dados': {'read_only': True},
        }
    
    def validate_data_nascimento(self, value):
        """Não permitir alteração da data de nascimento"""
        if self.instance and self.instance.data_nascimento != value:
            raise serializers.ValidationError(
                "Data de nascimento não pode ser alterada após o cadastro."
            )
        return value
    
    def validate(self, attrs):
        """Validações específicas do perfil completo"""
        
        # Validar pressão arterial
        sistolica = attrs.get('pressao_arterial_sistolica')
        diastolica = attrs.get('pressao_arterial_diastolica')
        
        if sistolica and diastolica:
            if sistolica <= diastolica:
                raise serializers.ValidationError({
                    'pressao_arterial_sistolica': 'Pressão sistólica deve ser maior que diastólica.'
                })
            
            if sistolica < 70 or sistolica > 250:
                raise serializers.ValidationError({
                    'pressao_arterial_sistolica': 'Pressão sistólica deve estar entre 70 e 250 mmHg.'
                })
            
            if diastolica < 40 or diastolica > 150:
                raise serializers.ValidationError({
                    'pressao_arterial_diastolica': 'Pressão diastólica deve estar entre 40 e 150 mmHg.'
                })
        
        # Validar dados de fumante
        if attrs.get('fuma') and not attrs.get('cigarros_por_dia'):
            raise serializers.ValidationError({
                'cigarros_por_dia': 'Informe quantos cigarros por dia se o paciente fuma.'
            })
        
        # Validar dados femininos
        if attrs.get('genero') == 'F':
            menarca_idade = attrs.get('menarca_idade')
            if menarca_idade and (menarca_idade < 8 or menarca_idade > 18):
                raise serializers.ValidationError({
                    'menarca_idade': 'Idade da menarca deve estar entre 8 e 18 anos.'
                })
        
        return attrs


class HistoricoFamiliarSerializer(serializers.ModelSerializer):
    """
    Serializer para histórico familiar do paciente
    """
    
    class Meta:
        model = HistoricoFamiliar
        exclude = ['paciente', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validações do histórico familiar"""
        
        # Validar idade de morte dos pais
        if attrs.get('pai_idade_morte'):
            if attrs['pai_idade_morte'] < 0 or attrs['pai_idade_morte'] > 150:
                raise serializers.ValidationError({
                    'pai_idade_morte': 'Idade deve estar entre 0 e 150 anos.'
                })
        
        if attrs.get('mae_idade_morte'):
            if attrs['mae_idade_morte'] < 0 or attrs['mae_idade_morte'] > 150:
                raise serializers.ValidationError({
                    'mae_idade_morte': 'Idade deve estar entre 0 e 150 anos.'
                })
        
        return attrs


class DoencaFamiliarSerializer(serializers.ModelSerializer):
    """
    Serializer para doenças específicas na família
    """
    
    class Meta:
        model = DoencaFamiliar
        exclude = ['paciente']
    
    def validate_doenca(self, value):
        """Validar nome da doença"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Nome da doença deve ter pelo menos 3 caracteres."
            )
        return value.strip().title()


class PacienteResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagem de pacientes
    """
    
    email = serializers.CharField(source='user.email', read_only=True)
    telefone_usuario = serializers.CharField(source='user.telefone', read_only=True)
    idade = serializers.IntegerField(read_only=True)
    regiao_nome = serializers.CharField(source='regiao.get_nome_display', read_only=True)
    cidade_nome = serializers.CharField(source='cidade.nome', read_only=True)
    endereco_formatado = serializers.CharField(source='get_endereco_completo_formatado', read_only=True)
    
    class Meta:
        model = Paciente
        fields = [
            'id', 'numero_utente', 'nome_completo', 'email', 'telefone_usuario',
            'data_nascimento', 'idade', 'genero', 'regiao_nome', 'cidade_nome',
            'endereco_formatado', 'perfil_completo', 'porcentagem_preenchimento',
            'created_at'
        ]


class PacienteCompletoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para visualização detalhada do paciente
    """
    
    # Dados do usuário
    email = serializers.CharField(source='user.email', read_only=True)
    telefone_usuario = serializers.CharField(source='user.telefone', read_only=True)
    idioma_preferido = serializers.CharField(source='user.get_idioma_preferido_display', read_only=True)
    ultimo_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    
    # Dados calculados
    idade = serializers.IntegerField(read_only=True)
    classificacao_imc = serializers.CharField(read_only=True)
    classificacao_pressao = serializers.CharField(read_only=True)
    
    # Localização
    regiao_nome = serializers.CharField(source='regiao.get_nome_display', read_only=True)
    cidade_nome = serializers.CharField(source='cidade.nome', read_only=True)
    tabanca_nome = serializers.CharField(source='tabanca_bairro.nome', read_only=True)
    endereco_formatado = serializers.CharField(source='get_endereco_completo_formatado', read_only=True)
    
    # Histórico familiar
    historico_familiar = HistoricoFamiliarSerializer(read_only=True)
    doencas_familiares = DoencaFamiliarSerializer(many=True, read_only=True)
    
    class Meta:
        model = Paciente
        fields = '__all__'