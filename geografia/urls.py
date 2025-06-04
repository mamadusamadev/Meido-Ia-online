# geografia/urls.py
"""
URLs para o módulo de geografia

Define rotas para:
- CRUD de regiões, cidades e tabancas
- Consulta e gestão de indicadores de saúde
- Relatórios e estatísticas geográficas
- Pesquisa e exportação de dados

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    # Regiões
    RegiaoListCreateView,
    RegiaoDetailView,
    
    # Cidades
    CidadeListCreateView,
    CidadeDetailView,
    
    # Tabancas
    TabancaListCreateView,
    TabancaDetailView,
    
    # Indicadores de Saúde
    IndicadorSaudeListCreateView,
    IndicadorSaudeDetailView,
    IndicadoresPorLocalizacaoView,
    
    # Relatórios e Estatísticas
    EstatisticasGeografiaView,
    RelatorioSaudeRegionalView,
    HierarquiaGeograficaView,
    
    # Utilitários
    PesquisaGeograficaView,
    ExportacaoGeografiaView,
)
from .viewsets import CidadeViewSet, TabancaViewSet

router = DefaultRouter()
router.register('crud/cidades', CidadeViewSet, basename='crud-cidades')
router.register('crud/tabancas', TabancaViewSet, basename='crud-tabancas')

app_name = 'geografia'

urlpatterns = [
    # === REGIÕES ===
    # Lista/cria regiões
    path('regioes/', RegiaoListCreateView.as_view(), name='regiao-list-create'),
    
    # Detalhes/atualiza/remove região específica
    path('regioes/<int:regiao_id>/', RegiaoDetailView.as_view(), name='regiao-detail'),
    
    # === CIDADES ===
    # Lista/cria cidades
    path('cidades/', CidadeListCreateView.as_view(), name='cidade-list-create'),
    
    # Detalhes/atualiza/remove cidade específica
    path('cidades/<int:cidade_id>/', CidadeDetailView.as_view(), name='cidade-detail'),
    
    # === TABANCAS ===
    # Lista/cria tabancas
    path('tabancas/', TabancaListCreateView.as_view(), name='tabanca-list-create'),
    
    # Detalhes/atualiza/remove tabanca específica
    path('tabancas/<int:tabanca_id>/', TabancaDetailView.as_view(), name='tabanca-detail'),
    
    # === INDICADORES DE SAÚDE ===
    # Lista/cria indicadores
    path('indicadores/', IndicadorSaudeListCreateView.as_view(), name='indicador-list-create'),
    
    # Detalhes/atualiza/remove indicador específico
    path('indicadores/<int:indicador_id>/', IndicadorSaudeDetailView.as_view(), name='indicador-detail'),
    
    # Indicadores por localização
    path('indicadores/localizacao/', IndicadoresPorLocalizacaoView.as_view(), name='indicadores-localizacao'),
    
    # === RELATÓRIOS E ESTATÍSTICAS ===
    # Estatísticas gerais de geografia
    path('estatisticas/', EstatisticasGeografiaView.as_view(), name='estatisticas'),
    
    # Relatório de saúde por região
    path('relatorios/regiao/<int:regiao_id>/', RelatorioSaudeRegionalView.as_view(), name='relatorio-regional'),
    
    # Hierarquia geográfica completa
    path('hierarquia/', HierarquiaGeograficaView.as_view(), name='hierarquia'),
    
    # === UTILITÁRIOS ===
    # Pesquisa unificada
    path('pesquisar/', PesquisaGeograficaView.as_view(), name='pesquisa'),
    
    # Exportação de dados por região
    path('exportar/<int:regiao_id>/', ExportacaoGeografiaView.as_view(), name='exportacao'),
]

urlpatterns += router.urls
