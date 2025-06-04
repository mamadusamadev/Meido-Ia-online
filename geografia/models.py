# geografia/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Regiao(models.Model):
    """
    Modelo para as regiões administrativas da Guiné-Bissau
    """
    REGIOES_CHOICES = [
        ('bissau', 'Bissau'),
        ('bafata', 'Bafatá'),
        ('biombo', 'Biombo'),
        ('bolama', 'Bolama/Bijagós'),
        ('cacheu', 'Cacheu'),
        ('gabu', 'Gabú'),
        ('oio', 'Oio'),
        ('quinara', 'Quinara'),
        ('tombali', 'Tombali'),
    ]
    
    CLIMA_CHOICES = [
        ('tropical_humido', 'Tropical Húmido'),
        ('tropical_seco', 'Tropical Seco'),
        ('savana', 'Savana'),
        ('costeiro', 'Costeiro'),
    ]
    
    nome = models.CharField(max_length=50, choices=REGIOES_CHOICES, unique=True)
    codigo_regiao = models.CharField(max_length=10, unique=True)
    populacao_estimada = models.PositiveIntegerField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    caracteristicas_climaticas = models.CharField(max_length=30, choices=CLIMA_CHOICES)
    area_km2 = models.PositiveIntegerField(help_text="Área em quilômetros quadrados")
    densidade_populacional = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Infraestrutura de saúde
    hospitais_regionais = models.PositiveIntegerField(default=0)
    centros_saude = models.PositiveIntegerField(default=0)
    postos_saude = models.PositiveIntegerField(default=0)
    medicos_por_1000hab = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Região"
        verbose_name_plural = "Regiões"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.get_nome_display()} ({self.codigo_regiao})"
    
    def save(self, *args, **kwargs):
        if self.populacao_estimada and self.area_km2:
            self.densidade_populacional = Decimal(self.populacao_estimada) / Decimal(self.area_km2)
        super().save(*args, **kwargs)


class Cidade(models.Model):
    """
    Modelo para cidades/sectores das regiões
    """
    TIPO_CHOICES = [
        ('urbana', 'Urbana'),
        ('rural', 'Rural'),
        ('semi_urbana', 'Semi-urbana'),
    ]
    
    regiao = models.ForeignKey(Regiao, on_delete=models.CASCADE, related_name='cidades')
    nome = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20, null=True, blank=True)
    populacao = models.PositiveIntegerField()
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    distancia_hospital_km = models.PositiveIntegerField(
        help_text="Distância ao hospital mais próximo em km"
    )
    
    # Coordenadas GPS
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Infraestrutura básica
    tem_centro_saude = models.BooleanField(default=False)
    tem_posto_saude = models.BooleanField(default=False)
    tem_farmacia = models.BooleanField(default=False)
    tem_ambulancia = models.BooleanField(default=False)
    
    # Acesso e comunicação
    tem_estrada_asfaltada = models.BooleanField(default=False)
    tem_internet = models.BooleanField(default=False)
    tem_rede_movel = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cidade/Sector"
        verbose_name_plural = "Cidades/Sectores"
        ordering = ['regiao', 'nome']
        unique_together = ['regiao', 'nome']
    
    def __str__(self):
        return f"{self.nome} ({self.regiao.get_nome_display()})"


class Tabanca(models.Model):
    """
    Modelo para tabancas/bairros (menor divisão administrativa)
    """
    INFRAESTRUTURA_CHOICES = [
        ('nenhuma', 'Nenhuma'),
        ('basica', 'Básica'),
        ('completa', 'Completa'),
    ]
    
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE, related_name='tabancas')
    nome = models.CharField(max_length=100)
    
    # Localização
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Infraestrutura de saúde
    infraestrutura_saude = models.CharField(max_length=15, choices=INFRAESTRUTURA_CHOICES)
    tem_agente_saude_comunitario = models.BooleanField(default=False)
    
    # Serviços básicos
    acesso_agua_potavel = models.BooleanField(default=False)
    fonte_agua_principal = models.CharField(max_length=50, null=True, blank=True)
    acesso_eletricidade = models.BooleanField(default=False)
    tem_saneamento_basico = models.BooleanField(default=False)
    
    # Demografia
    populacao_estimada = models.PositiveIntegerField(null=True, blank=True)
    numero_familias = models.PositiveIntegerField(null=True, blank=True)
    
    # Características específicas
    principal_atividade_economica = models.CharField(max_length=100, null=True, blank=True)
    grupo_etnico_predominante = models.CharField(max_length=50, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tabanca/Bairro"
        verbose_name_plural = "Tabancas/Bairros"
        ordering = ['cidade', 'nome']
        unique_together = ['cidade', 'nome']
    
    def __str__(self):
        return f"{self.nome} ({self.cidade.nome})"


class IndicadorSaude(models.Model):
    """
    Modelo para armazenar indicadores de saúde por localização
    """
    # Relacionamentos geográficos
    regiao = models.ForeignKey(Regiao, on_delete=models.CASCADE, null=True, blank=True)
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE, null=True, blank=True)
    tabanca = models.ForeignKey(Tabanca, on_delete=models.CASCADE, null=True, blank=True)
    
    # Período de referência
    ano = models.PositiveIntegerField()
    mes = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    # Indicadores demográficos
    nascimentos = models.PositiveIntegerField(default=0)
    obitos = models.PositiveIntegerField(default=0)
    taxa_natalidade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    taxa_mortalidade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Indicadores de morbidade
    casos_malaria = models.PositiveIntegerField(default=0)
    casos_dengue = models.PositiveIntegerField(default=0)
    casos_tuberculose = models.PositiveIntegerField(default=0)
    casos_diabetes = models.PositiveIntegerField(default=0)
    casos_hipertensao = models.PositiveIntegerField(default=0)
    casos_desnutricao = models.PositiveIntegerField(default=0)
    
    # Indicadores de vacinação
    cobertura_vacinal_infantil = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Metadados
    fonte_dados = models.CharField(max_length=100, default='Sistema Médico-IA')
    observacoes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Indicador de Saúde"
        verbose_name_plural = "Indicadores de Saúde"
        ordering = ['-ano', '-mes', 'regiao']
        unique_together = ['regiao', 'cidade', 'tabanca', 'ano', 'mes']
    
    def __str__(self):
        location = self.tabanca or self.cidade or self.regiao
        return f"Indicadores {location} - {self.mes}/{self.ano}"