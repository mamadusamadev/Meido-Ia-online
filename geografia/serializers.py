# geografia/serializers.py
"""
Serializers para API REST do módulo de geografia

Este módulo implementa serializers para diferentes operações:
- CRUD de regiões, cidades e tabancas
- Indicadores de saúde por localização
- Relatórios geográficos e estatísticas
- Validações específicas para dados geográficos

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Regiao, Cidade, Tabanca, IndicadorSaude


class RegiaoSerializer(serializers.ModelSerializer):
    """
    Serializer básico para o modelo Regiao
    
    Usado para listagem e visualização de dados das regiões
    """
    
    nome_display = serializers.CharField(source='get_nome_display', read_only=True)
    total_cidades = serializers.SerializerMethodField()
    total_tabancas = serializers.SerializerMethodField()
    
    class Meta:
        model = Regiao
        fields = [
            'id',
            'nome',
            'nome_display',
            'codigo_regiao',
            'populacao_estimada',
            'latitude',
            'longitude',
            'caracteristicas_climaticas',
            'area_km2',
            'densidade_populacional',
            'hospitais_regionais',
            'centros_saude',
            'postos_saude',
            'medicos_por_1000hab',
            'total_cidades',
            'total_tabancas',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'densidade_populacional',
            'total_cidades',
            'total_tabancas',
            'created_at',
            'updated_at'
        ]
    
    def get_total_cidades(self, obj):
        """Retorna o total de cidades da região"""
        return obj.cidades.count()
    
    def get_total_tabancas(self, obj):
        """Retorna o total de tabancas da região"""
        return sum(cidade.tabancas.count() for cidade in obj.cidades.all())


class RegiaoCriacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novas regiões
    
    Inclui validações específicas para dados geográficos
    """
    
    class Meta:
        model = Regiao
        fields = [
            'nome',
            'codigo_regiao',
            'populacao_estimada',
            'latitude',
            'longitude',
            'caracteristicas_climaticas',
            'area_km2',
            'hospitais_regionais',
            'centros_saude',
            'postos_saude',
            'medicos_por_1000hab'
        ]
    
    def validate_codigo_regiao(self, value):
        """Valida se o código da região é único"""
        if Regiao.objects.filter(codigo_regiao=value).exists():
            raise serializers.ValidationError(
                'Este código de região já está sendo usado.'
            )
        return value.upper()
    
    def validate_latitude(self, value):
        """Valida coordenadas de latitude para Guiné-Bissau"""
        if value and (value < 10.5 or value > 12.7):
            raise serializers.ValidationError(
                'Latitude deve estar entre 10.5° e 12.7° para Guiné-Bissau.'
            )
        return value
    
    def validate_longitude(self, value):
        """Valida coordenadas de longitude para Guiné-Bissau"""
        if value and (value < -16.8 or value > -13.6):
            raise serializers.ValidationError(
                'Longitude deve estar entre -16.8° e -13.6° para Guiné-Bissau.'
            )
        return value
    
    def validate(self, attrs):
        """Validações adicionais"""
        # Valida se população e área fazem sentido
        if attrs.get('populacao_estimada') and attrs.get('area_km2'):
            densidade = Decimal(attrs['populacao_estimada']) / Decimal(attrs['area_km2'])
            if densidade > 10000:  # Densidade muito alta
                raise serializers.ValidationError(
                    'Densidade populacional parece muito alta. Verifique os dados.'
                )
        
        return attrs


