# usuarios/managers.py
"""
Managers personalizados para o modelo de Usuário

Este módulo implementa managers customizados para gerenciar diferentes tipos
de usuários no sistema médico IA da Guiné-Bissau.

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para o modelo Usuario
    
    Gerencia a criação de usuários normais e superusuários,
    implementando validações específicas do sistema médico.
    """
    
    def _create_user(self, email, password=None, **extra_fields):
        """
        Método base para criar usuários
        
        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
            **extra_fields: Campos adicionais
            
        Returns:
            Usuario: Instância do usuário criado
            
        Raises:
            ValueError: Se email não for fornecido
        """
        if not email:
            raise ValueError('O email é obrigatório')
        
        # Normalizar email
        email = self.normalize_email(email)
        
        # Validar formato do email
        if '@' not in email:
            raise ValueError('Formato de email inválido')
        
        # Criar usuário
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            # Se não há senha, definir uma senha temporária
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Cria um usuário normal
        
        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
            **extra_fields: Campos adicionais
            
        Returns:
            Usuario: Instância do usuário criado
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_admin', False)
        
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Cria um superusuário (administrador do sistema)
        
        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
            **extra_fields: Campos adicionais
            
        Returns:
            Usuario: Instância do superusuário criado
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser deve ter is_admin=True.')
        
        return self._create_user(email, password, **extra_fields)
    
    def create_paciente(self, email, password=None, **extra_fields):
        """
        Cria um usuário do tipo paciente
        
        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
            **extra_fields: Campos adicionais
            
        Returns:
            Usuario: Instância do usuário paciente criado
        """
        extra_fields.setdefault('is_paciente', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_admin', False)
        
        return self._create_user(email, password, **extra_fields)
    
    def create_moderador(self, email, password=None, **extra_fields):
        """
        Cria um usuário do tipo moderador
        
        Args:
            email (str): Email do usuário
            password (str): Senha do usuário
            **extra_fields: Campos adicionais
            
        Returns:
            Usuario: Instância do usuário moderador criado
        """
        extra_fields.setdefault('is_moderador', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_admin', False)
        
        return self._create_user(email, password, **extra_fields)
    
    # QuerySets personalizados
    def get_queryset(self):
        """Queryset base com otimizações"""
        return super().get_queryset().select_related('perfil_seguranca')
    
    def ativos(self):
        """Retorna apenas usuários ativos"""
        return self.get_queryset().filter(is_active=True)
    
    def inativos(self):
        """Retorna apenas usuários inativos"""
        return self.get_queryset().filter(is_active=False)
    
    def administradores(self):
        """Retorna apenas administradores"""
        return self.get_queryset().filter(is_admin=True, is_active=True)
    
    def pacientes(self):
        """Retorna apenas pacientes"""
        return self.get_queryset().filter(is_paciente=True, is_active=True)
    
    def moderadores(self):
        """Retorna apenas moderadores"""
        return self.get_queryset().filter(is_moderador=True, is_active=True)
    
    def contas_bloqueadas(self):
        """Retorna usuários com contas bloqueadas"""
        agora = timezone.now()
        return self.get_queryset().filter(
            conta_bloqueada_ate__gt=agora
        )
    
    def usuarios_por_idioma(self, idioma):
        """
        Retorna usuários que preferem um idioma específico
        
        Args:
            idioma (str): Código do idioma ('pt', 'gcr', 'fr')
            
        Returns:
            QuerySet: Usuários que preferem o idioma
        """
        return self.get_queryset().filter(idioma_preferido=idioma)
    
    def usuarios_criados_periodo(self, data_inicio, data_fim):
        """
        Retorna usuários criados em um período específico
        
        Args:
            data_inicio (datetime): Data de início
            data_fim (datetime): Data de fim
            
        Returns:
            QuerySet: Usuários criados no período
        """
        return self.get_queryset().filter(
            created_at__gte=data_inicio,
            created_at__lte=data_fim
        )
    
    def usuarios_com_tentativas_login_falhadas(self, min_tentativas=3):
        """
        Retorna usuários com muitas tentativas de login falhadas
        
        Args:
            min_tentativas (int): Número mínimo de tentativas
            
        Returns:
            QuerySet: Usuários com tentativas falhadas
        """
        return self.get_queryset().filter(
            tentativas_login__gte=min_tentativas
        )
    
    def usuarios_sem_login_recente(self, dias=30):
        """
        Retorna usuários que não fizeram login recentemente
        
        Args:
            dias (int): Número de dias
            
        Returns:
            QuerySet: Usuários sem login recente
        """
        data_limite = timezone.now() - timezone.timedelta(days=dias)
        return self.get_queryset().filter(
            models.Q(last_login__lt=data_limite) | 
            models.Q(last_login__isnull=True)
        )


class UsuarioAtivoManager(models.Manager):
    """
    Manager que retorna apenas usuários ativos
    
    Útil para consultas que sempre precisam de usuários ativos
    """
    
    def get_queryset(self):
        """Queryset filtrado apenas para usuários ativos"""
        return super().get_queryset().filter(is_active=True)


class PacienteManager(models.Manager):
    """
    Manager específico para usuários do tipo paciente
    
    Inclui métodos específicos para gerenciar pacientes
    """
    
    def get_queryset(self):
        """Queryset filtrado para pacientes ativos"""
        return super().get_queryset().filter(
            is_paciente=True, 
            is_active=True
        ).select_related('perfil_seguranca')
    
    def com_consultas_recentes(self, dias=30):
        """
        Retorna pacientes com consultas recentes
        
        Args:
            dias (int): Número de dias para considerar "recente"
            
        Returns:
            QuerySet: Pacientes com consultas recentes
        """
        data_limite = timezone.now() - timezone.timedelta(days=dias)
        return self.get_queryset().filter(
            consultas__created_at__gte=data_limite
        ).distinct()
    
    def sem_consultas(self):
        """Retorna pacientes que nunca fizeram consultas"""
        return self.get_queryset().filter(consultas__isnull=True)
    
    def por_regiao(self, regiao):
        """
        Retorna pacientes de uma região específica
        
        Args:
            regiao (str): Nome da região
            
        Returns:
            QuerySet: Pacientes da região
        """
        return self.get_queryset().filter(
            paciente__regiao__nome=regiao
        )
    
    def por_faixa_etaria(self, idade_min, idade_max):
        """
        Retorna pacientes em uma faixa etária específica
        
        Args:
            idade_min (int): Idade mínima
            idade_max (int): Idade máxima
            
        Returns:
            QuerySet: Pacientes na faixa etária
        """
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        hoje = date.today()
        data_nascimento_max = hoje - relativedelta(years=idade_min)
        data_nascimento_min = hoje - relativedelta(years=idade_max + 1)
        
        return self.get_queryset().filter(
            paciente__data_nascimento__gte=data_nascimento_min,
            paciente__data_nascimento__lte=data_nascimento_max
        )
    
    def com_condicoes_cronicas(self):
        """Retorna pacientes com condições crônicas registradas"""
        return self.get_queryset().exclude(
            paciente__condicoes_cronicas__isnull=True
        ).exclude(
            paciente__condicoes_cronicas__exact=[]
        )
    
    def necessitam_followup(self):
        """
        Retorna pacientes que necessitam de follow-up
        
        Baseado em consultas recentes com recomendações de retorno
        """
        return self.get_queryset().filter(
            consultas__recomendacoes__icontains='retorno',
            consultas__created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).distinct()


class ModeradorManager(models.Manager):
    """
    Manager específico para usuários do tipo moderador
    """
    
    def get_queryset(self):
        """Queryset filtrado para moderadores ativos"""
        return super().get_queryset().filter(
            is_moderador=True, 
            is_active=True
        )
    
    def com_atividade_recente(self, dias=7):
        """
        Retorna moderadores com atividade recente
        
        Args:
            dias (int): Número de dias para considerar "recente"
            
        Returns:
            QuerySet: Moderadores com atividade recente
        """
        data_limite = timezone.now() - timezone.timedelta(days=dias)
        return self.get_queryset().filter(
            atividades__timestamp__gte=data_limite,
            atividades__tipo_atividade__in=[
                'admin_action', 'consulta_view', 'relatorio_generate'
            ]
        ).distinct()


class AdminManager(models.Manager):
    """
    Manager específico para usuários administradores
    """
    
    def get_queryset(self):
        """Queryset filtrado para administradores ativos"""
        return super().get_queryset().filter(
            is_admin=True, 
            is_active=True
        )
    
    def superusuarios(self):
        """Retorna apenas superusuários"""
        return self.get_queryset().filter(is_superuser=True)
    
    def administradores_sistema(self):
        """Retorna administradores que não são superusuários"""
        return self.get_queryset().filter(is_superuser=False)