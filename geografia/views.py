# geografia/views.py
"""
Views para API REST do módulo de geografia

Este módulo implementa views para diferentes operações:
- CRUD de regiões, cidades e tabancas
- Consulta de indicadores de saúde por localização
- Relatórios geográficos e estatísticas
- Pesquisa e filtros geográficos

Segue padrões de segurança e boas práticas:
- Autenticação obrigatória
- Controle de permissões por tipo de usuário
- Validação de dados de entrada
- Rate limiting implícito
- Logs de auditoria

Autor: Sistema Médico IA Guiné
Data: 2025
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from decimal import Decimal
import logging
from datetime import datetime

from .models import Regiao, Cidade, Tabanca, IndicadorSaude
from .serializers import (
    RegiaoSerializer, RegiaoCriacaoSerializer, RegiaoResumoSerializer,
    CidadeSerializer, CidadeCriacaoSerializer, CidadeResumoSerializer,
    TabancaSerializer, TabancaCriacaoSerializer, TabancaResumoSerializer,
    IndicadorSaudeSerializer, IndicadorSaudeCriacaoSerializer,
    EstatisticasGeografiaSerializer, RelatorioSaudeRegionalSerializer,
    HierarquiaGeograficaSerializer, LocalizacaoComplataSerializer,
    ExportacaoGeografiaSerializer
)
from usuarios.permissions import IsAdminUser, IsModerador

logger = logging.getLogger(__name__)


class BaseGeografiaView(APIView):
    """
    Classe base para views de geografia com funcionalidades comuns
    """
    permission_classes = [IsAuthenticated]
    
    def get_base_queryset(self, model):
        """Retorna queryset base com otimizações"""
        if model == Regiao:
            return Regiao.objects.select_related().prefetch_related('cidades')
        elif model == Cidade:
            return Cidade.objects.select_related('regiao').prefetch_related('tabancas')
        elif model == Tabanca:
            return Tabanca.objects.select_related('cidade__regiao')
        elif model == IndicadorSaude:
            return IndicadorSaude.objects.select_related('regiao', 'cidade', 'tabanca')
        return model.objects.all()
    
    def paginate_queryset(self, queryset, request, page_size=20):
        """Pagina o queryset"""
        try:
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', page_size)), 100)
        except (ValueError, TypeError):
            page = 1
            page_size = 20
        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'results': page_obj.object_list,
            'pagination': {
                'page': page,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }


class RegiaoListCreateView(BaseGeografiaView):
    """
    Lista regiões ou cria nova região
    
    GET: Lista todas as regiões (público)
    POST: Cria nova região (admin/moderador)
    """
    
    def get_permissions(self):
        """Define permissões baseadas no método"""
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    @method_decorator(cache_page(60 * 15))  # Cache por 15 minutos
    def get(self, request):
        """Lista regiões com filtros e paginação"""
        try:
            queryset = self.get_base_queryset(Regiao)
            
            # Aplicar filtros
            nome = request.GET.get('nome')
            if nome:
                queryset = queryset.filter(
                    Q(nome__icontains=nome) | 
                    Q(codigo_regiao__icontains=nome)
                )
            
            # Ordenação
            order_by = request.GET.get('order_by', 'nome')
            if order_by in ['nome', 'populacao_estimada', 'area_km2', 'created_at']:
                if request.GET.get('order', 'asc') == 'desc':
                    order_by = f'-{order_by}'
                queryset = queryset.order_by(order_by)
            
            # Formato de resposta
            resumo = request.GET.get('resumo', 'false').lower() == 'true'
            serializer_class = RegiaoResumoSerializer if resumo else RegiaoSerializer
            
            # Paginação
            paginated_data = self.paginate_queryset(queryset, request)
            serializer = serializer_class(paginated_data['results'], many=True)
            
            logger.info(f"Usuário {request.user.username} consultou regiões")
            
            return Response({
                'success': True,
                'data': serializer.data,
                'pagination': paginated_data['pagination']
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar regiões: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Cria nova região"""
        try:
            serializer = RegiaoCriacaoSerializer(data=request.data)
            
            if serializer.is_valid():
                with transaction.atomic():
                    regiao = serializer.save()
                    
                    logger.info(
                        f"Região '{regiao.nome}' criada por {request.user.nome}"
                    )
                    
                    # Limpar cache relacionado
                    cache.delete_many([
                        'regioes_list',
                        'estatisticas_geografia',
                        'hierarquia_geografica'
                    ])
                    
                    return Response({
                        'success': True,
                        'message': 'Região criada com sucesso',
                        'data': RegiaoSerializer(regiao).data
                    }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao criar região: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegiaoDetailView(BaseGeografiaView):
    """
    Detalhes, atualização e exclusão de região
    
    GET: Visualiza detalhes (público)
    PUT: Atualiza região (admin/moderador)
    DELETE: Remove região (admin)
    """
    
    def get_permissions(self):
        """Define permissões baseadas no método"""
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminUser()]
        elif self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]
    
    def get_object(self, regiao_id):
        """Obtém objeto região ou retorna None"""
        try:
            return Regiao.objects.select_related().prefetch_related(
                'cidades__tabancas'
            ).get(id=regiao_id)
        except Regiao.DoesNotExist:
            return None
    
    def get(self, request, regiao_id):
        """Retorna detalhes da região"""
        try:
            regiao = self.get_object(regiao_id)
            if not regiao:
                return Response({
                    'success': False,
                    'message': 'Região não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Dados completos ou resumo
            completo = request.GET.get('completo', 'false').lower() == 'true'
            serializer_class = LocalizacaoComplataSerializer if completo else RegiaoSerializer
            
            serializer = serializer_class(regiao)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar região {regiao_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, regiao_id):
        """Atualiza região"""
        try:
            regiao = self.get_object(regiao_id)
            if not regiao:
                return Response({
                    'success': False,
                    'message': 'Região não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = RegiaoCriacaoSerializer(regiao, data=request.data, partial=True)
            
            if serializer.is_valid():
                with transaction.atomic():
                    regiao_atualizada = serializer.save()
                    
                    logger.info(
                        f"Região '{regiao.nome}' atualizada por {request.user.username}"
                    )
                    
                    # Limpar cache
                    cache.delete_many([
                        f'regiao_{regiao_id}',
                        'regioes_list',
                        'estatisticas_geografia'
                    ])
                    
                    return Response({
                        'success': True,
                        'message': 'Região atualizada com sucesso',
                        'data': RegiaoSerializer(regiao_atualizada).data
                    })
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar região {regiao_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, regiao_id):
        """Remove região (apenas admin)"""
        try:
            regiao = self.get_object(regiao_id)
            if not regiao:
                return Response({
                    'success': False,
                    'message': 'Região não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verificar se tem cidades associadas
            if regiao.cidades.exists():
                return Response({
                    'success': False,
                    'message': 'Não é possível remover região com cidades associadas'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            nome_regiao = regiao.nome
            
            with transaction.atomic():
                regiao.delete()
                
                logger.warning(
                    f"Região '{nome_regiao}' removida por {request.user.username}"
                )
                
                # Limpar cache
                cache.clear()
                
                return Response({
                    'success': True,
                    'message': 'Região removida com sucesso'
                })
            
        except Exception as e:
            logger.error(f"Erro ao remover região {regiao_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CidadeListCreateView(BaseGeografiaView):
    """
    Lista cidades ou cria nova cidade
    """
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]
    
    def get(self, request):
        """Lista cidades com filtros"""
        try:
            queryset = self.get_base_queryset(Cidade)
            
            # Filtros
            regiao_id = request.GET.get('regiao')
            if regiao_id:
                queryset = queryset.filter(regiao_id=regiao_id)
            
            nome = request.GET.get('nome')
            if nome:
                queryset = queryset.filter(nome__icontains=nome)
            
            tipo = request.GET.get('tipo')
            if tipo:
                queryset = queryset.filter(tipo=tipo)
            
            tem_centro_saude = request.GET.get('tem_centro_saude')
            if tem_centro_saude:
                queryset = queryset.filter(
                    tem_centro_saude=(tem_centro_saude.lower() == 'true')
                )
            
            # Ordenação
            order_by = request.GET.get('order_by', 'nome')
            if order_by in ['nome', 'populacao', 'created_at']:
                if request.GET.get('order', 'asc') == 'desc':
                    order_by = f'-{order_by}'
                queryset = queryset.order_by(order_by)
            
            # Formato
            resumo = request.GET.get('resumo', 'false').lower() == 'true'
            serializer_class = CidadeResumoSerializer if resumo else CidadeSerializer
            
            # Paginação
            paginated_data = self.paginate_queryset(queryset, request)
            serializer = serializer_class(paginated_data['results'], many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'pagination': paginated_data['pagination']
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar cidades: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Cria nova cidade"""
        try:
            serializer = CidadeCriacaoSerializer(data=request.data)
            
            if serializer.is_valid():
                with transaction.atomic():
                    cidade = serializer.save()
                    
                    logger.info(
                        f"Cidade '{cidade.nome}' criada por {request.user.username}"
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Cidade criada com sucesso',
                        'data': CidadeSerializer(cidade).data
                    }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao criar cidade: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CidadeDetailView(BaseGeografiaView):
    """
    Detalhes, atualização e exclusão de cidade
    """
    
    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminUser()]
        elif self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]
    
    def get_object(self, cidade_id):
        try:
            return Cidade.objects.select_related('regiao').prefetch_related(
                'tabancas'
            ).get(id=cidade_id)
        except Cidade.DoesNotExist:
            return None
    
    def get(self, request, cidade_id):
        """Detalhes da cidade"""
        try:
            cidade = self.get_object(cidade_id)
            if not cidade:
                return Response({
                    'success': False,
                    'message': 'Cidade não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = CidadeSerializer(cidade)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar cidade {cidade_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, cidade_id):
        """Atualiza cidade"""
        try:
            cidade = self.get_object(cidade_id)
            if not cidade:
                return Response({
                    'success': False,
                    'message': 'Cidade não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = CidadeCriacaoSerializer(cidade, data=request.data, partial=True)
            
            if serializer.is_valid():
                with transaction.atomic():
                    cidade_atualizada = serializer.save()
                    
                    logger.info(
                        f"Cidade '{cidade.nome}' atualizada por {request.user.username}"
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Cidade atualizada com sucesso',
                        'data': CidadeSerializer(cidade_atualizada).data
                    })
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cidade {cidade_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, cidade_id):
        """Remove cidade"""
        try:
            cidade = self.get_object(cidade_id)
            if not cidade:
                return Response({
                    'success': False,
                    'message': 'Cidade não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if cidade.tabancas.exists():
                return Response({
                    'success': False,
                    'message': 'Não é possível remover cidade com tabancas associadas'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            nome_cidade = cidade.nome
            
            with transaction.atomic():
                cidade.delete()
                
                logger.warning(
                    f"Cidade '{nome_cidade}' removida por {request.user.username}"
                )
                
                return Response({
                    'success': True,
                    'message': 'Cidade removida com sucesso'
                })
            
        except Exception as e:
            logger.error(f"Erro ao remover cidade {cidade_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TabancaListCreateView(BaseGeografiaView):
    """
    Lista tabancas ou cria nova tabanca
    """
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]
    
    def get(self, request):
        """Lista tabancas com filtros"""
        try:
            queryset = self.get_base_queryset(Tabanca)
            
            # Filtros
            cidade_id = request.GET.get('cidade')
            if cidade_id:
                queryset = queryset.filter(cidade_id=cidade_id)
            
            regiao_id = request.GET.get('regiao')
            if regiao_id:
                queryset = queryset.filter(cidade__regiao_id=regiao_id)
            
            nome = request.GET.get('nome')
            if nome:
                queryset = queryset.filter(nome__icontains=nome)
            
            tem_agente = request.GET.get('tem_agente_saude')
            if tem_agente:
                queryset = queryset.filter(
                    tem_agente_saude_comunitario=(tem_agente.lower() == 'true')
                )
            
            # Ordenação
            order_by = request.GET.get('order_by', 'nome')
            if order_by in ['nome', 'populacao_estimada', 'created_at']:
                if request.GET.get('order', 'asc') == 'desc':
                    order_by = f'-{order_by}'
                queryset = queryset.order_by(order_by)
            
            # Formato
            resumo = request.GET.get('resumo', 'false').lower() == 'true'
            serializer_class = TabancaResumoSerializer if resumo else TabancaSerializer
            
            # Paginação
            paginated_data = self.paginate_queryset(queryset, request)
            serializer = serializer_class(paginated_data['results'], many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'pagination': paginated_data['pagination']
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar tabancas: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Cria nova tabanca"""
        try:
            serializer = TabancaCriacaoSerializer(data=request.data)
            
            if serializer.is_valid():
                with transaction.atomic():
                    tabanca = serializer.save()
                    
                    logger.info(
                        f"Tabanca '{tabanca.nome}' criada por {request.user.username}"
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Tabanca criada com sucesso',
                        'data': TabancaSerializer(tabanca).data
                    }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao criar tabanca: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TabancaDetailView(BaseGeografiaView):
    """
    Detalhes, atualização e exclusão de tabanca
    """
    
    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminUser()]
        elif self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]
    
    def get_object(self, tabanca_id):
        try:
            return Tabanca.objects.select_related(
                'cidade__regiao'
            ).get(id=tabanca_id)
        except Tabanca.DoesNotExist:
            return None
    
    def get(self, request, tabanca_id):
        """Detalhes da tabanca"""
        try:
            tabanca = self.get_object(tabanca_id)
            if not tabanca:
                return Response({
                    'success': False,
                    'message': 'Tabanca não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = TabancaSerializer(tabanca)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar tabanca {tabanca_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, tabanca_id):
        """Atualiza tabanca"""
        try:
            tabanca = self.get_object(tabanca_id)
            if not tabanca:
                return Response({
                    'success': False,
                    'message': 'Tabanca não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = TabancaCriacaoSerializer(tabanca, data=request.data, partial=True)
            
            if serializer.is_valid():
                with transaction.atomic():
                    tabanca_atualizada = serializer.save()
                    
                    logger.info(
                        f"Tabanca '{tabanca.nome}' atualizada por {request.user.username}"
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Tabanca atualizada com sucesso',
                        'data': TabancaSerializer(tabanca_atualizada).data
                    })
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar tabanca {tabanca_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, tabanca_id):
        """Remove tabanca"""
        try:
            tabanca = self.get_object(tabanca_id)
            if not tabanca:
                return Response({
                    'success': False,
                    'message': 'Tabanca não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            nome_tabanca = tabanca.nome
            
            with transaction.atomic():
                tabanca.delete()
                
                logger.warning(
                    f"Tabanca '{nome_tabanca}' removida por {request.user.username}"
                )
                
                return Response({
                    'success': True,
                    'message': 'Tabanca removida com sucesso'
                })
            
        except Exception as e:
            logger.error(f"Erro ao remover tabanca {tabanca_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IndicadorSaudeListCreateView(BaseGeografiaView):
    """
    Lista indicadores de saúde ou cria novo indicador
    """
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]
    
    def get(self, request):
        """Lista indicadores com filtros avançados"""
        try:
            queryset = self.get_base_queryset(IndicadorSaude)
            
            # Filtros por localização
            regiao_id = request.GET.get('regiao')
            if regiao_id:
                queryset = queryset.filter(regiao_id=regiao_id)
            
            cidade_id = request.GET.get('cidade')
            if cidade_id:
                queryset = queryset.filter(cidade_id=cidade_id)
            
            tabanca_id = request.GET.get('tabanca')
            if tabanca_id:
                queryset = queryset.filter(tabanca_id=tabanca_id)
            
            # Filtros por período
            ano = request.GET.get('ano')
            if ano:
                queryset = queryset.filter(ano=ano)
            
            mes = request.GET.get('mes')
            if mes:
                queryset = queryset.filter(mes=mes)
            
            # Filtros por tipo de dados
            tem_malaria = request.GET.get('tem_malaria')
            if tem_malaria and tem_malaria.lower() == 'true':
                queryset = queryset.filter(casos_malaria__gt=0)
            
            # Ordenação
            order_by = request.GET.get('order_by', '-ano')
            if order_by.lstrip('-') in ['ano', 'mes', 'created_at']:
                queryset = queryset.order_by(order_by, '-mes')
            
            # Paginação
            paginated_data = self.paginate_queryset(queryset, request)
            serializer = IndicadorSaudeSerializer(paginated_data['results'], many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'pagination': paginated_data['pagination']
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar indicadores: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Cria novo indicador de saúde"""
        try:
            serializer = IndicadorSaudeCriacaoSerializer(data=request.data)
            
            if serializer.is_valid():
                with transaction.atomic():
                    indicador = serializer.save()
                    
                    logger.info(
                        f"Indicador de saúde criado por {request.user.username} - "
                        f"Localização: {indicador.get_localizacao_nome()}, "
                        f"Período: {indicador.mes}/{indicador.ano}"
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Indicador de saúde criado com sucesso',
                        'data': IndicadorSaudeSerializer(indicador).data
                    }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao criar indicador: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IndicadorSaudeDetailView(BaseGeografiaView):
    """
    Detalhes, atualização e exclusão de indicador de saúde
    """
    
    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminUser()]
        elif self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsModerador()]
        return [IsAuthenticated()]
    
    def get_object(self, indicador_id):
        try:
            return IndicadorSaude.objects.select_related(
                'regiao', 'cidade', 'tabanca'
            ).get(id=indicador_id)
        except IndicadorSaude.DoesNotExist:
            return None
    
    def get(self, request, indicador_id):
        """Detalhes do indicador"""
        try:
            indicador = self.get_object(indicador_id)
            if not indicador:
                return Response({
                    'success': False,
                    'message': 'Indicador não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = IndicadorSaudeSerializer(indicador)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar indicador {indicador_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, indicador_id):
        """Atualiza indicador"""
        try:
            indicador = self.get_object(indicador_id)
            if not indicador:
                return Response({
                    'success': False,
                    'message': 'Indicador não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = IndicadorSaudeCriacaoSerializer(
                indicador, data=request.data, partial=True
            )
            
            if serializer.is_valid():
                with transaction.atomic():
                    indicador_atualizado = serializer.save()
                    
                    logger.info(
                        f"Indicador {indicador_id} atualizado por {request.user.username}"
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Indicador atualizado com sucesso',
                        'data': IndicadorSaudeSerializer(indicador_atualizado).data
                    })
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar indicador {indicador_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, indicador_id):
        """Remove indicador"""
        try:
            indicador = self.get_object(indicador_id)
            if not indicador:
                return Response({
                    'success': False,
                    'message': 'Indicador não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            with transaction.atomic():
                indicador.delete()
                
                logger.warning(
                    f"Indicador {indicador_id} removido por {request.user.username}"
                )
                
                return Response({
                    'success': True,
                    'message': 'Indicador removido com sucesso'
                })
            
        except Exception as e:
            logger.error(f"Erro ao remover indicador {indicador_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EstatisticasGeografiaView(BaseGeografiaView):
    """
    Estatísticas gerais de geografia e saúde
    """
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 30))  # Cache por 30 minutos
    def get(self, request):
        """Retorna estatísticas consolidadas"""
        try:
            # Estatísticas básicas
            total_regioes = Regiao.objects.count()
            total_cidades = Cidade.objects.count()
            total_tabancas = Tabanca.objects.count()
            
            # Estatísticas populacionais
            pop_regioes = Regiao.objects.aggregate(
                total=Sum('populacao_estimada')
            )['total'] or 0
            
            pop_cidades = Cidade.objects.aggregate(
                total=Sum('populacao')
            )['total'] or 0
            
            pop_tabancas = Tabanca.objects.aggregate(
                total=Sum('populacao_estimada')
            )['total'] or 0
            
            populacao_total = max(pop_regioes, pop_cidades, pop_tabancas)
            
            # Área total
            area_total = Regiao.objects.aggregate(
                total=Sum('area_km2')
            )['total'] or 0
            
            # Densidade média
            densidade_media = Decimal('0')
            if area_total > 0:
                densidade_media = Decimal(populacao_total) / Decimal(area_total)
            
            # Cidades por tipo
            cidades_por_tipo = dict(
                Cidade.objects.values('tipo').annotate(
                    count=Count('id')
                ).values_list('tipo', 'count')
            )
            
            # Infraestrutura de saúde
            infraestrutura = {
                'hospitais_regionais': Regiao.objects.aggregate(
                    total=Sum('hospitais_regionais')
                )['total'] or 0,
                'centros_saude': Regiao.objects.aggregate(
                    total=Sum('centros_saude')
                )['total'] or 0,
                'postos_saude': Regiao.objects.aggregate(
                    total=Sum('postos_saude')
                )['total'] or 0,
                'cidades_com_centro_saude': Cidade.objects.filter(
                    tem_centro_saude=True
                ).count(),
                'cidades_com_farmacia': Cidade.objects.filter(
                    tem_farmacia=True
                ).count(),
                'tabancas_com_agente': Tabanca.objects.filter(
                    tem_agente_saude_comunitario=True
                ).count()
            }
            
            # Cobertura de serviços
            cobertura_servicos = {
                'cidades_com_internet': Cidade.objects.filter(
                    tem_internet=True
                ).count(),
                'cidades_com_estrada_asfaltada': Cidade.objects.filter(
                    tem_estrada_asfaltada=True
                ).count(),
                'tabancas_com_agua_potavel': Tabanca.objects.filter(
                    acesso_agua_potavel=True
                ).count(),
                'tabancas_com_eletricidade': Tabanca.objects.filter(
                    acesso_eletricidade=True
                ).count(),
                'tabancas_com_saneamento': Tabanca.objects.filter(
                    tem_saneamento_basico=True
                ).count()
            }
            
            dados_estatisticas = {
                'total_regioes': total_regioes,
                'total_cidades': total_cidades,
                'total_tabancas': total_tabancas,
                'populacao_total': populacao_total,
                'area_total_km2': int(area_total),
                'densidade_media': densidade_media,
                'cidades_por_tipo': cidades_por_tipo,
                'infraestrutura_saude': infraestrutura,
                'cobertura_servicos': cobertura_servicos
            }
            
            serializer = EstatisticasGeografiaSerializer(dados_estatisticas)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RelatorioSaudeRegionalView(BaseGeografiaView):
    """
    Relatório de saúde por região e período
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, regiao_id):
        """Gera relatório de saúde regional"""
        try:
            # Validar região
            try:
                regiao = Regiao.objects.get(id=regiao_id)
            except Regiao.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Região não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Parâmetros de período
            ano = request.GET.get('ano', datetime.now().year)
            mes_inicio = request.GET.get('mes_inicio', 1)
            mes_fim = request.GET.get('mes_fim', 12)
            
            try:
                ano = int(ano)
                mes_inicio = int(mes_inicio)
                mes_fim = int(mes_fim)
            except ValueError:
                return Response({
                    'success': False,
                    'message': 'Parâmetros de período inválidos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Consultar indicadores
            indicadores = IndicadorSaude.objects.filter(
                regiao=regiao,
                ano=ano,
                mes__gte=mes_inicio,
                mes__lte=mes_fim
            )
            
            if not indicadores.exists():
                return Response({
                    'success': False,
                    'message': 'Nenhum dado encontrado para o período especificado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Agregar dados
            agregacao = indicadores.aggregate(
                total_nascimentos=Sum('nascimentos'),
                total_obitos=Sum('obitos'),
                casos_malaria=Sum('casos_malaria'),
                casos_dengue=Sum('casos_dengue'),
                casos_tuberculose=Sum('casos_tuberculose'),
                cobertura_vacinal_media=Avg('cobertura_vacinal_infantil')
            )
            
            # Infraestrutura da região
            infraestrutura_saude = {
                'hospitais_regionais': regiao.hospitais_regionais,
                'centros_saude': regiao.centros_saude,
                'postos_saude': regiao.postos_saude,
                'medicos_por_1000hab': regiao.medicos_por_1000hab
            }
            
            # Montar relatório
            relatorio_dados = {
                'regiao_id': regiao.id,
                'regiao_nome': regiao.get_nome_display(),
                'periodo_inicio': f"{ano}-{mes_inicio:02d}-01",
                'periodo_fim': f"{ano}-{mes_fim:02d}-28",
                'total_nascimentos': agregacao['total_nascimentos'] or 0,
                'total_obitos': agregacao['total_obitos'] or 0,
                'casos_malaria': agregacao['casos_malaria'] or 0,
                'casos_dengue': agregacao['casos_dengue'] or 0,
                'casos_tuberculose': agregacao['casos_tuberculose'] or 0,
                'cobertura_vacinal_media': agregacao['cobertura_vacinal_media'] or Decimal('0'),
                'infraestrutura_saude': infraestrutura_saude
            }
            
            serializer = RelatorioSaudeRegionalSerializer(relatorio_dados)
            
            logger.info(
                f"Relatório regional gerado por {request.user.username} - "
                f"Região: {regiao.nome}, Período: {mes_inicio}-{mes_fim}/{ano}"
            )
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório regional: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HierarquiaGeograficaView(BaseGeografiaView):
    """
    Estrutura hierárquica completa da geografia
    """
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 60))  # Cache por 1 hora
    def get(self, request):
        """Retorna hierarquia completa"""
        try:
            # Buscar todas as regiões
            regioes = Regiao.objects.prefetch_related(
                'cidades__tabancas'
            ).all()
            
            regioes_data = RegiaoResumoSerializer(regioes, many=True).data
            
            # Mapear cidades por região
            cidades_por_regiao = {}
            tabancas_por_cidade = {}
            
            for regiao in regioes:
                cidades = regiao.cidades.all()
                cidades_por_regiao[regiao.id] = CidadeResumoSerializer(
                    cidades, many=True
                ).data
                
                for cidade in cidades:
                    tabancas = cidade.tabancas.all()
                    tabancas_por_cidade[cidade.id] = TabancaResumoSerializer(
                        tabancas, many=True
                    ).data
            
            dados_hierarquia = {
                'regioes': regioes_data,
                'cidades_por_regiao': cidades_por_regiao,
                'tabancas_por_cidade': tabancas_por_cidade
            }
            
            serializer = HierarquiaGeograficaSerializer(dados_hierarquia)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar hierarquia: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PesquisaGeograficaView(BaseGeografiaView):
    """
    Pesquisa unificada em todas as entidades geográficas
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Pesquisa por termo em regiões, cidades e tabancas"""
        try:
            termo = request.GET.get('q', '').strip()
            if not termo:
                return Response({
                    'success': False,
                    'message': 'Termo de pesquisa é obrigatório'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(termo) < 2:
                return Response({
                    'success': False,
                    'message': 'Termo deve ter pelo menos 2 caracteres'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Pesquisar em regiões
            regioes = Regiao.objects.filter(
                Q(nome__icontains=termo) | Q(codigo_regiao__icontains=termo)
            )[:10]
            
            # Pesquisar em cidades
            cidades = Cidade.objects.filter(
                Q(nome__icontains=termo) | Q(codigo_postal__icontains=termo)
            ).select_related('regiao')[:10]
            
            # Pesquisar em tabancas
            tabancas = Tabanca.objects.filter(
                nome__icontains=termo
            ).select_related('cidade__regiao')[:10]
            
            # Serializar resultados
            resultados = {
                'regioes': RegiaoResumoSerializer(regioes, many=True).data,
                'cidades': CidadeResumoSerializer(cidades, many=True).data,
                'tabancas': TabancaResumoSerializer(tabancas, many=True).data,
                'total_resultados': len(regioes) + len(cidades) + len(tabancas)
            }
            
            return Response({
                'success': True,
                'data': resultados,
                'termo_pesquisado': termo
            })
            
        except Exception as e:
            logger.error(f"Erro na pesquisa geográfica: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExportacaoGeografiaView(BaseGeografiaView):
    """
    Exportação de dados geográficos
    """
    
    permission_classes = [IsAuthenticated, IsModerador]
    
    def get(self, request, regiao_id):
        """Exporta dados completos de uma região"""
        try:
            # Validar região
            try:
                regiao = Regiao.objects.prefetch_related(
                    'cidades__tabancas'
                ).get(id=regiao_id)
            except Regiao.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Região não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Buscar dados relacionados
            cidades = regiao.cidades.all()
            tabancas = Tabanca.objects.filter(cidade__regiao=regiao)
            indicadores = IndicadorSaude.objects.filter(regiao=regiao)
            
            # Gerar estatísticas
            estatisticas_dados = {
                'total_regioes': 1,
                'total_cidades': cidades.count(),
                'total_tabancas': tabancas.count(),
                'populacao_total': regiao.populacao_estimada or 0,
                'area_total_km2': int(regiao.area_km2 or 0),
                'densidade_media': regiao.densidade_populacional or Decimal('0'),
                'cidades_por_tipo': dict(cidades.values('tipo').annotate(
                    count=Count('id')
                ).values_list('tipo', 'count')),
                'infraestrutura_saude': {
                    'hospitais_regionais': regiao.hospitais_regionais,
                    'centros_saude': regiao.centros_saude,
                    'postos_saude': regiao.postos_saude
                },
                'cobertura_servicos': {
                    'cidades_com_internet': cidades.filter(
                        tem_internet=True
                    ).count(),
                    'cidades_com_estrada_asfaltada': cidades.filter(
                        tem_estrada_asfaltada=True
                    ).count()
                }
            }
            
            # Montar dados de exportação
            dados_exportacao = {
                'regiao': RegiaoSerializer(regiao).data,
                'cidades': CidadeSerializer(cidades, many=True).data,
                'tabancas': TabancaSerializer(tabancas, many=True).data,
                'indicadores': IndicadorSaudeSerializer(indicadores, many=True).data,
                'estatisticas': EstatisticasGeografiaSerializer(estatisticas_dados).data
            }
            
            serializer = ExportacaoGeografiaSerializer(dados_exportacao)
            
            logger.info(
                f"Exportação de dados geográficos por {request.user.username} - "
                f"Região: {regiao.nome}"
            )
            
            return Response({
                'success': True,
                'data': serializer.data,
                'exported_at': datetime.now().isoformat(),
                'exported_by': request.user.username
            })
            
        except Exception as e:
            logger.error(f"Erro na exportação: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IndicadoresPorLocalizacaoView(BaseGeografiaView):
    """
    Indicadores de saúde filtrados por localização
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista indicadores por hierarquia de localização"""
        try:
            # Parâmetros de localização
            regiao_id = request.GET.get('regiao')
            cidade_id = request.GET.get('cidade')
            tabanca_id = request.GET.get('tabanca')
            
            # Validar se pelo menos uma localização foi especificada
            if not any([regiao_id, cidade_id, tabanca_id]):
                return Response({
                    'success': False,
                    'message': 'Deve ser especificada pelo menos uma localização'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            queryset = IndicadorSaude.objects.select_related(
                'regiao', 'cidade', 'tabanca'
            )
            
            # Aplicar filtros de localização
            if tabanca_id:
                queryset = queryset.filter(tabanca_id=tabanca_id)
            elif cidade_id:
                queryset = queryset.filter(cidade_id=cidade_id)
            elif regiao_id:
                queryset = queryset.filter(regiao_id=regiao_id)
            
            # Filtros de período
            ano = request.GET.get('ano')
            if ano:
                queryset = queryset.filter(ano=ano)
            
            mes = request.GET.get('mes')
            if mes:
                queryset = queryset.filter(mes=mes)
            
            # Últimos N registros
            limite = request.GET.get('limite')
            if limite:
                try:
                    limite = min(int(limite), 100)  # Máximo 100 registros
                    queryset = queryset.order_by('-ano', '-mes')[:limite]
                except ValueError:
                    pass
            
            # Paginação
            paginated_data = self.paginate_queryset(queryset, request)
            serializer = IndicadorSaudeSerializer(paginated_data['results'], many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'pagination': paginated_data['pagination']
            })
            
        except Exception as e:
            logger.error(f"Erro ao buscar indicadores por localização: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)