class CidadeSerializer(serializers.ModelSerializer):
    """
    Serializer básico para o modelo Cidade
    """
    
    regiao_nome = serializers.CharField(source='regiao.get_nome_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    total_tabancas = serializers.SerializerMethodField()
    
    class Meta:
        model = Cidade
        fields = [
            'id',
            'regiao',
            'regiao_nome',
            'nome',
            'codigo_postal',
            'populacao',
            'tipo',
            'tipo_display',
            'distancia_hospital_km',
            'latitude',
            'longitude',
            'tem_centro_saude',
            'tem_posto_saude',
            'tem_farmacia',
            'tem_ambulancia',
            'tem_estrada_asfaltada',
            'tem_internet',
            'tem_rede_movel',
            'total_tabancas',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'regiao_nome',
            'tipo_display',
            'total_tabancas',
            'created_at',
            'updated_at'
        ]
    
    def get_total_tabancas(self, obj):
        """Retorna o total de tabancas da cidade"""
        return obj.tabancas.count()


class CidadeCriacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novas cidades
    """
    
    class Meta:
        model = Cidade
        fields = [
            'regiao',
            'nome',
            'codigo_postal',
            'populacao',
            'tipo',
            'distancia_hospital_km',
            'latitude',
            'longitude',
            'tem_centro_saude',
            'tem_posto_saude',
            'tem_farmacia',
            'tem_ambulancia',
            'tem_estrada_asfaltada',
            'tem_internet',
            'tem_rede_movel'
        ]
    
    def validate(self, attrs):
        """Validações específicas para cidades"""
        regiao = attrs.get('regiao')
        nome = attrs.get('nome')
        
        # Verifica se já existe cidade com mesmo nome na região
        if Cidade.objects.filter(regiao=regiao, nome=nome).exists():
            raise serializers.ValidationError(
                'Já existe uma cidade com este nome nesta região.'
            )
        
        # Validações de lógica
        if attrs.get('tem_ambulancia') and not (attrs.get('tem_centro_saude') or attrs.get('tem_posto_saude')):
            raise serializers.ValidationError(
                'Cidade com ambulância deve ter pelo menos um centro ou posto de saúde.'
            )
        
        return attrs


class TabancaSerializer(serializers.ModelSerializer):
    """
    Serializer básico para o modelo Tabanca
    """
    
    cidade_nome = serializers.CharField(source='cidade.nome', read_only=True)
    regiao_nome = serializers.CharField(source='cidade.regiao.get_nome_display', read_only=True)
    infraestrutura_display = serializers.CharField(source='get_infraestrutura_saude_display', read_only=True)
    
    class Meta:
        model = Tabanca
        fields = [
            'id',
            'cidade',
            'cidade_nome',
            'regiao_nome',
            'nome',
            'latitude',
            'longitude',
            'infraestrutura_saude',
            'infraestrutura_display',
            'tem_agente_saude_comunitario',
            'acesso_agua_potavel',
            'fonte_agua_principal',
            'acesso_eletricidade',
            'tem_saneamento_basico',
            'populacao_estimada',
            'numero_familias',
            'principal_atividade_economica',
            'grupo_etnico_predominante',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'cidade_nome',
            'regiao_nome',
            'infraestrutura_display',
            'created_at',
            'updated_at'
        ]


class TabancaCriacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novas tabancas
    """
    
    class Meta:
        model = Tabanca
        fields = [
            'cidade',
            'nome',
            'latitude',
            'longitude',
            'infraestrutura_saude',
            'tem_agente_saude_comunitario',
            'acesso_agua_potavel',
            'fonte_agua_principal',
            'acesso_eletricidade',
            'tem_saneamento_basico',
            'populacao_estimada',
            'numero_familias',
            'principal_atividade_economica',
            'grupo_etnico_predominante'
        ]
    
    def validate(self, attrs):
        """Validações específicas para tabancas"""
        cidade = attrs.get('cidade')
        nome = attrs.get('nome')
        
        # Verifica se já existe tabanca com mesmo nome na cidade
        if Tabanca.objects.filter(cidade=cidade, nome=nome).exists():
            raise serializers.ValidationError(
                'Já existe uma tabanca com este nome nesta cidade.'
            )
        
        # Validações de lógica
        populacao = attrs.get('populacao_estimada')
        familias = attrs.get('numero_familias')
        
        if populacao and familias:
            if populacao < familias:
                raise serializers.ValidationError(
                    'Número de famílias não pode ser maior que a população.'
                )
            
            # Média de pessoas por família (entre 3 e 15)
            media_familia = populacao / familias
            if media_familia < 2 or media_familia > 20:
                raise serializers.ValidationError(
                    'Média de pessoas por família parece inconsistente.'
                )
        
        return attrs


class IndicadorSaudeSerializer(serializers.ModelSerializer):
    """
    Serializer para indicadores de saúde
    """
    
    localizacao_nome = serializers.SerializerMethodField()
    nivel_localizacao = serializers.SerializerMethodField()
    
    class Meta:
        model = IndicadorSaude
        fields = [
            'id',
            'regiao',
            'cidade',
            'tabanca',
            'localizacao_nome',
            'nivel_localizacao',
            'ano',
            'mes',
            'nascimentos',
            'obitos',
            'taxa_natalidade',
            'taxa_mortalidade',
            'casos_malaria',
            'casos_dengue',
            'casos_tuberculose',
            'casos_diabetes',
            'casos_hipertensao',
            'casos_desnutricao',
            'cobertura_vacinal_infantil',
            'fonte_dados',
            'observacoes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'localizacao_nome',
            'nivel_localizacao',
            'created_at',
            'updated_at'
        ]
    
    def get_localizacao_nome(self, obj):
        """Retorna o nome da localização"""
        if obj.tabanca:
            return f"{obj.tabanca.nome} ({obj.tabanca.cidade.nome})"
        elif obj.cidade:
            return f"{obj.cidade.nome} ({obj.cidade.regiao.get_nome_display()})"
        elif obj.regiao:
            return obj.regiao.get_nome_display()
        return "Não especificado"
    
    def get_nivel_localizacao(self, obj):
        """Retorna o nível da localização"""
        if obj.tabanca:
            return "Tabanca"
        elif obj.cidade:
            return "Cidade"
        elif obj.regiao:
            return "Região"
        return "Indefinido"


class IndicadorSaudeCriacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de indicadores de saúde
    """
    
    class Meta:
        model = IndicadorSaude
        fields = [
            'regiao',
            'cidade',
            'tabanca',
            'ano',
            'mes',
            'nascimentos',
            'obitos',
            'taxa_natalidade',
            'taxa_mortalidade',
            'casos_malaria',
            'casos_dengue',
            'casos_tuberculose',
            'casos_diabetes',
            'casos_hipertensao',
            'casos_desnutricao',
            'cobertura_vacinal_infantil',
            'fonte_dados',
            'observacoes'
        ]
    
    def validate(self, attrs):
        """Validações específicas para indicadores"""
        # Deve ter pelo menos uma localização definida
        if not any([attrs.get('regiao'), attrs.get('cidade'), attrs.get('tabanca')]):
            raise serializers.ValidationError(
                'Deve ser especificada pelo menos uma localização (região, cidade ou tabanca).'
            )
        
        # Hierarquia de localização
        if attrs.get('tabanca') and not attrs.get('cidade'):
            attrs['cidade'] = attrs['tabanca'].cidade
        
        if attrs.get('cidade') and not attrs.get('regiao'):
            attrs['regiao'] = attrs['cidade'].regiao
        
        # Validações de consistência
        nascimentos = attrs.get('nascimentos', 0)
        obitos = attrs.get('obitos', 0)
        
        if nascimentos < 0 or obitos < 0:
            raise serializers.ValidationError(
                'Nascimentos e óbitos não podem ser negativos.'
            )
        
        # Verifica se já existe indicador para o mesmo período e localização
        if IndicadorSaude.objects.filter(
            regiao=attrs.get('regiao'),
            cidade=attrs.get('cidade'),
            tabanca=attrs.get('tabanca'),
            ano=attrs.get('ano'),
            mes=attrs.get('mes')
        ).exists():
            raise serializers.ValidationError(
                'Já existem indicadores para esta localização e período.'
            )
        
        return attrs


class RegiaoResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagens rápidas de regiões
    """
    
    nome_display = serializers.CharField(source='get_nome_display', read_only=True)
    
    class Meta:
        model = Regiao
        fields = [
            'id',
            'nome',
            'nome_display',
            'codigo_regiao',
            'populacao_estimada',
            'area_km2'
        ]


class CidadeResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagens rápidas de cidades
    """
    
    regiao_nome = serializers.CharField(source='regiao.get_nome_display', read_only=True)
    
    class Meta:
        model = Cidade
        fields = [
            'id',
            'nome',
            'regiao_nome',
            'populacao',
            'tipo'
        ]


class TabancaResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagens rápidas de tabancas
    """
    
    cidade_nome = serializers.CharField(source='cidade.nome', read_only=True)
    
    class Meta:
        model = Tabanca
        fields = [
            'id',
            'nome',
            'cidade_nome',
            'populacao_estimada'
        ]


class EstatisticasGeografiaSerializer(serializers.Serializer):
    """
    Serializer para estatísticas geográficas
    """
    
    total_regioes = serializers.IntegerField()
    total_cidades = serializers.IntegerField()
    total_tabancas = serializers.IntegerField()
    populacao_total = serializers.IntegerField()
    area_total_km2 = serializers.IntegerField()
    densidade_media = serializers.DecimalField(max_digits=8, decimal_places=2)
    cidades_por_tipo = serializers.DictField()
    infraestrutura_saude = serializers.DictField()
    cobertura_servicos = serializers.DictField()


class RelatorioSaudeRegionalSerializer(serializers.Serializer):
    """
    Serializer para relatórios de saúde por região
    """
    
    regiao_id = serializers.IntegerField()
    regiao_nome = serializers.CharField()
    periodo_inicio = serializers.DateField()
    periodo_fim = serializers.DateField()
    total_nascimentos = serializers.IntegerField()
    total_obitos = serializers.IntegerField()
    casos_malaria = serializers.IntegerField()
    casos_dengue = serializers.IntegerField()
    casos_tuberculose = serializers.IntegerField()
    cobertura_vacinal_media = serializers.DecimalField(max_digits=5, decimal_places=2)
    infraestrutura_saude = serializers.DictField()


class HierarquiaGeograficaSerializer(serializers.Serializer):
    """
    Serializer para estrutura hierárquica geográfica
    """
    
    regioes = RegiaoResumoSerializer(many=True)
    cidades_por_regiao = serializers.DictField()
    tabancas_por_cidade = serializers.DictField()


class LocalizacaoComplataSerializer(serializers.ModelSerializer):
    """
    Serializer para dados completos de localização
    """
    
    cidades = CidadeSerializer(many=True, read_only=True)
    indicadores_recentes = serializers.SerializerMethodField()
    resumo_infraestrutura = serializers.SerializerMethodField()
    
    class Meta:
        model = Regiao
        fields = [
            'id',
            'nome',
            'codigo_regiao',
            'populacao_estimada',
            'latitude',
            'longitude',
            'caracteristicas_climaticas',
            'area_km2',
            'densidade_populacional',
            'hospitais_regionais',
            'centros_saude',
            'postos_saude',
            'medicos_por_1000hab',
            'cidades',
            'indicadores_recentes',
            'resumo_infraestrutura',
            'created_at',
            'updated_at'
        ]
    
    def get_indicadores_recentes(self, obj):
        """Retorna os indicadores mais recentes da região"""
        indicadores = IndicadorSaude.objects.filter(
            regiao=obj
        ).order_by('-ano', '-mes')[:3]
        return IndicadorSaudeSerializer(indicadores, many=True).data
    
    def get_resumo_infraestrutura(self, obj):
        """Retorna resumo da infraestrutura da região"""
        cidades = obj.cidades.all()
        return {
            'total_cidades': cidades.count(),
            'cidades_com_centro_saude': cidades.filter(tem_centro_saude=True).count(),
            'cidades_com_farmacia': cidades.filter(tem_farmacia=True).count(),
            'cidades_com_internet': cidades.filter(tem_internet=True).count(),
            'cidades_com_estrada_asfaltada': cidades.filter(tem_estrada_asfaltada=True).count()
        }


class ExportacaoGeografiaSerializer(serializers.Serializer):
    """
    Serializer para exportação de dados geográficos
    """
    
    regiao = RegiaoSerializer()
    cidades = CidadeSerializer(many=True)
    tabancas = TabancaSerializer(many=True)
    indicadores = IndicadorSaudeSerializer(many=True)
    estatisticas = EstatisticasGeografiaSerializer()


class PesquisaGeograficaSerializer(serializers.Serializer):
    """
    Serializer para pesquisa geográfica
    """
    
    termo_pesquisa = serializers.CharField(max_length=100)
    tipo_localizacao = serializers.CharField(max_length=20, required=False)
    regiao_filtro = serializers.IntegerField(required=False)
    
    def validate_tipo_localizacao(self, value):
        """Valida o tipo de localização"""
        tipos_validos = ['regiao', 'cidade', 'tabanca']
        if value and value not in tipos_validos:
            raise serializers.ValidationError(
                f'Tipo deve ser um de: {", ".join(tipos_validos)}'
            )
        return value